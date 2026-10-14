"""Vetting tests for periodic signals in light curves.

Each test returns plain numbers plus a ``flag`` explaining what failed, so a
claim card can quote them. Times in days; flux normalised to ~1.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import numpy as np
from astropy.timeseries import LombScargle
from numpy.typing import ArrayLike

# TESS: 13.7 d orbit; 1 d and its harmonics from ground-based and processing artefacts
KNOWN_SYSTEMATIC_PERIODS = (13.7, 1.0)
ODD_EVEN_SIGMA_LIMIT = 3.0
SECONDARY_SIGMA_LIMIT = 3.0
SEASON_CHI2_LIMIT = 5.0
DOMINANCE_LIMIT = 0.5


def _arrays(time: ArrayLike, flux: ArrayLike) -> tuple[np.ndarray, np.ndarray]:
    t, f = np.asarray(time, dtype=float), np.asarray(flux, dtype=float)
    if t.shape != f.shape or t.size < 10:
        raise ValueError("time and flux must be equal-length arrays of >= 10 points")
    return t, f


def _phase(time: np.ndarray, period: float, t0: float) -> np.ndarray:
    """Phase in [-0.5, 0.5) with transit at 0."""
    return ((time - t0) / period + 0.5) % 1.0 - 0.5


def _depth(flux: np.ndarray, inside: np.ndarray, outside: np.ndarray) -> tuple[float, float]:
    if inside.sum() < 3 or outside.sum() < 10:
        return float("nan"), float("nan")
    base = np.median(flux[outside])
    scatter = np.std(flux[outside])
    return float(base - flux[inside].mean()), float(scatter / np.sqrt(inside.sum()))


def odd_even_depths(time: ArrayLike, flux: ArrayLike, period: float, t0: float,
                    duration: float) -> dict[str, Any]:
    """Compare depths of odd and even events; a difference suggests an eclipsing binary at 2x period."""
    t, f = _arrays(time, flux)
    epoch = np.round((t - t0) / period).astype(int)
    near = np.abs(_phase(t, period, t0) * period) < duration / 2
    out = np.abs(_phase(t, period, t0) * period) > duration
    odd_d, odd_e = _depth(f, near & (epoch % 2 == 1), out)
    even_d, even_e = _depth(f, near & (epoch % 2 == 0), out)
    sigma = abs(odd_d - even_d) / np.hypot(odd_e, even_e) if np.isfinite(odd_d + even_d) else float("nan")
    return {"depth_odd": odd_d, "err_odd": odd_e, "depth_even": even_d, "err_even": even_e,
            "sigma_diff": float(sigma),
            "flag": bool(np.isfinite(sigma) and sigma > ODD_EVEN_SIGMA_LIMIT)}


def secondary_eclipse(time: ArrayLike, flux: ArrayLike, period: float, t0: float,
                      duration: float) -> dict[str, Any]:
    """Depth at phase 0.5; a significant dip suggests an eclipsing binary."""
    t, f = _arrays(time, flux)
    shifted = np.abs(_phase(t, period, t0 + period / 2) * period)
    primary = np.abs(_phase(t, period, t0) * period)
    depth, err = _depth(f, shifted < duration / 2, (shifted > duration) & (primary > duration))
    sigma = depth / err if np.isfinite(depth) and err > 0 else float("nan")
    return {"depth": depth, "err": err, "sigma": float(sigma),
            "flag": bool(np.isfinite(sigma) and sigma > SECONDARY_SIGMA_LIMIT)}


def split_seasons(time: ArrayLike, gap_days: float = 30.0) -> np.ndarray:
    """Season index per point, starting a new season after each gap > gap_days."""
    t = np.asarray(time, dtype=float)
    order = np.argsort(t)
    breaks = np.concatenate([[0], np.cumsum(np.diff(t[order]) > gap_days)])
    seasons = np.empty_like(breaks)
    seasons[order] = breaks
    return seasons


def season_depths(time: ArrayLike, flux: ArrayLike, period: float, t0: float, duration: float,
                  gap_days: float = 30.0) -> dict[str, Any]:
    """Depth per season and chi^2/dof of their consistency."""
    t, f = _arrays(time, flux)
    seasons = split_seasons(t, gap_days)
    dist = np.abs(_phase(t, period, t0) * period)
    rows = []
    for s in np.unique(seasons):
        sel = seasons == s
        d, e = _depth(f[sel], dist[sel] < duration / 2, dist[sel] > duration)
        if np.isfinite(d):
            rows.append({"season": int(s), "depth": d, "err": e})
    if len(rows) < 2:
        return {"seasons": rows, "chi2_dof": float("nan"), "flag": False}
    depths = np.array([r["depth"] for r in rows])
    errs = np.array([r["err"] for r in rows])
    weights = 1 / errs**2
    mean = np.sum(depths * weights) / weights.sum()
    chi2_dof = float(np.sum(((depths - mean) / errs) ** 2) / (len(rows) - 1))
    return {"seasons": rows, "weighted_mean": float(mean), "chi2_dof": chi2_dof,
            "flag": chi2_dof > SEASON_CHI2_LIMIT}


def event_dominance(time: ArrayLike, flux: ArrayLike, period: float, t0: float,
                    duration: float) -> dict[str, Any]:
    """Share of total signal (sum of squared per-event SNR) from the strongest single event."""
    t, f = _arrays(time, flux)
    dist = np.abs(_phase(t, period, t0) * period)
    out = dist > duration
    base, scatter = np.median(f[out]), np.std(f[out])
    epoch = np.round((t - t0) / period).astype(int)
    snr2 = []
    for e in np.unique(epoch[dist < duration / 2]):
        sel = (epoch == e) & (dist < duration / 2)
        if sel.sum() >= 2:
            snr = (base - f[sel].mean()) / (scatter / np.sqrt(sel.sum()))
            snr2.append(max(float(snr), 0.0) ** 2)
    total = sum(snr2)
    share = max(snr2) / total if total > 0 else float("nan")
    return {"n_events": len(snr2), "max_event_share": share,
            "flag": bool(len(snr2) < 3 or (np.isfinite(share) and share > DOMINANCE_LIMIT))}


def near_systematic_period(period: float, systematics: Sequence[float] = KNOWN_SYSTEMATIC_PERIODS,
                           rel_tol: float = 0.01, harmonics: int = 4) -> list[str]:
    """Known systematic periods (and harmonics/subharmonics) the period is close to."""
    hits = []
    for base in systematics:
        for n in range(1, harmonics + 1):
            for candidate, label in ((base * n, f"{n}x {base} d"), (base / n, f"{base} d / {n}")):
                if abs(period / candidate - 1) <= rel_tol:
                    hits.append(label)
    return sorted(set(hits))


def lomb_scargle_peak(time: ArrayLike, flux: ArrayLike, min_period: float, max_period: float,
                      samples_per_peak: int = 10) -> dict[str, float]:
    """Strongest Lomb-Scargle period and its false-alarm probability (white-noise assumption)."""
    t, f = _arrays(time, flux)
    if not 0 < min_period < max_period:
        raise ValueError("need 0 < min_period < max_period")
    ls = LombScargle(t, f)
    freq, power = ls.autopower(minimum_frequency=1 / max_period, maximum_frequency=1 / min_period,
                               samples_per_peak=samples_per_peak)
    best = int(np.argmax(power))
    return {"period": float(1 / freq[best]), "power": float(power[best]),
            "fap": float(ls.false_alarm_probability(power[best]))}
