"""Reusable fixtures for development smoke tests and automated tests.

The fixture modules intentionally mirror the main integration flow:

- `paths.py`: where the test data lives
- `source_specifications.py`: how each test source is described semantically
- `adapters.py`: how those sources become `DataAdapter` instances
- `requests.py`: ready-to-use requests for the most common MVP scenarios
- `recipes.py`: examples of how fixtures can drive high-level recipes
"""

from .adapters import (
    build_ceilometro_adapter,
    build_legacy_e3sm_adapter,
    build_legacy_monan_e3sm_adapter,
    build_legacy_mynn_monan_adapter,
    build_legacy_shoc_monan_adapter,
    build_model_u_adapter,
    build_radiosonde_u_adapter,
)
from .paths import (
    DATAFILES_DIR,
    LEGACY_E3SM_GLOB_PATTERN,
    LEGACY_MONAN_E3SM_GLOB_PATTERN,
    LEGACY_MYNN_MONAN_GLOB_PATTERN,
    LEGACY_SHOC_MONAN_GLOB_PATTERN,
    MODELO_U_PATH,
    OBS_CEILOMETRO_PATH,
    OBS_RADIOSONDA_U_PATH,
    OUTPUT_DIR,
)
from .requests import (
    build_ceilometro_time_series_request,
    build_legacy_chile_coast_vertical_profile_request,
    build_model_horizontal_field_request,
    build_model_single_time_request,
    build_model_vertical_profile_request,
    build_radiosonde_vertical_profile_request,
)
from .recipes import (
    build_legacy_monan_e3sm_cross_section_figure,
    build_legacy_monan_e3sm_cross_section_inputs,
    build_legacy_monan_e3sm_diurnal_amplitude_figure,
    build_legacy_monan_e3sm_diurnal_amplitude_inputs,
    build_legacy_monan_e3sm_hourly_mean_figure,
    build_legacy_monan_e3sm_hourly_mean_inputs,
    build_legacy_monan_e3sm_paper_grade_figure,
    build_legacy_monan_e3sm_paper_grade_inputs,
    build_legacy_monan_e3sm_side_by_side_figure,
    build_legacy_monan_e3sm_side_by_side_inputs,
    build_legacy_main_vertical_profile_recipe_panels,
    build_legacy_vertical_profile_figure_specification,
    build_legacy_vertical_profile_recipe_panels,
    build_vertical_profile_recipe_figure,
    build_vertical_profile_recipe_figure_specification,
    build_vertical_profile_recipe_panel_input,
)
from .source_specifications import (
    build_ceilometro_source_specification,
    build_legacy_e3sm_source_specification,
    build_legacy_monan_e3sm_source_specification,
    build_legacy_mynn_monan_source_specification,
    build_legacy_shoc_monan_source_specification,
    build_model_u_source_specification,
    build_radiosonde_u_source_specification,
)

__all__ = [
    "DATAFILES_DIR",
    "LEGACY_E3SM_GLOB_PATTERN",
    "LEGACY_MONAN_E3SM_GLOB_PATTERN",
    "LEGACY_MYNN_MONAN_GLOB_PATTERN",
    "LEGACY_SHOC_MONAN_GLOB_PATTERN",
    "MODELO_U_PATH",
    "OBS_CEILOMETRO_PATH",
    "OBS_RADIOSONDA_U_PATH",
    "OUTPUT_DIR",
    "build_ceilometro_adapter",
    "build_ceilometro_source_specification",
    "build_ceilometro_time_series_request",
    "build_legacy_e3sm_adapter",
    "build_legacy_e3sm_source_specification",
    "build_legacy_monan_e3sm_adapter",
    "build_legacy_monan_e3sm_source_specification",
    "build_legacy_chile_coast_vertical_profile_request",
    "build_legacy_monan_e3sm_cross_section_figure",
    "build_legacy_monan_e3sm_cross_section_inputs",
    "build_legacy_monan_e3sm_diurnal_amplitude_figure",
    "build_legacy_monan_e3sm_diurnal_amplitude_inputs",
    "build_legacy_monan_e3sm_hourly_mean_figure",
    "build_legacy_monan_e3sm_hourly_mean_inputs",
    "build_legacy_monan_e3sm_paper_grade_figure",
    "build_legacy_monan_e3sm_paper_grade_inputs",
    "build_legacy_monan_e3sm_side_by_side_figure",
    "build_legacy_monan_e3sm_side_by_side_inputs",
    "build_legacy_main_vertical_profile_recipe_panels",
    "build_legacy_mynn_monan_adapter",
    "build_legacy_mynn_monan_source_specification",
    "build_legacy_shoc_monan_adapter",
    "build_legacy_shoc_monan_source_specification",
    "build_model_horizontal_field_request",
    "build_model_single_time_request",
    "build_model_u_adapter",
    "build_model_u_source_specification",
    "build_model_vertical_profile_request",
    "build_radiosonde_u_adapter",
    "build_radiosonde_u_source_specification",
    "build_radiosonde_vertical_profile_request",
    "build_legacy_vertical_profile_figure_specification",
    "build_legacy_vertical_profile_recipe_panels",
    "build_vertical_profile_recipe_figure",
    "build_vertical_profile_recipe_figure_specification",
    "build_vertical_profile_recipe_panel_input",
]
