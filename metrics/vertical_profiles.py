from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable

import numpy as np
import xarray as xr

from plot_core.adapter import DataAdapter
from plot_core.plot_data import VerticalProfilePlotData
from plot_core.scenarios.adapters import (
    build_vertical_profile_mynn_adapter,
    build_vertical_profile_shoc_adapter,
)
from plot_core.scenarios.paths import (
    TIME_SERIES_DEFAULT_INIT_DATE,
    VERTICAL_PROFILE_LOCAL_HOURS_LT as SCENARIO_VERTICAL_PROFILE_LOCAL_HOURS_LT,
    build_vertical_profile_all_local_day_target_times,
    find_nearest_goamazon_radiosonde_path,
    normalize_time_series_init_date,
    parse_goamazon_radiosonde_launch_datetime,
)
from plot_core.scenarios.requests import (
    build_vertical_profile_comparison_gridded_request,
    build_vertical_profile_comparison_radiosonde_request,
)
from plot_core.scenarios.source_specifications import (
    build_goamazon_radiosonde_profile_source_specification,
)

from .registry import (
    BASE_METRIC_NAMES,
    REFERENCE_OBSERVATION,
    VARIABLE_LABELS,
    VARIABLE_UNITS,
    VERTICAL_PROFILE_METRIC_FAMILY,
    build_case_metadata,
)
from .scores import (
    compute_bias,
    compute_corr,
    compute_mae,
    compute_rmse,
    paired_finite_sample_count,
)

VERTICAL_PROFILE_VARIABLES = ("theta", "qv", "wind_speed")
VERTICAL_PROFILE_SOURCE_LABELS = ("SHOC", "MYNN")
VERTICAL_PROFILE_LOCAL_HOURS_LT = SCENARIO_VERTICAL_PROFILE_LOCAL_HOURS_LT
VERTICAL_PROFILE_SYNOPTIC_HOURS = tuple(
    (local_hour + 4) % 24 for local_hour in VERTICAL_PROFILE_LOCAL_HOURS_LT
)
VERTICAL_PROFILE_PRESSURE_BOTTOM_HPA = 1000.0
VERTICAL_PROFILE_PRESSURE_TOP_HPA = 700.0
DEFAULT_RADIOSONDE_TOLERANCE = timedelta(hours=3)
VERTICAL_PROFILE_METRIC_EXCLUDED_TARGET_TIMES = {
    "20140216": frozenset(
        (
            "2014-02-19T18:00:00",
            "2014-02-20T00:00:00",
        )
    ),
}

AlignmentLogger = Callable[[str], None]


@dataclass(frozen=True)
class AcceptedRadiosondeLaunch:
    """Manifest-selected radiosonde launch accepted for one target time."""

    target_time: np.datetime64
    launch_datetime: datetime
    path: str
    delta_seconds: float


@dataclass(frozen=True)
class ProfilePairSamples:
    """Paired profile samples for one target time/source/variable."""

    candidate_values: np.ndarray
    reference_values: np.ndarray

    @property
    def n_samples(self) -> int:
        return int(self.candidate_values.size)


@dataclass
class ProfileAccumulator:
    """Collect valid samples across forecast days for one output row."""

    candidate_values: list[float]
    reference_values: list[float]
    n_profiles: int = 0

    def add(self, samples: ProfilePairSamples) -> None:
        if samples.n_samples == 0:
            return
        self.candidate_values.extend(samples.candidate_values.tolist())
        self.reference_values.extend(samples.reference_values.tolist())
        self.n_profiles += 1


def compute_vertical_profile_metric_rows(
    *,
    init_date: object = TIME_SERIES_DEFAULT_INIT_DATE,
    alignment_logger: AlignmentLogger | None = None,
    radiosonde_tolerance: timedelta = DEFAULT_RADIOSONDE_TOLERANCE,
) -> tuple[list[dict[str, object]], dict[str, str]]:
    """Compute vertical-profile wide metric rows for one supported case."""
    case = build_case_metadata(init_date)
    accumulators = _build_profile_accumulators()
    target_times = build_vertical_profile_target_times(init_date=case.init_date)
    candidate_adapters = {
        "SHOC": build_vertical_profile_shoc_adapter(init_date=case.init_date),
        "MYNN": build_vertical_profile_mynn_adapter(init_date=case.init_date),
    }

    try:
        for target_time in target_times:
            if _is_metric_excluded_target_time(
                target_time=target_time,
                init_date=case.init_date,
            ):
                _log_alignment(
                    alignment_logger,
                    target_time=target_time,
                    launch_datetime=None,
                    delta_seconds=None,
                    status="skipped",
                    reason="configured unavailable radiosonde target",
                )
                continue

            accepted_launch = find_accepted_radiosonde_launch(
                target_time=target_time,
                init_date=case.init_date,
                tolerance=radiosonde_tolerance,
            )
            if accepted_launch is None:
                _log_alignment(
                    alignment_logger,
                    target_time=target_time,
                    launch_datetime=None,
                    delta_seconds=None,
                    status="skipped",
                    reason="outside tolerance",
                )
                continue

            _log_alignment(
                alignment_logger,
                target_time=target_time,
                launch_datetime=accepted_launch.launch_datetime,
                delta_seconds=accepted_launch.delta_seconds,
                status="accepted",
                reason=None,
            )
            radiosonde_adapter = _build_radiosonde_adapter_from_path(
                accepted_launch.path
            )
            try:
                _accumulate_target_profile_samples(
                    accumulators=accumulators,
                    candidate_adapters=candidate_adapters,
                    radiosonde_adapter=radiosonde_adapter,
                    target_time=target_time,
                )
            finally:
                radiosonde_adapter.close()
    finally:
        for adapter in candidate_adapters.values():
            adapter.close()

    return _build_wide_rows_from_accumulators(
        accumulators=accumulators,
        init_date=case.init_date,
        season_slug=case.season_slug,
    ), {
        "case_init_date": case.init_date,
        "season_slug": case.season_slug,
    }


def build_vertical_profile_target_times(
    *,
    init_date: object = TIME_SERIES_DEFAULT_INIT_DATE,
) -> np.ndarray:
    """Return all local-day full-mode vertical-profile target times."""
    return build_vertical_profile_all_local_day_target_times(init_date)


def _is_metric_excluded_target_time(
    *,
    target_time: object,
    init_date: object,
) -> bool:
    compact_date = normalize_time_series_init_date(init_date)
    target_key = str(
        np.datetime_as_string(
            np.datetime64(target_time, "s"),
            unit="s",
        )
    )
    return (
        target_key
        in VERTICAL_PROFILE_METRIC_EXCLUDED_TARGET_TIMES.get(
            compact_date,
            frozenset(),
        )
    )


def find_accepted_radiosonde_launch(
    *,
    target_time: object,
    init_date: object = TIME_SERIES_DEFAULT_INIT_DATE,
    tolerance: timedelta = DEFAULT_RADIOSONDE_TOLERANCE,
) -> AcceptedRadiosondeLaunch | None:
    """Return the selected radiosonde launch if it is within tolerance."""
    compact_date = normalize_time_series_init_date(init_date)
    target_datetime = _datetime64_to_datetime(np.datetime64(target_time, "ns"))
    path = find_nearest_goamazon_radiosonde_path(
        target_time=target_time,
        init_date=compact_date,
    )

    launch_datetime = parse_goamazon_radiosonde_launch_datetime(path)
    delta_seconds = abs((launch_datetime - target_datetime).total_seconds())
    if delta_seconds > tolerance.total_seconds():
        return None

    return AcceptedRadiosondeLaunch(
        target_time=np.datetime64(target_time, "ns"),
        launch_datetime=launch_datetime,
        path=path,
        delta_seconds=delta_seconds,
    )


def align_profile_to_nearest_pressure(
    *,
    candidate_profile: VerticalProfilePlotData,
    reference_profile: VerticalProfilePlotData,
) -> ProfilePairSamples:
    """Align a candidate profile to radiosonde values by nearest pressure."""
    candidate_pressure = np.asarray(
        candidate_profile.vertical_values,
        dtype=float,
    )
    candidate_values = np.asarray(candidate_profile.values, dtype=float)
    reference_pressure = np.asarray(
        reference_profile.vertical_values,
        dtype=float,
    )
    reference_values = np.asarray(reference_profile.values, dtype=float)

    if candidate_pressure.size != candidate_values.size:
        raise ValueError("Candidate profile pressure/value sizes differ.")
    if reference_pressure.size != reference_values.size:
        raise ValueError("Reference profile pressure/value sizes differ.")
    finite_reference_pressure = np.isfinite(reference_pressure)
    reference_pressure = reference_pressure[finite_reference_pressure]
    reference_values = reference_values[finite_reference_pressure]
    if reference_pressure.size == 0:
        return ProfilePairSamples(
            candidate_values=np.asarray([], dtype=float),
            reference_values=np.asarray([], dtype=float),
        )

    in_layer = (
        np.isfinite(candidate_pressure)
        &
        (candidate_pressure <= VERTICAL_PROFILE_PRESSURE_BOTTOM_HPA)
        & (candidate_pressure >= VERTICAL_PROFILE_PRESSURE_TOP_HPA)
    )
    layer_candidate_pressure = candidate_pressure[in_layer]
    layer_candidate_values = candidate_values[in_layer]
    if layer_candidate_pressure.size == 0:
        return ProfilePairSamples(
            candidate_values=np.asarray([], dtype=float),
            reference_values=np.asarray([], dtype=float),
        )

    nearest_reference_indices = nearest_pressure_indices(
        candidate_pressure=layer_candidate_pressure,
        reference_pressure=reference_pressure,
    )
    layer_reference_values = reference_values[nearest_reference_indices]
    paired_mask = (
        np.isfinite(layer_candidate_values)
        & np.isfinite(layer_reference_values)
    )

    return ProfilePairSamples(
        candidate_values=layer_candidate_values[paired_mask],
        reference_values=layer_reference_values[paired_mask],
    )


def nearest_pressure_indices(
    *,
    candidate_pressure: np.ndarray,
    reference_pressure: np.ndarray,
) -> np.ndarray:
    """Return nearest reference-pressure indices for candidate levels."""
    candidate_values = np.asarray(candidate_pressure, dtype=float)
    reference_values = np.asarray(reference_pressure, dtype=float)
    if reference_values.size == 0:
        raise ValueError("Reference pressure array cannot be empty.")
    return np.asarray(
        [
            int(np.nanargmin(np.abs(reference_values - candidate_value)))
            for candidate_value in candidate_values
        ],
        dtype=int,
    )


def _accumulate_target_profile_samples(
    *,
    accumulators: dict[tuple[str, str, int], ProfileAccumulator],
    candidate_adapters: dict[str, DataAdapter],
    radiosonde_adapter: DataAdapter,
    target_time: np.datetime64,
) -> None:
    local_hour = _local_hour_lt(target_time)
    candidate_request = build_vertical_profile_comparison_gridded_request(
        time_value=target_time,
        point_sample_pattern="cross_5",
    )
    radiosonde_request = build_vertical_profile_comparison_radiosonde_request(
        time_value=target_time,
    )

    for variable_name in VERTICAL_PROFILE_VARIABLES:
        reference_profile = radiosonde_adapter.to_vertical_profile_plot_data(
            variable_name=variable_name,
            request=radiosonde_request,
        )
        for source_label, candidate_adapter in candidate_adapters.items():
            candidate_profile, _ = (
                candidate_adapter.to_vertical_profile_mean_std_plot_data(
                    variable_name=variable_name,
                    request=candidate_request,
                )
            )
            samples = align_profile_to_nearest_pressure(
                candidate_profile=candidate_profile,
                reference_profile=reference_profile,
            )
            accumulators[(source_label, variable_name, local_hour)].add(
                samples
            )


def _build_profile_accumulators(
) -> dict[tuple[str, str, int], ProfileAccumulator]:
    accumulators: dict[tuple[str, str, int], ProfileAccumulator] = {}
    for source_label in VERTICAL_PROFILE_SOURCE_LABELS:
        for variable_name in VERTICAL_PROFILE_VARIABLES:
            for local_hour in VERTICAL_PROFILE_LOCAL_HOURS_LT:
                accumulators[(source_label, variable_name, local_hour)] = (
                    ProfileAccumulator(candidate_values=[], reference_values=[])
                )
    return accumulators


def _build_wide_rows_from_accumulators(
    *,
    accumulators: dict[tuple[str, str, int], ProfileAccumulator],
    init_date: str,
    season_slug: str,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for source_label in VERTICAL_PROFILE_SOURCE_LABELS:
        for local_hour in VERTICAL_PROFILE_LOCAL_HOURS_LT:
            for variable_name in VERTICAL_PROFILE_VARIABLES:
                accumulator = accumulators[
                    (source_label, variable_name, local_hour)
                ]
                candidate_da, reference_da = _build_sample_dataarrays(
                    accumulator
                )
                synoptic_hour = _synoptic_hour_utc_from_local_hour(local_hour)
                rows.append(
                    {
                        "case_init_date": init_date,
                        "season": season_slug,
                        "metric_family": VERTICAL_PROFILE_METRIC_FAMILY,
                        "variable": variable_name,
                        "variable_label": VARIABLE_LABELS[variable_name],
                        "source": source_label,
                        "reference_source": REFERENCE_OBSERVATION,
                        "local_hour_lt": f"{local_hour:02d}",
                        "synoptic_hour_utc": f"{synoptic_hour:02d}",
                        "units": VARIABLE_UNITS[variable_name],
                        "n_samples": paired_finite_sample_count(
                            candidate_da,
                            reference_da,
                        ),
                        "n_profiles": accumulator.n_profiles,
                        "bias": compute_bias(candidate_da, reference_da),
                        "mae": compute_mae(candidate_da, reference_da),
                        "rmse": compute_rmse(candidate_da, reference_da),
                        "corr": compute_corr(candidate_da, reference_da),
                    }
                )
    return rows


def _build_sample_dataarrays(
    accumulator: ProfileAccumulator,
) -> tuple[xr.DataArray, xr.DataArray]:
    candidate_values = np.asarray(accumulator.candidate_values, dtype=float)
    reference_values = np.asarray(accumulator.reference_values, dtype=float)
    if candidate_values.size == 0:
        candidate_values = np.asarray([np.nan], dtype=float)
        reference_values = np.asarray([np.nan], dtype=float)
    sample_indices = np.arange(candidate_values.size)
    return (
        xr.DataArray(
            candidate_values,
            dims=["time"],
            coords={"time": sample_indices},
        ),
        xr.DataArray(
            reference_values,
            dims=["time"],
            coords={"time": sample_indices},
        ),
    )


def _build_radiosonde_adapter_from_path(path: str) -> DataAdapter:
    return DataAdapter(
        path=Path(path),
        file_format="netcdf",
        geometry_type="moving_point",
        source_specification=(
            build_goamazon_radiosonde_profile_source_specification()
        ),
        reader_options={},
    )


def _log_alignment(
    alignment_logger: AlignmentLogger | None,
    *,
    target_time: np.datetime64,
    launch_datetime: datetime | None,
    delta_seconds: float | None,
    status: str,
    reason: str | None,
) -> None:
    if alignment_logger is None:
        return

    target_label = np.datetime_as_string(target_time, unit="s")
    if launch_datetime is None:
        launch_label = "unavailable"
        delta_minutes = "nan"
    else:
        launch_label = launch_datetime.isoformat()
        delta_minutes = f"{delta_seconds / 60.0:.1f}"
    reason_suffix = "" if reason is None else f" reason={reason}"
    for source_label in VERTICAL_PROFILE_SOURCE_LABELS:
        alignment_logger(
            "datetime alignment "
            f"{source_label}/Observation: target={target_label} "
            f"observation={launch_label} delta_minutes={delta_minutes} "
            f"status={status}{reason_suffix}"
        )


def _local_hour_lt(target_time: np.datetime64) -> int:
    return int(
        np.datetime64(target_time, "h").astype("datetime64[h]").astype(int)
        - 4
    ) % 24


def _synoptic_hour_utc_from_local_hour(local_hour: int) -> int:
    return (local_hour + 4) % 24


def _datetime64_to_datetime(value: np.datetime64) -> datetime:
    seconds_since_epoch = value.astype("datetime64[s]").astype(int)
    return datetime.utcfromtimestamp(int(seconds_since_epoch))


__all__ = [
    "DEFAULT_RADIOSONDE_TOLERANCE",
    "VERTICAL_PROFILE_PRESSURE_BOTTOM_HPA",
    "VERTICAL_PROFILE_PRESSURE_TOP_HPA",
    "VERTICAL_PROFILE_LOCAL_HOURS_LT",
    "VERTICAL_PROFILE_SYNOPTIC_HOURS",
    "VERTICAL_PROFILE_VARIABLES",
    "align_profile_to_nearest_pressure",
    "build_vertical_profile_target_times",
    "compute_vertical_profile_metric_rows",
    "find_accepted_radiosonde_launch",
    "nearest_pressure_indices",
]
