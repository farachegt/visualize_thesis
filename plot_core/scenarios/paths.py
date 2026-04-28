from __future__ import annotations

from pathlib import Path

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

TIME_SERIES_MONAN_MYNN_GLOB_PATTERN = (
    "/lustre/projetos/monan_atm/guilherme.farache/runs/MONAN/model/"
    "dataout/REGNOL2_GFdef_ERA5_10km_mynn_dry_season/2014100200/"
    "diag/posprocess/*.nc"
)
TIME_SERIES_MONAN_SHOC_GLOB_PATTERN = (
    "/lustre/projetos/monan_atm/guilherme.farache/runs/MONAN/model/"
    "dataout/REGNOL2_GFdef_ERA5_10km_shoc_dry_season/2014100200/"
    "diag/posprocess/*.nc"
)
TIME_SERIES_ERA5_PATH = (
    "/lustre/projetos/monan_atm/guilherme.farache/ERA5/sl_20141002.grib"
)
TIME_SERIES_GOAMAZON_SURFACE_STATION_GLOB_PATTERN = (
    "/lustre/projetos/monan_atm/guilherme.farache/GoAmazon_ATTO_data/"
    "b1 (Quality Control applied)/MET/maometM1.b1.2014100[2-6]*.cdf"
)
