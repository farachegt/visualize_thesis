from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import xarray as xr
import xskillscore as xs


@dataclass(frozen=True)
class PrecipitationTotals:
    """Totals over paired finite precipitation timestamps."""

    total_candidate: float
    total_reference: float
    total_bias: float
    relative_total_bias_percent: float


def paired_finite_sample_count(
    candidate: xr.DataArray,
    reference: xr.DataArray,
) -> int:
    """Count samples where both candidate and reference are finite."""
    paired_mask = (
        np.isfinite(np.asarray(candidate.values, dtype=float))
        & np.isfinite(np.asarray(reference.values, dtype=float))
    )
    return int(np.count_nonzero(paired_mask))


def compute_bias(
    candidate: xr.DataArray,
    reference: xr.DataArray,
) -> float:
    """Return mean error as candidate minus reference."""
    return _to_float(
        xs.me(candidate, reference, dim="time", skipna=True)
    )


def compute_mae(
    candidate: xr.DataArray,
    reference: xr.DataArray,
) -> float:
    """Return mean absolute error."""
    return _to_float(
        xs.mae(candidate, reference, dim="time", skipna=True)
    )


def compute_rmse(
    candidate: xr.DataArray,
    reference: xr.DataArray,
) -> float:
    """Return root mean squared error."""
    return _to_float(
        xs.rmse(candidate, reference, dim="time", skipna=True)
    )


def compute_corr(
    candidate: xr.DataArray,
    reference: xr.DataArray,
) -> float:
    """Return Pearson correlation with a minimum sample guard."""
    if paired_finite_sample_count(candidate, reference) < 2:
        return float("nan")

    return _to_float(
        xs.pearson_r(candidate, reference, dim="time", skipna=True)
    )


def compute_precipitation_totals(
    candidate: xr.DataArray,
    reference: xr.DataArray,
) -> PrecipitationTotals:
    """Return precipitation totals and biases over paired finite samples."""
    candidate_values = np.asarray(candidate.values, dtype=float)
    reference_values = np.asarray(reference.values, dtype=float)
    paired_mask = np.isfinite(candidate_values) & np.isfinite(reference_values)
    if not np.any(paired_mask):
        nan_value = float("nan")
        return PrecipitationTotals(
            total_candidate=nan_value,
            total_reference=nan_value,
            total_bias=nan_value,
            relative_total_bias_percent=nan_value,
        )

    total_candidate = float(np.sum(candidate_values[paired_mask]))
    total_reference = float(np.sum(reference_values[paired_mask]))
    total_bias = total_candidate - total_reference

    if total_reference == 0.0:
        relative_total_bias_percent = float("nan")
    else:
        relative_total_bias_percent = (
            total_bias / total_reference
        ) * 100.0

    return PrecipitationTotals(
        total_candidate=total_candidate,
        total_reference=total_reference,
        total_bias=total_bias,
        relative_total_bias_percent=relative_total_bias_percent,
    )


def _to_float(value: xr.DataArray) -> float:
    """Return a scalar DataArray as a Python float."""
    if value.size == 0:
        return float("nan")
    return float(value.values)
