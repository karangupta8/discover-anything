"""Calibration, reprint grouping, vetting tests and shuffle nulls on synthetic data."""

import numpy as np
import pytest

from discover_anything import calibration, textmatch, vetting
from discover_anything.controls import block_shuffle, inject_box_transit, shuffle_flux

# --- calibration ---------------------------------------------------------------

def test_known_answer_recall_with_values_and_aliases():
    known = [{"id": "A", "period": 3.0}, {"id": "B", "period": 5.0}, {"id": "C", "period": 7.0}]
    found = [{"id": "A", "period": 6.0},        # 2x alias: recovered
             {"id": "B", "period": 5.6}]        # wrong value
    result = calibration.score_known_answers(known, found, "id", "period", rel_tol=0.01)
    assert result["recovered"] == ["A"]
    assert result["missed"] == ["C"]
    assert result["wrong_value"][0]["key"] == "B"
    assert result["recall"] == pytest.approx(1 / 3)


def test_known_answers_cannot_be_empty():
    with pytest.raises(ValueError):
        calibration.score_known_answers([], [], "id")


def test_judge_agreement_kappa_and_confusions():
    expected = {"1": "yes", "2": "yes", "3": "no", "4": "no", "5": "yes"}
    predicted = {"1": "yes", "2": "no", "3": "no", "4": "no"}
    result = calibration.judge_agreement(expected, predicted)
    assert result["n"] == 4 and result["accuracy"] == 0.75
    assert result["confusions"] == {"yes -> no": 1}
    assert result["unpredicted"] == ["5"]
    assert result["per_label"]["no"]["precision"] == pytest.approx(2 / 3)
    perfect = calibration.judge_agreement({"1": "a", "2": "b"}, {"1": "a", "2": "b"})
    assert perfect["kappa"] == 1.0


# --- reprints ------------------------------------------------------------------

def test_reprints_grouped_but_distinct_stories_kept_apart():
    base = ("A stone precipitated from a thunder cloud near the village three days ago, "
            "very heavy for its size and coated with a thin black crust")
    texts = [base, base.replace("thunder cloud", "thunder-cloud") + " (Bombay Gazette)",
             "The governor reported a great fire behind a cloud mixed with lightning and a great roar"]
    pairs = textmatch.near_duplicates(texts, threshold=0.5)
    assert [(i, j) for i, j, _ in pairs] == [(0, 1)]
    assert textmatch.group_duplicates(3, pairs) == ((0, 1), (2,))
    with pytest.raises(ValueError):
        textmatch.near_duplicates(texts, threshold=0)


# --- vetting -------------------------------------------------------------------

def lightcurve(seed=1, noise=200e-6):
    rng = np.random.default_rng(seed)
    t = np.concatenate([np.arange(0, 27, 0.02), np.arange(100, 127, 0.02)])
    return t, 1 + rng.normal(0, noise, t.size)


def test_planet_like_signal_passes_odd_even_and_secondary():
    t, f = lightcurve()
    f = inject_box_transit(t, f, 3.0, 1.0, 1e-3, 0.1)
    assert not vetting.odd_even_depths(t, f, 3.0, 1.0, 0.1)["flag"]
    assert not vetting.secondary_eclipse(t, f, 3.0, 1.0, 0.1)["flag"]
    seasons = vetting.season_depths(t, f, 3.0, 1.0, 0.1)
    assert len(seasons["seasons"]) == 2 and not seasons["flag"]
    assert not vetting.event_dominance(t, f, 3.0, 1.0, 0.1)["flag"]


def test_eclipsing_binary_fails_odd_even_and_secondary():
    t, f = lightcurve()
    # binary at P=6 seen at half period: alternating deep and shallow eclipses
    f = inject_box_transit(t, f, 6.0, 1.0, 2e-3, 0.1)
    f = inject_box_transit(t, f, 6.0, 4.0, 0.5e-3, 0.1)
    assert vetting.odd_even_depths(t, f, 3.0, 1.0, 0.1)["flag"]
    t2, f2 = lightcurve(2)
    f2 = inject_box_transit(t2, f2, 3.0, 1.0, 2e-3, 0.1)
    f2 = inject_box_transit(t2, f2, 3.0, 2.5, 1e-3, 0.1)  # secondary at phase 0.5
    assert vetting.secondary_eclipse(t2, f2, 3.0, 1.0, 0.1)["flag"]


def test_inconsistent_season_depths_flagged():
    t, f = lightcurve()
    first = t < 50
    f = np.where(first, inject_box_transit(t, f, 3.0, 1.0, 2e-3, 0.1), f)
    assert vetting.season_depths(t, f, 3.0, 1.0, 0.1)["flag"]


def test_single_event_dominance_flagged():
    t, f = lightcurve()
    one = (t > 9.9) & (t < 10.1)
    f = np.where(one, f - 3e-3, f)
    assert vetting.event_dominance(t, f, 3.0, 10.0, 0.1)["flag"]


def test_systematic_periods():
    assert "1x 13.7 d" in vetting.near_systematic_period(13.75)
    assert "13.7 d / 2" in vetting.near_systematic_period(6.85)
    assert vetting.near_systematic_period(3.18) == []


def test_lomb_scargle_recovers_sinusoid():
    t, f = lightcurve()
    f = f + 2e-3 * np.sin(2 * np.pi * t / 1.7)
    peak = vetting.lomb_scargle_peak(t, f, 0.2, 10)
    assert peak["period"] == pytest.approx(1.7, rel=0.01)
    assert peak["fap"] < 1e-6


# --- shuffle nulls --------------------------------------------------------------

def test_shuffle_destroys_periodicity_and_keeps_values():
    t, f = lightcurve()
    f = f + 2e-3 * np.sin(2 * np.pi * t / 1.7)
    shuffled = shuffle_flux(f, seed=3)
    assert np.allclose(np.sort(shuffled), np.sort(f))
    assert vetting.lomb_scargle_peak(t, shuffled, 0.2, 10)["fap"] > 1e-3
    original = f.copy()
    block_shuffle(f, 50, seed=1)
    assert np.array_equal(f, original)  # inputs never modified
    assert np.allclose(np.sort(block_shuffle(f, 50)), np.sort(f))
    with pytest.raises(ValueError):
        block_shuffle(f, 0)
