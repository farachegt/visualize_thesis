from __future__ import annotations

from pathlib import Path

FIXTURES_DIR = Path(__file__).resolve().parent
TESTS_DIR = FIXTURES_DIR.parent
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
LEGACY_MYNN_MONAN_GLOB_PATTERN = (
    "/mnt/beegfs/guilherme.farache/runs/MONAN/model/"
    "GLOBAL_GFdef_ERA5_x1.655362_mynn_transition_dry/"
    "2014090300/diag/posprocess/diag.*"
)
