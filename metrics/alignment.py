from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import xarray as xr


@dataclass(frozen=True)
class AlignedSeries:
    """Aligned candidate/reference values on shared timestamps."""

    times: np.ndarray
    candidate: np.ndarray
    reference: np.ndarray

    @property
    def paired_finite_mask(self) -> np.ndarray:
        """Return mask where both candidate and reference are finite."""
        return np.isfinite(self.candidate) & np.isfinite(self.reference)


def align_time_series(
    *,
    candidate_times: np.ndarray,
    candidate_values: np.ndarray,
    reference_times: np.ndarray,
    reference_values: np.ndarray,
) -> AlignedSeries:
    """Align two time series by common timestamps."""
    candidate_time_array = np.asarray(candidate_times, dtype="datetime64[ns]")
    reference_time_array = np.asarray(reference_times, dtype="datetime64[ns]")
    candidate_value_array = np.asarray(candidate_values, dtype=float)
    reference_value_array = np.asarray(reference_values, dtype=float)

    if candidate_time_array.size != candidate_value_array.size:
        raise ValueError(
            "Candidate times and values must have the same size for "
            "alignment."
        )
    if reference_time_array.size != reference_value_array.size:
        raise ValueError(
            "Reference times and values must have the same size for "
            "alignment."
        )

    if candidate_time_array.size == 0 or reference_time_array.size == 0:
        return AlignedSeries(
            times=np.asarray([], dtype="datetime64[ns]"),
            candidate=np.asarray([], dtype=float),
            reference=np.asarray([], dtype=float),
        )

    candidate_sort_indices = np.argsort(candidate_time_array)
    reference_sort_indices = np.argsort(reference_time_array)
    sorted_candidate_times = candidate_time_array[candidate_sort_indices]
    sorted_reference_times = reference_time_array[reference_sort_indices]
    sorted_candidate_values = candidate_value_array[candidate_sort_indices]
    sorted_reference_values = reference_value_array[reference_sort_indices]

    common_times, candidate_indices, reference_indices = np.intersect1d(
        sorted_candidate_times,
        sorted_reference_times,
        assume_unique=False,
        return_indices=True,
    )

    return AlignedSeries(
        times=common_times.astype("datetime64[ns]"),
        candidate=sorted_candidate_values[candidate_indices],
        reference=sorted_reference_values[reference_indices],
    )


def build_paired_dataarrays(
    aligned: AlignedSeries,
) -> tuple[xr.DataArray, xr.DataArray]:
    """Build paired xarray DataArrays with a common finite mask."""
    candidate = np.asarray(aligned.candidate, dtype=float)
    reference = np.asarray(aligned.reference, dtype=float)
    paired_mask = aligned.paired_finite_mask

    candidate_paired = np.where(paired_mask, candidate, np.nan)
    reference_paired = np.where(paired_mask, reference, np.nan)

    return (
        xr.DataArray(
            candidate_paired,
            dims=["time"],
            coords={"time": aligned.times},
        ),
        xr.DataArray(
            reference_paired,
            dims=["time"],
            coords={"time": aligned.times},
        ),
    )
