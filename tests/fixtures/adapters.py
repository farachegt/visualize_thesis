from __future__ import annotations

from plot_core.adapter import DataAdapter

from .paths import MODELO_U_PATH, OBS_CEILOMETRO_PATH, OBS_RADIOSONDA_U_PATH
from .source_specifications import (
    build_ceilometro_source_specification,
    build_model_u_source_specification,
    build_radiosonde_u_source_specification,
)


def build_model_u_adapter() -> DataAdapter:
    """Build a `DataAdapter` for the model wind test file.

    Returns
    -------
    DataAdapter
        Adapter configured for the gridded model NetCDF fixture.
    """
    return DataAdapter(
        path=MODELO_U_PATH,
        file_format="netcdf",
        geometry_type="gridded",
        source_specification=build_model_u_source_specification(),
    )


def build_radiosonde_u_adapter() -> DataAdapter:
    """Build a `DataAdapter` for the radiosonde wind test file.

    Returns
    -------
    DataAdapter
        Adapter configured for the moving-point radiosonde NetCDF fixture.
    """
    return DataAdapter(
        path=OBS_RADIOSONDA_U_PATH,
        file_format="netcdf",
        geometry_type="moving_point",
        source_specification=build_radiosonde_u_source_specification(),
    )


def build_ceilometro_adapter() -> DataAdapter:
    """Build a `DataAdapter` for the ceilometer CSV test file.

    Returns
    -------
    DataAdapter
        Adapter configured for the fixed-point ceilometer CSV fixture.
    """
    return DataAdapter(
        path=OBS_CEILOMETRO_PATH,
        file_format="csv",
        geometry_type="fixed_point",
        source_specification=build_ceilometro_source_specification(),
        reader_options={"parse_dates": ["datetime"]},
    )
