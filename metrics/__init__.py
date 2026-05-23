"""Error-metrics helpers built on top of plot_core scenario adapters."""

from .alignment import AlignedSeries, align_time_series, build_paired_dataarrays
from .scores import (
    compute_bias,
    compute_corr,
    compute_mae,
    compute_rmse,
    compute_precipitation_totals,
    paired_finite_sample_count,
)

__all__ = [
    "AlignedSeries",
    "align_time_series",
    "build_paired_dataarrays",
    "compute_bias",
    "compute_corr",
    "compute_mae",
    "compute_rmse",
    "compute_precipitation_totals",
    "paired_finite_sample_count",
]
