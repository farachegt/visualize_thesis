from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
import sys
from typing import Literal, Sequence

import numpy as np
import xarray as xr

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from plot_core.scenarios.paths import (  # noqa: E402
    TIME_SERIES_DEFAULT_INIT_DATE,
    TIME_SERIES_FORECAST_DAYS,
    TIME_SERIES_GOAMAZON_CEILOMETER_PBL_HEIGHT_DIR,
    TIME_SERIES_GOAMAZON_CEILOMETER_PBL_HEIGHT_HOURLY_NEAREST_5MIN_DIR,
    TIME_SERIES_SUPPORTED_INIT_DATES,
    normalize_time_series_init_date,
)

RAW_FILE_STEM = "maoceilpblhtM1.a0"
TIME_NAME = "time"
VARIABLE_NAME = "bl_height_1"
DEFAULT_WINDOW_MINUTES = 5

FileStatus = Literal["written", "skipped"]


@dataclass(frozen=True)
class PreprocessedFileResult:
    """Describe one preprocessing output file."""

    path: Path
    status: FileStatus


def select_hourly_nearest_finite_values(
    *,
    source_times: Sequence[object],
    source_values: Sequence[float],
    start_time: np.datetime64,
    end_time_exclusive: np.datetime64,
    window_minutes: int = DEFAULT_WINDOW_MINUTES,
) -> tuple[np.ndarray, np.ndarray]:
    """Return hourly nearest finite values inside a symmetric time window."""
    if window_minutes <= 0:
        raise ValueError("window_minutes must be positive.")

    times = np.asarray(source_times, dtype="datetime64[ns]").reshape(-1)
    values = np.asarray(source_values, dtype=float).reshape(-1)
    if times.size != values.size:
        raise ValueError(
            "source_times and source_values must have the same size."
        )

    sort_indices = np.argsort(times)
    times = times[sort_indices]
    values = values[sort_indices]

    hourly_times = _build_hourly_times(start_time, end_time_exclusive)
    hourly_values = np.full(hourly_times.shape, np.nan, dtype=float)
    if times.size == 0:
        return hourly_times, hourly_values

    time_int = times.astype("datetime64[ns]").astype(np.int64)
    value_is_finite = np.isfinite(values)
    window_delta = np.timedelta64(window_minutes, "m")
    window_ns = window_delta.astype("timedelta64[ns]").astype(np.int64)

    for hourly_index, hourly_time in enumerate(hourly_times):
        target_ns = hourly_time.astype("datetime64[ns]").astype(np.int64)
        distances = np.abs(time_int - target_ns)
        candidate_mask = (distances <= window_ns) & value_is_finite
        if not np.any(candidate_mask):
            continue

        candidate_indices = np.flatnonzero(candidate_mask)
        candidate_distances = distances[candidate_indices]
        minimum_distance = np.min(candidate_distances)
        closest_indices = candidate_indices[
            candidate_distances == minimum_distance
        ]
        hourly_values[hourly_index] = float(values[closest_indices[0]])

    return hourly_times, hourly_values


def preprocess_init_date(
    *,
    init_date: object = TIME_SERIES_DEFAULT_INIT_DATE,
    output_dir: Path | None = None,
    window_minutes: int = DEFAULT_WINDOW_MINUTES,
    overwrite: bool = False,
) -> list[PreprocessedFileResult]:
    """Preprocess the five daily HPBL observation files for one init date."""
    compact_date = normalize_time_series_init_date(init_date)
    start_date = datetime.strptime(compact_date, "%Y%m%d").date()
    destination_dir = output_dir or Path(
        TIME_SERIES_GOAMAZON_CEILOMETER_PBL_HEIGHT_HOURLY_NEAREST_5MIN_DIR
    )
    return [
        preprocess_day(
            target_day=start_date + timedelta(days=day_offset),
            output_dir=destination_dir,
            window_minutes=window_minutes,
            overwrite=overwrite,
        )
        for day_offset in range(TIME_SERIES_FORECAST_DAYS)
    ]


def preprocess_day(
    *,
    target_day: date,
    output_dir: Path,
    window_minutes: int = DEFAULT_WINDOW_MINUTES,
    overwrite: bool = False,
    raw_dir: Path | None = None,
) -> PreprocessedFileResult:
    """Write one daily hourly-nearest HPBL observation file."""
    destination = _build_output_path(output_dir, target_day)
    if destination.exists() and not overwrite:
        return PreprocessedFileResult(path=destination, status="skipped")

    source_dir = raw_dir or Path(
        TIME_SERIES_GOAMAZON_CEILOMETER_PBL_HEIGHT_DIR
    )
    raw_paths = _find_raw_paths_for_day(target_day, source_dir)
    if not raw_paths:
        raise FileNotFoundError(
            "No raw ceilometer PBL-height files found for "
            f"{target_day:%Y-%m-%d} in {source_dir}."
        )

    source_times, source_values = _read_raw_time_series(raw_paths)
    start_time = np.datetime64(f"{target_day:%Y-%m-%d}T00:00:00", "ns")
    end_time_exclusive = start_time + np.timedelta64(1, "D")
    hourly_times, hourly_values = select_hourly_nearest_finite_values(
        source_times=source_times,
        source_values=source_values,
        start_time=start_time,
        end_time_exclusive=end_time_exclusive,
        window_minutes=window_minutes,
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    dataset = _build_output_dataset(
        hourly_times=hourly_times,
        hourly_values=hourly_values,
        raw_paths=raw_paths,
        window_minutes=window_minutes,
    )
    dataset.to_netcdf(destination)
    return PreprocessedFileResult(path=destination, status="written")


def _build_hourly_times(
    start_time: np.datetime64,
    end_time_exclusive: np.datetime64,
) -> np.ndarray:
    return np.arange(
        start_time,
        end_time_exclusive,
        np.timedelta64(1, "h"),
    ).astype("datetime64[ns]")


def _find_raw_paths_for_day(target_day: date, raw_dir: Path) -> list[Path]:
    raw_paths: list[Path] = []
    for day_offset in (-1, 0, 1):
        candidate_day = target_day + timedelta(days=day_offset)
        raw_paths.extend(
            sorted(
                raw_dir.glob(
                    f"{RAW_FILE_STEM}.{candidate_day:%Y%m%d}*.cdf"
                )
            )
        )
    return sorted(raw_paths)


def _read_raw_time_series(
    raw_paths: Sequence[Path],
) -> tuple[np.ndarray, np.ndarray]:
    time_parts: list[np.ndarray] = []
    value_parts: list[np.ndarray] = []
    for raw_path in raw_paths:
        with xr.open_dataset(raw_path) as dataset:
            if TIME_NAME not in dataset:
                raise KeyError(
                    f"{raw_path} does not contain time coordinate "
                    f"{TIME_NAME!r}."
                )
            if VARIABLE_NAME not in dataset:
                raise KeyError(
                    f"{raw_path} does not contain variable "
                    f"{VARIABLE_NAME!r}."
                )

            times = np.asarray(
                dataset[TIME_NAME].values,
                dtype="datetime64[ns]",
            ).reshape(-1)
            values = np.asarray(dataset[VARIABLE_NAME].values, dtype=float)
            values = np.squeeze(values).reshape(-1)
            if times.size != values.size:
                raise ValueError(
                    f"{raw_path} has {times.size} times but "
                    f"{values.size} {VARIABLE_NAME} values."
                )

            time_parts.append(times)
            value_parts.append(values)

    if not time_parts:
        return (
            np.asarray([], dtype="datetime64[ns]"),
            np.asarray([], dtype=float),
        )
    return np.concatenate(time_parts), np.concatenate(value_parts)


def _build_output_dataset(
    *,
    hourly_times: np.ndarray,
    hourly_values: np.ndarray,
    raw_paths: Sequence[Path],
    window_minutes: int,
) -> xr.Dataset:
    dataset = xr.Dataset(
        data_vars={
            VARIABLE_NAME: (
                (TIME_NAME,),
                hourly_values,
                {
                    "units": "m",
                    "processing_method": "nearest_finite_within_window",
                    "processing_window": f"{window_minutes} minutes",
                },
            )
        },
        coords={TIME_NAME: hourly_times},
        attrs={
            "source_variable": VARIABLE_NAME,
            "source_path_pattern": (
                f"{TIME_SERIES_GOAMAZON_CEILOMETER_PBL_HEIGHT_DIR}/"
                f"{RAW_FILE_STEM}.*.cdf"
            ),
            "source_files": ",".join(str(path) for path in raw_paths),
            "processing_method": "nearest_finite_within_window",
            "processing_window_minutes": int(window_minutes),
        },
    )
    dataset[TIME_NAME].attrs["standard_name"] = "time"
    return dataset


def _build_output_path(output_dir: Path, target_day: date) -> Path:
    return output_dir / f"{RAW_FILE_STEM}.{target_day:%Y%m%d}.cdf"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Preprocess GoAmazon ceilometer HPBL observations to hourly "
            "nearest finite values."
        )
    )
    init_group = parser.add_mutually_exclusive_group(required=True)
    init_group.add_argument(
        "--init-date",
        choices=TIME_SERIES_SUPPORTED_INIT_DATES,
        default=None,
        help="Forecast initialization date selector.",
    )
    init_group.add_argument(
        "--all",
        action="store_true",
        help="Process all supported forecast initialization dates.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help=(
            "Output directory. Default writes to hourly_nearest_5min beside "
            "the raw ceilometer directory."
        ),
    )
    parser.add_argument(
        "--window-minutes",
        type=int,
        default=DEFAULT_WINDOW_MINUTES,
        help="Symmetric nearest-sample window in minutes. Default: 5.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Rewrite existing preprocessed files.",
    )
    return parser.parse_args()


def main() -> None:
    """Preprocess HPBL observations and print output file statuses."""
    args = _parse_args()
    init_dates = (
        TIME_SERIES_SUPPORTED_INIT_DATES
        if args.all
        else (args.init_date,)
    )
    for init_date in init_dates:
        results = preprocess_init_date(
            init_date=init_date,
            output_dir=args.output_dir,
            window_minutes=args.window_minutes,
            overwrite=args.overwrite,
        )
        for result in results:
            print(f"{result.status}: {result.path}")


if __name__ == "__main__":
    main()
