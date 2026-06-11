from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
import re
from typing import Literal, cast

import numpy as np

SCENARIOS_DIR = Path(__file__).resolve().parent
PLOT_CORE_DIR = SCENARIOS_DIR.parent
PROJECT_ROOT = PLOT_CORE_DIR.parent
FIXTURES_DIR = SCENARIOS_DIR
TESTS_DIR = PROJECT_ROOT / "tests"
DATAFILES_DIR = TESTS_DIR / "datafiles"
OUTPUT_DIR = TESTS_DIR / "output"

MODELO_U_PATH = DATAFILES_DIR / "modelo_u.nc"
OBS_RADIOSONDA_U_PATH = DATAFILES_DIR / "observado_radiosonda_u.nc"
OBS_CEILOMETRO_PATH = DATAFILES_DIR / "observado_ceilometro.csv"

LEGACY_SHOC_MONAN_GLOB_PATTERN = (
    "/mnt/beegfs/guilherme.farache/runs/MONAN/model/"
    "GLOBAL_GFdef_ERA5_x1.655362_shoc_transition_dry/"
    "2014090300/diag/posprocess/diag.*"
)
LEGACY_MONAN_E3SM_GLOB_PATTERN = (
    "/mnt/beegfs/guilherme.farache/runs/MONAN/model/"
    "GLOBAL_GFdef_ERA5_x1.655362_shoc_petervalidation/"
    "2014022400/diag/posprocess/diag.*"
)
LEGACY_E3SM_GLOB_PATTERN = (
    "/mnt/beegfs/guilherme.farache/peter_data/E3SM_in_MONAN*.nc"
)
LEGACY_MYNN_MONAN_GLOB_PATTERN = (
    "/mnt/beegfs/guilherme.farache/runs/MONAN/model/"
    "GLOBAL_GFdef_ERA5_x1.655362_mynn_transition_dry/"
    "2014090300/diag/posprocess/diag.*"
)

TimeSeriesMonanScheme = Literal["mynn", "shoc"]
HpblObservationProcessing = Literal[
    "hourly_nearest_5min",
    "rolling_mean_30min",
    "rolling_median_30min",
]

TIME_SERIES_DEFAULT_INIT_DATE = "20141002"
TIME_SERIES_SUPPORTED_INIT_DATES = (
    "20141002",
    "20140802",
    "20140216",
)
TIME_SERIES_INIT_DATE_TO_MONAN_SEASON = {
    "20141002": "dry_season",
    "20140802": "transition_season",
    "20140216": "wet_season",
}
HPBL_OBSERVATION_PROCESSING_DEFAULT: HpblObservationProcessing = (
    "hourly_nearest_5min"
)
HPBL_OBSERVATION_PROCESSING_OPTIONS: tuple[
    HpblObservationProcessing,
    ...,
] = (
    "hourly_nearest_5min",
    "rolling_mean_30min",
    "rolling_median_30min",
)
TIME_SERIES_FORECAST_DAYS = 5
VERTICAL_PROFILE_LOCAL_HOURS_LT = (2, 8, 14, 20)
VERTICAL_PROFILE_TARGET_UTC_OFFSETS_HOURS = (6, 12, 18, 24)
TIME_SERIES_MONAN_DATAOUT_DIR = (
    "/lustre/projetos/monan_atm/guilherme.farache/runs/MONAN/model/"
    "dataout"
)
TIME_SERIES_ERA5_DIR = (
    "/lustre/projetos/monan_atm/guilherme.farache/ERA5"
)
TIME_SERIES_GOAMAZON_SURFACE_STATION_DIR = (
    "/lustre/projetos/monan_atm/guilherme.farache/GoAmazon_ATTO_data/"
    "b1 (Quality Control applied)/MET"
)
TIME_SERIES_GOAMAZON_RAIN_GAUGE_DIR = (
    "/lustre/projetos/monan_atm/guilherme.farache/GoAmazon_ATTO_data/"
    "b1 (Quality Control applied)/Rain Gauge"
)
TIME_SERIES_GOAMAZON_EDDY_CORRELATION_FLUX_DIR = (
    "/lustre/projetos/monan_atm/guilherme.farache/GoAmazon_ATTO_data/"
    "c1 (Derived products)/mao30qcecorM1.c1"
)
TIME_SERIES_GOAMAZON_CEILOMETER_PBL_HEIGHT_DIR = (
    "/lustre/projetos/monan_atm/guilherme.farache/GoAmazon_ATTO_data/"
    "a0 (Derived Minimal Quality Control)/maoceilpblhtM1.a0"
)
TIME_SERIES_GOAMAZON_CEILOMETER_PBL_HEIGHT_HOURLY_NEAREST_5MIN_DIR = (
    f"{TIME_SERIES_GOAMAZON_CEILOMETER_PBL_HEIGHT_DIR}/"
    "hourly_nearest_5min"
)
TIME_SERIES_GOAMAZON_CEILOMETER_PBL_HEIGHT_ROLLING_MEAN_30MIN_DIR = (
    f"{TIME_SERIES_GOAMAZON_CEILOMETER_PBL_HEIGHT_DIR}/"
    "rolling_mean_30min"
)
TIME_SERIES_GOAMAZON_CEILOMETER_PBL_HEIGHT_ROLLING_MEDIAN_30MIN_DIR = (
    f"{TIME_SERIES_GOAMAZON_CEILOMETER_PBL_HEIGHT_DIR}/"
    "rolling_median_30min"
)
VERTICAL_PROFILE_GOAMAZON_RADIOSONDE_DIR = (
    "/lustre/projetos/monan_atm/guilherme.farache/GoAmazon_ATTO_data/"
    "b1 (Quality Control applied)/Radiosonde"
)
GOAMAZON_RADIOSONDE_FILENAME_RE = re.compile(
    r"maosondewnpnM1\.b1\.(\d{8})\.(\d{4,6})\.cdf$"
)
GOAMAZON_RADIOSONDE_SELECTED_FILENAMES = {
    "20141002": {
        "2014-10-02T00:00:00": "maosondewnpnM1.b1.20141001.234200.cdf",
        "2014-10-02T06:00:00": "maosondewnpnM1.b1.20141002.052800.cdf",
        "2014-10-02T12:00:00": "maosondewnpnM1.b1.20141002.120000.cdf",
        "2014-10-02T18:00:00": "maosondewnpnM1.b1.20141002.172800.cdf",
        "2014-10-03T00:00:00": "maosondewnpnM1.b1.20141002.232800.cdf",
        "2014-10-03T06:00:00": "maosondewnpnM1.b1.20141003.052600.cdf",
        "2014-10-03T12:00:00": "maosondewnpnM1.b1.20141003.113900.cdf",
        "2014-10-03T18:00:00": "maosondewnpnM1.b1.20141003.172700.cdf",
        "2014-10-04T00:00:00": "maosondewnpnM1.b1.20141003.232900.cdf",
        "2014-10-04T06:00:00": "maosondewnpnM1.b1.20141004.052600.cdf",
        "2014-10-04T12:00:00": "maosondewnpnM1.b1.20141004.112900.cdf",
        "2014-10-04T18:00:00": "maosondewnpnM1.b1.20141004.174600.cdf",
        "2014-10-05T00:00:00": "maosondewnpnM1.b1.20141004.233000.cdf",
        "2014-10-05T06:00:00": "maosondewnpnM1.b1.20141005.053000.cdf",
        "2014-10-05T12:00:00": "maosondewnpnM1.b1.20141005.113600.cdf",
        "2014-10-05T18:00:00": "maosondewnpnM1.b1.20141005.172800.cdf",
        "2014-10-06T00:00:00": "maosondewnpnM1.b1.20141005.232900.cdf",
        "2014-10-06T06:00:00": "maosondewnpnM1.b1.20141006.052500.cdf",
        "2014-10-06T12:00:00": "maosondewnpnM1.b1.20141006.113300.cdf",
        "2014-10-06T18:00:00": "maosondewnpnM1.b1.20141006.173000.cdf",
        "2014-10-07T00:00:00": "maosondewnpnM1.b1.20141006.233000.cdf",
    },
    "20140802": {
        "2014-08-02T00:00:00": "maosondewnpnM1.b1.20140801.232800.cdf",
        "2014-08-02T06:00:00": "maosondewnpnM1.b1.20140802.053000.cdf",
        "2014-08-02T12:00:00": "maosondewnpnM1.b1.20140802.112800.cdf",
        "2014-08-02T18:00:00": "maosondewnpnM1.b1.20140802.172700.cdf",
        "2014-08-03T00:00:00": "maosondewnpnM1.b1.20140802.233000.cdf",
        "2014-08-03T06:00:00": "maosondewnpnM1.b1.20140803.052700.cdf",
        "2014-08-03T12:00:00": "maosondewnpnM1.b1.20140803.113100.cdf",
        "2014-08-03T18:00:00": "maosondewnpnM1.b1.20140803.172400.cdf",
        "2014-08-04T00:00:00": "maosondewnpnM1.b1.20140803.233000.cdf",
        "2014-08-04T06:00:00": "maosondewnpnM1.b1.20140804.052900.cdf",
        "2014-08-04T12:00:00": "maosondewnpnM1.b1.20140804.113600.cdf",
        "2014-08-04T18:00:00": "maosondewnpnM1.b1.20140804.172800.cdf",
        "2014-08-05T00:00:00": "maosondewnpnM1.b1.20140804.233000.cdf",
        "2014-08-05T06:00:00": "maosondewnpnM1.b1.20140805.052800.cdf",
        "2014-08-05T12:00:00": "maosondewnpnM1.b1.20140805.113400.cdf",
        "2014-08-05T18:00:00": "maosondewnpnM1.b1.20140805.172900.cdf",
        "2014-08-06T00:00:00": "maosondewnpnM1.b1.20140805.233000.cdf",
        "2014-08-06T06:00:00": "maosondewnpnM1.b1.20140806.053000.cdf",
        "2014-08-06T12:00:00": "maosondewnpnM1.b1.20140806.113700.cdf",
        "2014-08-06T18:00:00": "maosondewnpnM1.b1.20140806.172900.cdf",
        "2014-08-07T00:00:00": "maosondewnpnM1.b1.20140806.233000.cdf",
    },
    "20140216": {
        "2014-02-16T00:00:00": "maosondewnpnM1.b1.20140215.232900.cdf",
        "2014-02-16T06:00:00": "maosondewnpnM1.b1.20140216.052800.cdf",
        "2014-02-16T12:00:00": "maosondewnpnM1.b1.20140216.112600.cdf",
        "2014-02-16T18:00:00": "maosondewnpnM1.b1.20140216.172800.cdf",
        "2014-02-17T00:00:00": "maosondewnpnM1.b1.20140216.232900.cdf",
        "2014-02-17T06:00:00": "maosondewnpnM1.b1.20140217.052900.cdf",
        "2014-02-17T12:00:00": "maosondewnpnM1.b1.20140217.113300.cdf",
        "2014-02-17T18:00:00": "maosondewnpnM1.b1.20140217.172800.cdf",
        "2014-02-18T00:00:00": "maosondewnpnM1.b1.20140217.232900.cdf",
        "2014-02-18T06:00:00": "maosondewnpnM1.b1.20140218.053000.cdf",
        "2014-02-18T12:00:00": "maosondewnpnM1.b1.20140218.112600.cdf",
        "2014-02-18T18:00:00": "maosondewnpnM1.b1.20140218.172600.cdf",
        "2014-02-19T00:00:00": "maosondewnpnM1.b1.20140218.232900.cdf",
        "2014-02-19T06:00:00": "maosondewnpnM1.b1.20140219.052900.cdf",
        "2014-02-19T12:00:00": "maosondewnpnM1.b1.20140219.113400.cdf",
        "2014-02-19T18:00:00": "maosondewnpnM1.b1.20140219.113400.cdf",
        "2014-02-20T00:00:00": "maosondewnpnM1.b1.20140220.052900.cdf",
        "2014-02-20T06:00:00": "maosondewnpnM1.b1.20140220.052900.cdf",
        "2014-02-20T12:00:00": "maosondewnpnM1.b1.20140220.112700.cdf",
        "2014-02-20T18:00:00": "maosondewnpnM1.b1.20140220.174500.cdf",
        "2014-02-21T00:00:00": "maosondewnpnM1.b1.20140220.233000.cdf",
    },
}


def normalize_time_series_init_date(
    init_date: object = TIME_SERIES_DEFAULT_INIT_DATE,
) -> str:
    """Return a supported time-series init date as `YYYYMMDD`."""
    raw_value = str(init_date).strip()
    if "-" in raw_value[:10]:
        compact_date = raw_value[:10].replace("-", "")
    else:
        compact_date = raw_value[:8]

    if compact_date not in TIME_SERIES_INIT_DATE_TO_MONAN_SEASON:
        supported_dates = ", ".join(TIME_SERIES_SUPPORTED_INIT_DATES)
        raise ValueError(
            "Unsupported time-series init date "
            f"{init_date!r}. Supported dates: {supported_dates}."
        )

    return compact_date


def build_time_series_init_datetime_string(
    init_date: object = TIME_SERIES_DEFAULT_INIT_DATE,
) -> str:
    """Return the supported init date as an ISO midnight timestamp."""
    compact_date = normalize_time_series_init_date(init_date)
    return (
        f"{compact_date[:4]}-{compact_date[4:6]}-"
        f"{compact_date[6:]}T00:00:00"
    )


def build_vertical_profile_local_day_target_times(
    *,
    init_date: object = TIME_SERIES_DEFAULT_INIT_DATE,
    forecast_day_index: int,
) -> np.ndarray:
    """Return target times for one GMT-4 local forecast day."""
    if forecast_day_index < 0 or forecast_day_index >= TIME_SERIES_FORECAST_DAYS:
        raise ValueError(
            "forecast_day_index must be between 0 and "
            f"{TIME_SERIES_FORECAST_DAYS - 1}."
        )

    local_day_start = (
        np.datetime64(build_time_series_init_datetime_string(init_date), "ns")
        + np.timedelta64(forecast_day_index, "D")
    )
    return np.asarray(
        [
            local_day_start + np.timedelta64(hour_offset, "h")
            for hour_offset in VERTICAL_PROFILE_TARGET_UTC_OFFSETS_HOURS
        ],
        dtype="datetime64[ns]",
    )


def build_vertical_profile_all_local_day_target_times(
    init_date: object = TIME_SERIES_DEFAULT_INIT_DATE,
) -> np.ndarray:
    """Return all profile target times for the five GMT-4 local days."""
    return np.concatenate(
        [
            build_vertical_profile_local_day_target_times(
                init_date=init_date,
                forecast_day_index=forecast_day_index,
            )
            for forecast_day_index in range(TIME_SERIES_FORECAST_DAYS)
        ]
    )


def build_time_series_season_label(
    init_date: object = TIME_SERIES_DEFAULT_INIT_DATE,
) -> str:
    """Return a human-readable season label for one comparison case."""
    compact_date = normalize_time_series_init_date(init_date)
    season_name = TIME_SERIES_INIT_DATE_TO_MONAN_SEASON[compact_date]
    return season_name.replace("_", " ").title()


def build_time_series_monan_glob_pattern(
    *,
    scheme: TimeSeriesMonanScheme,
    init_date: object = TIME_SERIES_DEFAULT_INIT_DATE,
) -> str:
    """Return the MONAN post-processed file glob for one comparison case."""
    compact_date = normalize_time_series_init_date(init_date)
    season = TIME_SERIES_INIT_DATE_TO_MONAN_SEASON[compact_date]
    return (
        f"{TIME_SERIES_MONAN_DATAOUT_DIR}/"
        f"REGNOL2_GFdef_ERA5_10km_{scheme}_{season}/{compact_date}00/"
        "diag/posprocess/*.nc"
    )


def build_time_series_era5_path(
    init_date: object = TIME_SERIES_DEFAULT_INIT_DATE,
) -> str:
    """Return the ERA5 GRIB path for one comparison case."""
    compact_date = normalize_time_series_init_date(init_date)
    return f"{TIME_SERIES_ERA5_DIR}/sl_{compact_date}.grib"


def build_vertical_profile_era5_path(
    init_date: object = TIME_SERIES_DEFAULT_INIT_DATE,
) -> str:
    """Return the ERA5 pressure-level GRIB path for one profile case."""
    compact_date = normalize_time_series_init_date(init_date)
    return f"{TIME_SERIES_ERA5_DIR}/pl_{compact_date}.grib"


def build_time_series_goamazon_surface_station_glob_patterns(
    init_date: object = TIME_SERIES_DEFAULT_INIT_DATE,
) -> tuple[str, ...]:
    """Return exact daily GoAmazon station globs for the 5-day window."""
    compact_date = normalize_time_series_init_date(init_date)
    start_date = datetime.strptime(compact_date, "%Y%m%d").date()
    return tuple(
        (
            f"{TIME_SERIES_GOAMAZON_SURFACE_STATION_DIR}/"
            f"maometM1.b1.{(start_date + timedelta(days=day_offset)):%Y%m%d}"
            "*.cdf"
        )
        for day_offset in range(TIME_SERIES_FORECAST_DAYS)
    )


def build_surface_flux_goamazon_eddy_correlation_glob_patterns(
    init_date: object = TIME_SERIES_DEFAULT_INIT_DATE,
) -> tuple[str, ...]:
    """Return exact daily corrected GoAmazon C1 eddy-correlation globs."""
    compact_date = normalize_time_series_init_date(init_date)
    start_date = datetime.strptime(compact_date, "%Y%m%d").date()
    return tuple(
        (
            f"{TIME_SERIES_GOAMAZON_EDDY_CORRELATION_FLUX_DIR}/"
            "mao30qcecorM1.c1."
            f"{(start_date + timedelta(days=day_offset)):%Y%m%d}*.nc"
        )
        for day_offset in range(TIME_SERIES_FORECAST_DAYS)
    )


def build_time_series_goamazon_rain_gauge_precipitation_glob_patterns(
    init_date: object = TIME_SERIES_DEFAULT_INIT_DATE,
) -> tuple[str, ...]:
    """Return exact daily rain-gauge globs for the 5-day window."""
    compact_date = normalize_time_series_init_date(init_date)
    start_date = datetime.strptime(compact_date, "%Y%m%d").date()
    return tuple(
        (
            f"{TIME_SERIES_GOAMAZON_RAIN_GAUGE_DIR}/"
            f"maoraintbS10.b1."
            f"{(start_date + timedelta(days=day_offset)):%Y%m%d}"
            ".*.cdf"
        )
        for day_offset in range(TIME_SERIES_FORECAST_DAYS)
    )


def build_time_series_goamazon_ceilometer_pbl_height_glob_patterns(
    init_date: object = TIME_SERIES_DEFAULT_INIT_DATE,
) -> tuple[str, ...]:
    """Return exact daily ceilometer PBL-height globs for the 5-day window."""
    compact_date = normalize_time_series_init_date(init_date)
    start_date = datetime.strptime(compact_date, "%Y%m%d").date()
    return tuple(
        (
            f"{TIME_SERIES_GOAMAZON_CEILOMETER_PBL_HEIGHT_DIR}/"
            "maoceilpblhtM1.a0."
            f"{(start_date + timedelta(days=day_offset)):%Y%m%d}*.cdf"
        )
        for day_offset in range(TIME_SERIES_FORECAST_DAYS)
    )


def build_time_series_goamazon_ceilometer_pbl_height_hourly_nearest_paths(
    init_date: object = TIME_SERIES_DEFAULT_INIT_DATE,
) -> tuple[str, ...]:
    """Return exact daily preprocessed ceilometer PBL-height paths."""
    compact_date = normalize_time_series_init_date(init_date)
    start_date = datetime.strptime(compact_date, "%Y%m%d").date()
    processed_dir = (
        TIME_SERIES_GOAMAZON_CEILOMETER_PBL_HEIGHT_HOURLY_NEAREST_5MIN_DIR
    )
    return tuple(
        (
            f"{processed_dir}/"
            "maoceilpblhtM1.a0."
            f"{(start_date + timedelta(days=day_offset)):%Y%m%d}.cdf"
        )
        for day_offset in range(TIME_SERIES_FORECAST_DAYS)
    )


def normalize_hpbl_observation_processing(
    observation_processing: object = HPBL_OBSERVATION_PROCESSING_DEFAULT,
) -> HpblObservationProcessing:
    """Return a supported HPBL observation preprocessing selector."""
    normalized = str(observation_processing).strip().replace("-", "_")
    if normalized not in HPBL_OBSERVATION_PROCESSING_OPTIONS:
        supported_options = ", ".join(HPBL_OBSERVATION_PROCESSING_OPTIONS)
        raise ValueError(
            "Unsupported HPBL observation processing "
            f"{observation_processing!r}. Supported options: "
            f"{supported_options}."
        )
    return cast(HpblObservationProcessing, normalized)


def build_time_series_goamazon_ceilometer_pbl_height_rolling_paths(
    *,
    method: Literal["mean", "median"],
    init_date: object = TIME_SERIES_DEFAULT_INIT_DATE,
) -> tuple[str, ...]:
    """Return exact daily rolling-statistic ceilometer PBL-height paths."""
    compact_date = normalize_time_series_init_date(init_date)
    start_date = datetime.strptime(compact_date, "%Y%m%d").date()
    if method == "mean":
        processed_dir = (
            TIME_SERIES_GOAMAZON_CEILOMETER_PBL_HEIGHT_ROLLING_MEAN_30MIN_DIR
        )
    elif method == "median":
        processed_dir = (
            TIME_SERIES_GOAMAZON_CEILOMETER_PBL_HEIGHT_ROLLING_MEDIAN_30MIN_DIR
        )
    else:
        raise ValueError("Rolling HPBL method must be 'mean' or 'median'.")
    return tuple(
        (
            f"{processed_dir}/"
            "maoceilpblhtM1.a0."
            f"{(start_date + timedelta(days=day_offset)):%Y%m%d}.cdf"
        )
        for day_offset in range(TIME_SERIES_FORECAST_DAYS)
    )


def build_time_series_goamazon_ceilometer_pbl_height_processed_paths(
    *,
    observation_processing: object = HPBL_OBSERVATION_PROCESSING_DEFAULT,
    init_date: object = TIME_SERIES_DEFAULT_INIT_DATE,
) -> tuple[str, ...]:
    """Return exact daily HPBL observation paths for one processing product."""
    processing = normalize_hpbl_observation_processing(
        observation_processing
    )
    if processing == "hourly_nearest_5min":
        return (
            build_time_series_goamazon_ceilometer_pbl_height_hourly_nearest_paths(
                init_date=init_date
            )
        )
    if processing == "rolling_mean_30min":
        return build_time_series_goamazon_ceilometer_pbl_height_rolling_paths(
            method="mean",
            init_date=init_date,
        )
    return build_time_series_goamazon_ceilometer_pbl_height_rolling_paths(
        method="median",
        init_date=init_date,
    )


def build_goamazon_radiosonde_glob_patterns(
    init_date: object = TIME_SERIES_DEFAULT_INIT_DATE,
) -> tuple[str, ...]:
    """Return radiosonde globs covering candidate launches for an init date.

    Profile comparison uses `GOAMAZON_RADIOSONDE_SELECTED_FILENAMES` instead
    of inferring from these globs. This helper is kept for diagnostics and for
    rebuilding the manifest when needed.
    """
    compact_date = normalize_time_series_init_date(init_date)
    start_date = datetime.strptime(compact_date, "%Y%m%d").date()
    return tuple(
        (
            f"{VERTICAL_PROFILE_GOAMAZON_RADIOSONDE_DIR}/"
            "maosondewnpnM1.b1."
            f"{(start_date + timedelta(days=day_offset)):%Y%m%d}.*.cdf"
        )
        for day_offset in range(-1, TIME_SERIES_FORECAST_DAYS)
    )


def parse_goamazon_radiosonde_launch_datetime(path: str | Path) -> datetime:
    """Parse the launch datetime encoded in one radiosonde filename."""
    match = GOAMAZON_RADIOSONDE_FILENAME_RE.search(Path(path).name)
    if match is None:
        raise ValueError(
            "Could not parse GoAmazon radiosonde launch time from "
            f"{path!r}."
        )

    date_text, time_text = match.groups()
    if len(time_text) == 4:
        time_text = f"{time_text}00"

    return datetime.strptime(f"{date_text}{time_text}", "%Y%m%d%H%M%S")


def find_selected_goamazon_radiosonde_path(
    *,
    target_time: object,
    init_date: object = TIME_SERIES_DEFAULT_INIT_DATE,
) -> str:
    """Return the manifest-selected radiosonde path for a target."""
    compact_date = normalize_time_series_init_date(init_date)
    target_key = str(
        np.datetime_as_string(
            np.datetime64(target_time, "s"),
            unit="s",
        )
    )
    selected_filenames = GOAMAZON_RADIOSONDE_SELECTED_FILENAMES.get(
        compact_date
    )
    if selected_filenames is None:
        raise KeyError(
            "No configured GoAmazon radiosonde manifest exists for "
            f"init date {compact_date!r}."
        )

    selected_filename = selected_filenames.get(target_key)
    if selected_filename is None:
        raise KeyError(
            "No configured GoAmazon radiosonde file exists for "
            f"init date {compact_date!r} and target time {target_key!r}."
        )

    selected_path = (
        Path(VERTICAL_PROFILE_GOAMAZON_RADIOSONDE_DIR) / selected_filename
    )
    if not selected_path.exists():
        raise FileNotFoundError(
            "The configured GoAmazon radiosonde file is missing for "
            f"init date {compact_date!r} and target time {target_key!r}: "
            f"{selected_path}"
        )
    return str(selected_path)


def find_nearest_goamazon_radiosonde_path(
    *,
    target_time: object,
    init_date: object = TIME_SERIES_DEFAULT_INIT_DATE,
) -> str:
    """Return the selected radiosonde file for one target datetime.

    Profile-comparison target times use the deterministic
    `GOAMAZON_RADIOSONDE_SELECTED_FILENAMES` manifest. Missing manifest
    entries or files are treated as configuration errors; this function does
    not infer a replacement from nearby files.
    """
    return find_selected_goamazon_radiosonde_path(
        target_time=target_time,
        init_date=init_date,
    )

TIME_SERIES_MONAN_MYNN_GLOB_PATTERN = build_time_series_monan_glob_pattern(
    scheme="mynn"
)
TIME_SERIES_MONAN_SHOC_GLOB_PATTERN = build_time_series_monan_glob_pattern(
    scheme="shoc"
)
TIME_SERIES_ERA5_PATH = build_time_series_era5_path()
TIME_SERIES_GOAMAZON_SURFACE_STATION_GLOB_PATTERNS = (
    build_time_series_goamazon_surface_station_glob_patterns()
)
TIME_SERIES_GOAMAZON_SURFACE_STATION_GLOB_PATTERN = (
    TIME_SERIES_GOAMAZON_SURFACE_STATION_GLOB_PATTERNS[0]
)
TIME_SERIES_GOAMAZON_EDDY_CORRELATION_FLUX_GLOB_PATTERNS = (
    build_surface_flux_goamazon_eddy_correlation_glob_patterns()
)
TIME_SERIES_GOAMAZON_CEILOMETER_PBL_HEIGHT_GLOB_PATTERNS = (
    build_time_series_goamazon_ceilometer_pbl_height_glob_patterns()
)
TIME_SERIES_GOAMAZON_CEILOMETER_PBL_HEIGHT_HOURLY_NEAREST_5MIN_PATHS = (
    build_time_series_goamazon_ceilometer_pbl_height_hourly_nearest_paths()
)
TIME_SERIES_GOAMAZON_CEILOMETER_PBL_HEIGHT_ROLLING_MEAN_30MIN_PATHS = (
    build_time_series_goamazon_ceilometer_pbl_height_rolling_paths(
        method="mean"
    )
)
TIME_SERIES_GOAMAZON_CEILOMETER_PBL_HEIGHT_ROLLING_MEDIAN_30MIN_PATHS = (
    build_time_series_goamazon_ceilometer_pbl_height_rolling_paths(
        method="median"
    )
)
