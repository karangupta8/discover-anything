"""Control experiments for periodic-dip searches.

The three controls every credible October 2026 TESS hunt used:

- invert_flux: a null test. Flip the light curve so real dips become bumps;
  anything the search still finds is noise or systematics.
- inject_box_transit / injection_recovery: plant fake transits and measure how
  many the search recovers at a given depth.
- holdout_prediction: hide part of the data, fit the ephemeris on the rest,
  predict the hidden dips, then measure them.

All functions return new arrays/dicts and never modify their inputs.
Times are in days; flux is normalised to ~1.
"""

from collections.abc import Sequence
from typing import Any

import numpy as np
from astropy.timeseries import BoxLeastSquares
from numpy.typing import ArrayLike, NDArray

DEFAULT_DURATIONS = (0.04, 0.06, 0.08, 0.1, 0.13, 0.17)
DETECTION_SIGMA = 4.0
PERIOD_MATCH_TOLERANCE = 0.01  # fractional
MAX_GRID_SIZE = 2_000_000  # guard against accidentally huge period grids


def invert_flux(flux: ArrayLike) -> NDArray[np.float64]:
    """Mirror flux about its median: dips become bumps, noise statistics stay."""
    flux = np.asarray(flux, dtype=float)
    return 2 * np.median(flux) - flux


def _phase_distance(time: ArrayLike, period: float, t0: float) -> NDArray[np.float64]:
    """Absolute time (days) from each point to the nearest transit centre."""
    phase = (np.asarray(time) - t0 + 0.5 * period) % period - 0.5 * period
    return np.abs(phase)


def inject_box_transit(time: ArrayLike, flux: ArrayLike, period: float, t0: float,
                       depth: float, duration: float) -> NDArray[np.float64]:
    """Return a copy of flux with box-shaped transits subtracted."""
    if period <= 0 or duration <= 0:
        raise ValueError("period and duration must be positive")
    flux = np.asarray(flux, dtype=float)
    in_transit = _phase_distance(time, period, t0) < duration / 2
    return np.where(in_transit, flux - depth, flux)


def period_grid(baseline: float, min_period: float, max_period: float,
                min_duration: float, oversample: float = 3) -> NDArray[np.float64]:
    """Periods uniform in frequency.

    Step chosen so a transit drifts by at most min_duration / oversample over the
    full baseline at the longest period, which is safe for all shorter periods.
    """
    if not 0 < min_period < max_period:
        raise ValueError("need 0 < min_period < max_period")
    df = min_duration / (oversample * baseline * max_period)
    n = int((1 / min_period - 1 / max_period) / df) + 1
    if n > MAX_GRID_SIZE:
        raise ValueError(f"period grid of {n:,} points; narrow the range or oversample")
    freqs = np.linspace(1 / max_period, 1 / min_period, n)
    return np.sort(1 / freqs)


def bls_search(time: ArrayLike, flux: ArrayLike, min_period: float, max_period: float,
               durations: Sequence[float] = DEFAULT_DURATIONS,
               oversample: float = 3) -> dict[str, float]:
    """Box-least-squares search; returns the strongest peak.

    snr is BLS depth / depth uncertainty (astropy's depth_snr).
    """
    time = np.asarray(time, dtype=float)
    flux = np.asarray(flux, dtype=float)
    if time.size != flux.size or time.size < 10:
        raise ValueError("time and flux must be equal-length arrays of >= 10 points")
    noise = np.std(flux) or 1.0
    model = BoxLeastSquares(time, flux, dy=np.full_like(flux, noise))
    periods = period_grid(time.max() - time.min(), min_period, max_period,
                          min(durations), oversample)
    result = model.power(periods, list(durations), objective="snr")
    best = int(np.argmax(result.power))
    return {
        "period": float(result.period[best]),
        "t0": float(result.transit_time[best]),
        "depth": float(result.depth[best]),
        "duration": float(result.duration[best]),
        "snr": float(result.depth_snr[best]),
    }


def _period_matches(found: float, injected: float,
                    tolerance: float = PERIOD_MATCH_TOLERANCE) -> bool:
    """True if found period equals injected, or a simple 1/2 or 2x alias."""
    return any(abs(found / (injected * k) - 1) < tolerance for k in (1, 0.5, 2))


def injection_recovery(time: ArrayLike, flux: ArrayLike, depth: float, n_trials: int,
                       period_range: tuple[float, float], duration: float,
                       seed: int = 0, min_period: float | None = None,
                       max_period: float | None = None) -> dict[str, Any]:
    """Inject n_trials random transits at the given depth and count recoveries.

    A trial counts as recovered if the strongest BLS peak matches the injected
    period (or a factor-2 alias). Returns the fraction and per-trial rows.
    """
    rng = np.random.default_rng(seed)
    lo, hi = period_range
    min_period = min_period or lo * 0.8
    max_period = max_period or hi * 1.2
    time = np.asarray(time, dtype=float)
    trials = []
    for _ in range(n_trials):
        period = float(rng.uniform(lo, hi))
        t0 = float(time.min() + rng.uniform(0, period))
        injected = inject_box_transit(time, flux, period, t0, depth, duration)
        found = bls_search(time, injected, min_period, max_period)
        trials.append({
            "injected_period": period,
            "found_period": found["period"],
            "snr": found["snr"],
            "recovered": _period_matches(found["period"], period),
        })
    recovered = sum(t["recovered"] for t in trials)
    return {"recovered_fraction": recovered / n_trials, "trials": trials}


def holdout_prediction(time: ArrayLike, flux: ArrayLike, hidden_mask: ArrayLike,
                       period_guess: float, duration: float,
                       search_width: float = 0.02) -> dict[str, Any]:
    """Fit the ephemeris on visible data, predict and measure the hidden dips.

    The hidden data is never used in the fit. Detection requires the in-transit
    mean of the hidden data to sit DETECTION_SIGMA below its out-of-transit level.
    """
    time = np.asarray(time, dtype=float)
    flux = np.asarray(flux, dtype=float)
    hidden_mask = np.asarray(hidden_mask, dtype=bool)
    if hidden_mask.all() or not hidden_mask.any():
        raise ValueError("hidden_mask must hide some, but not all, of the data")

    fit = bls_search(time[~hidden_mask], flux[~hidden_mask],
                     min_period=period_guess * (1 - search_width),
                     max_period=period_guess * (1 + search_width),
                     durations=(duration,), oversample=10)
    ephemeris = {"period": fit["period"], "t0": fit["t0"]}

    hidden_t, hidden_f = time[hidden_mask], flux[hidden_mask]
    dist = _phase_distance(hidden_t, fit["period"], fit["t0"])
    in_transit = dist < duration / 2
    out_transit = dist > duration
    n_predicted = int(np.unique(
        np.round((hidden_t[in_transit] - fit["t0"]) / fit["period"])).size)

    if in_transit.sum() < 3 or out_transit.sum() < 10:
        return {**ephemeris, "n_predicted": n_predicted, "depth": float("nan"),
                "depth_sigma": float("nan"), "detected": False}

    baseline = np.median(hidden_f[out_transit])
    scatter = np.std(hidden_f[out_transit])
    depth = baseline - np.mean(hidden_f[in_transit])
    depth_sigma = depth / (scatter / np.sqrt(in_transit.sum()))
    return {
        **ephemeris,
        "n_predicted": n_predicted,
        "depth": float(depth),
        "depth_sigma": float(depth_sigma),
        "detected": bool(depth_sigma > DETECTION_SIGMA),
    }


def shuffle_flux(flux: ArrayLike, seed: int = 0) -> NDArray[np.float64]:
    """Null test for periodicity searches: permute flux values in time.

    Destroys any periodic signal while keeping the flux distribution. White
    noise only: it also destroys correlated (red) noise, so prefer
    block_shuffle when the light curve has trends.
    """
    rng = np.random.default_rng(seed)
    return rng.permutation(np.asarray(flux, dtype=float))


def block_shuffle(flux: ArrayLike, block: int, seed: int = 0) -> NDArray[np.float64]:
    """Permute contiguous blocks of flux, keeping noise correlated within each block."""
    flux = np.asarray(flux, dtype=float)
    if block < 1:
        raise ValueError("block must be >= 1")
    blocks = [flux[i:i + block] for i in range(0, flux.size, block)]
    order = np.random.default_rng(seed).permutation(len(blocks))
    return np.concatenate([blocks[i] for i in order])
