"""Tests for the control experiments, on synthetic light curves (no network)."""

import numpy as np
import pytest

from discover_anything.controls import (
    bls_search,
    holdout_prediction,
    inject_box_transit,
    injection_recovery,
    invert_flux,
    period_grid,
)

NOISE = 300e-6  # 300 ppm per 30-min point


def make_lightcurve(seed=0, n_seasons=3):
    """Three 27-day "sectors" 60 days apart at 30-minute cadence, white noise."""
    rng = np.random.default_rng(seed)
    cadence = 30 / 60 / 24
    chunks = [np.arange(0, 27, cadence) + 60 * i for i in range(n_seasons)]
    time = np.concatenate(chunks)
    flux = 1 + rng.normal(0, NOISE, time.size)
    return time, flux


def test_invert_flux_flips_dips_and_does_not_mutate():
    flux = np.array([1.0, 1.0, 0.99, 1.0, 1.0])
    original = flux.copy()
    inverted = invert_flux(flux)
    np.testing.assert_array_equal(flux, original)
    assert np.median(inverted) == pytest.approx(np.median(flux))
    assert inverted[2] == pytest.approx(1.01)


def test_inject_box_transit_only_touches_in_transit_points():
    time = np.linspace(0, 10, 1001)
    flux = np.ones_like(time)
    out = inject_box_transit(time, flux, period=2.0, t0=1.0, depth=1e-3, duration=0.1)
    in_transit = np.abs(((time - 1.0 + 1.0) % 2.0) - 1.0) < 0.05
    assert np.all(flux == 1.0)  # input untouched
    np.testing.assert_allclose(out[in_transit], 1 - 1e-3)
    np.testing.assert_allclose(out[~in_transit], 1.0)


def test_bls_recovers_injected_period():
    time, flux = make_lightcurve(seed=1)
    flux = inject_box_transit(time, flux, period=3.18, t0=0.7, depth=800e-6, duration=0.09)
    result = bls_search(time, flux, min_period=0.8, max_period=10)
    assert result["period"] == pytest.approx(3.18, rel=2e-3)
    assert result["snr"] > 10


def test_null_run_is_weaker_than_real_signal():
    time, flux = make_lightcurve(seed=2)
    with_planet = inject_box_transit(time, flux, period=4.93, t0=1.1, depth=800e-6, duration=0.07)
    real = bls_search(time, with_planet, min_period=0.8, max_period=10)
    null = bls_search(time, invert_flux(with_planet), min_period=0.8, max_period=10)
    assert real["snr"] > 2 * null["snr"]


def test_injection_recovery_depends_on_depth():
    time, flux = make_lightcurve(seed=3)
    kwargs = {"n_trials": 6, "period_range": (1.0, 6.0), "duration": 0.08, "seed": 7,
              "min_period": 0.8, "max_period": 8}
    strong = injection_recovery(time, flux, depth=1500e-6, **kwargs)
    weak = injection_recovery(time, flux, depth=40e-6, **kwargs)
    assert strong["recovered_fraction"] >= 0.8
    assert weak["recovered_fraction"] <= 0.34
    assert len(strong["trials"]) == 6


def test_holdout_detects_real_transit_in_hidden_season():
    time, flux = make_lightcurve(seed=4)
    flux = inject_box_transit(time, flux, period=3.18, t0=0.7, depth=800e-6, duration=0.09)
    hidden = time > 100  # third season
    result = holdout_prediction(time, flux, hidden, period_guess=3.18, duration=0.09)
    assert result["n_predicted"] > 0
    assert result["detected"]
    assert result["depth"] == pytest.approx(800e-6, rel=0.35)


def test_holdout_rejects_signal_absent_from_hidden_season():
    time, flux = make_lightcurve(seed=5)
    hidden = time > 100
    # transit only in the visible seasons: a systematic that does not repeat
    visible_only = inject_box_transit(time, flux, period=3.18, t0=0.7, depth=800e-6, duration=0.09)
    flux = np.where(hidden, flux, visible_only)
    result = holdout_prediction(time, flux, hidden, period_guess=3.18, duration=0.09)
    assert not result["detected"]


def test_holdout_requires_both_visible_and_hidden_data():
    time, flux = make_lightcurve(seed=6)
    with pytest.raises(ValueError):
        holdout_prediction(time, flux, np.zeros_like(time, dtype=bool), 3.0, 0.1)


def test_period_grid_refuses_absurd_sizes():
    with pytest.raises(ValueError):
        period_grid(baseline=3000, min_period=0.2, max_period=500, min_duration=0.01)
