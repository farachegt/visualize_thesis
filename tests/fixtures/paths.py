from __future__ import annotations

from pathlib import Path

FIXTURES_DIR = Path(__file__).resolve().parent
TESTS_DIR = FIXTURES_DIR.parent
DATAFILES_DIR = TESTS_DIR / "datafiles"
OUTPUT_DIR = TESTS_DIR / "output"

MODELO_U_PATH = DATAFILES_DIR / "modelo_u.nc"
OBS_RADIOSONDA_U_PATH = DATAFILES_DIR / "observado_radiosonda_u.nc"
OBS_CEILOMETRO_PATH = DATAFILES_DIR / "observado_ceilometro.csv"
