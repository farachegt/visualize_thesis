from __future__ import annotations

from datetime import datetime, timedelta
from glob import glob
from pathlib import Path
import re
from typing import Literal

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
TIME_SERIES_FORECAST_DAYS = 5
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
TIME_SERIES_GOAMAZON_EDDY_CORRELATION_FLUX_DIR = (
    "/lustre/projetos/monan_atm/guilherme.farache/GoAmazon_ATTO_data/"
    "c1 (Derived products)/mao30qcecorM1.c1"
)
VERTICAL_PROFILE_GOAMAZON_RADIOSONDE_DIR = (
    "/lustre/projetos/monan_atm/guilherme.farache/GoAmazon_ATTO_data/"
    "b1 (Quality Control applied)/Radiosonde"
)
GOAMAZON_RADIOSONDE_FILENAME_RE = re.compile(
    r"maosondewnpnM1\.b1\.(\d{8})\.(\d{4,6})\.cdf$"
)


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


def build_goamazon_radiosonde_glob_patterns(
    init_date: object = TIME_SERIES_DEFAULT_INIT_DATE,
) -> tuple[str, ...]:
    """Return exact daily radiosonde globs for the 5-day window."""
    compact_date = normalize_time_series_init_date(init_date)
    start_date = datetime.strptime(compact_date, "%Y%m%d").date()
    return tuple(
        (
            f"{VERTICAL_PROFILE_GOAMAZON_RADIOSONDE_DIR}/"
            "maosondewnpnM1.b1."
            f"{(start_date + timedelta(days=day_offset)):%Y%m%d}.*.cdf"
        )
        for day_offset in range(TIME_SERIES_FORECAST_DAYS)
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


def find_nearest_goamazon_radiosonde_path(
    *,
    target_time: object,
    init_date: object = TIME_SERIES_DEFAULT_INIT_DATE,
) -> str:
    """Return the radiosonde file nearest to one target datetime."""
    target_datetime = _datetime64_to_datetime(
        np.datetime64(target_time, "ns")
    )
    candidates: list[tuple[float, str]] = []
    for glob_pattern in build_goamazon_radiosonde_glob_patterns(init_date):
        for path in glob(glob_pattern):
            launch_datetime = parse_goamazon_radiosonde_launch_datetime(path)
            candidates.append(
                (abs((launch_datetime - target_datetime).total_seconds()), path)
            )

    if not candidates:
        raise FileNotFoundError(
            "No GoAmazon radiosonde files matched the configured 5-day "
            f"window for init date {init_date!r}."
        )

    _, nearest_path = min(candidates, key=lambda item: item[0])
    return nearest_path


def _datetime64_to_datetime(value: np.datetime64) -> datetime:
    """Convert a numpy datetime64 value into a Python datetime."""
    seconds_since_epoch = (
        np.datetime64(value, "s") - np.datetime64("1970-01-01T00:00:00", "s")
    ).astype(int)
    return datetime.utcfromtimestamp(int(seconds_since_epoch))


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
