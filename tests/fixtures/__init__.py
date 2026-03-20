"""Reusable fixtures for development smoke tests and automated tests.

The fixture modules intentionally mirror the main integration flow:

- `paths.py`: where the test data lives
- `source_specifications.py`: how each test source is described semantically
- `adapters.py`: how those sources become `DataAdapter` instances
- `requests.py`: ready-to-use requests for the most common MVP scenarios
"""

from .adapters import (
    build_ceilometro_adapter,
    build_model_u_adapter,
    build_radiosonde_u_adapter,
)
from .paths import (
    DATAFILES_DIR,
    MODELO_U_PATH,
    OBS_CEILOMETRO_PATH,
    OBS_RADIOSONDA_U_PATH,
    OUTPUT_DIR,
)
from .requests import (
    build_ceilometro_time_series_request,
    build_model_horizontal_field_request,
    build_model_single_time_request,
    build_model_vertical_profile_request,
    build_radiosonde_vertical_profile_request,
)
from .source_specifications import (
    build_ceilometro_source_specification,
    build_model_u_source_specification,
    build_radiosonde_u_source_specification,
)

__all__ = [
    "DATAFILES_DIR",
    "MODELO_U_PATH",
    "OBS_CEILOMETRO_PATH",
    "OBS_RADIOSONDA_U_PATH",
    "OUTPUT_DIR",
    "build_ceilometro_adapter",
    "build_ceilometro_source_specification",
    "build_ceilometro_time_series_request",
    "build_model_horizontal_field_request",
    "build_model_single_time_request",
    "build_model_u_adapter",
    "build_model_u_source_specification",
    "build_model_vertical_profile_request",
    "build_radiosonde_u_adapter",
    "build_radiosonde_u_source_specification",
    "build_radiosonde_vertical_profile_request",
]
