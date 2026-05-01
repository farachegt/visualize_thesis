from __future__ import annotations

from plot_core.adapter import DataAdapter

from .paths import (
    LEGACY_E3SM_GLOB_PATTERN,
    LEGACY_MONAN_E3SM_GLOB_PATTERN,
    LEGACY_MYNN_MONAN_GLOB_PATTERN,
    LEGACY_SHOC_MONAN_GLOB_PATTERN,
    MODELO_U_PATH,
    OBS_CEILOMETRO_PATH,
    OBS_RADIOSONDA_U_PATH,
    TIME_SERIES_DEFAULT_INIT_DATE,
    build_surface_flux_goamazon_eddy_correlation_glob_patterns,
    build_time_series_era5_path,
    build_time_series_goamazon_surface_station_glob_patterns,
    build_time_series_monan_glob_pattern,
)
from .source_specifications import (
    build_surface_flux_goamazon_eddy_correlation_source_specification,
    build_surface_flux_time_series_era5_source_specification,
    build_surface_flux_time_series_mynn_source_specification,
    build_surface_flux_time_series_shoc_source_specification,
    build_ceilometro_source_specification,
    build_legacy_e3sm_source_specification,
    build_legacy_monan_e3sm_source_specification,
    build_legacy_mynn_monan_source_specification,
    build_legacy_shoc_monan_source_specification,
    build_model_u_source_specification,
    build_radiosonde_u_source_specification,
    build_time_series_era5_source_specification,
    build_time_series_goamazon_surface_station_source_specification,
    build_time_series_mynn_source_specification,
    build_time_series_shoc_source_specification,
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


def build_legacy_shoc_monan_adapter() -> DataAdapter:
    """Build a `DataAdapter` for the legacy SHOC MONAN run.

    Returns
    -------
    DataAdapter
        Adapter configured with the same glob pattern used by the old
        `visualizations.main()` workflow.
    """
    return DataAdapter(
        glob_pattern=LEGACY_SHOC_MONAN_GLOB_PATTERN,
        file_format="netcdf",
        geometry_type="gridded",
        source_specification=build_legacy_shoc_monan_source_specification(),
        reader_options={
            "combine": "nested",
            "concat_dim": "Time",
            "parallel": True,
        },
    )


def build_legacy_monan_e3sm_adapter() -> DataAdapter:
    """Build a `DataAdapter` for the legacy MONAN versus E3SM run.

    Returns
    -------
    DataAdapter
        Adapter configured with the MONAN path used in the old
        `monan_data_subset` workflow.
    """
    return DataAdapter(
        glob_pattern=LEGACY_MONAN_E3SM_GLOB_PATTERN,
        file_format="netcdf",
        geometry_type="gridded",
        source_specification=build_legacy_monan_e3sm_source_specification(),
        reader_options={
            "combine": "nested",
            "concat_dim": "Time",
            "parallel": True,
        },
    )


def build_legacy_e3sm_adapter() -> DataAdapter:
    """Build a `DataAdapter` for the legacy E3SM comparison files.

    Returns
    -------
    DataAdapter
        Adapter configured with the same glob pattern used by the commented
        E3SM path in the old `visualizations.main()` workflow.
    """
    return DataAdapter(
        glob_pattern=LEGACY_E3SM_GLOB_PATTERN,
        file_format="netcdf",
        geometry_type="gridded",
        source_specification=build_legacy_e3sm_source_specification(),
        reader_options={
            "combine": "by_coords",
            "parallel": True,
        },
    )


def build_legacy_mynn_monan_adapter() -> DataAdapter:
    """Build a `DataAdapter` for the legacy MYNN MONAN run.

    Returns
    -------
    DataAdapter
        Adapter configured with the same glob pattern used by the old
        `visualizations.main()` workflow.
    """
    return DataAdapter(
        glob_pattern=LEGACY_MYNN_MONAN_GLOB_PATTERN,
        file_format="netcdf",
        geometry_type="gridded",
        source_specification=build_legacy_mynn_monan_source_specification(),
        reader_options={
            "combine": "nested",
            "concat_dim": "Time",
            "parallel": True,
        },
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


def build_time_series_mynn_adapter(
    *,
    init_date: object = TIME_SERIES_DEFAULT_INIT_DATE,
) -> DataAdapter:
    """Build the MYNN MONAN adapter for the surface time-series scenario."""
    return DataAdapter(
        glob_pattern=build_time_series_monan_glob_pattern(
            scheme="mynn",
            init_date=init_date,
        ),
        file_format="netcdf",
        geometry_type="gridded",
        source_specification=build_time_series_mynn_source_specification(),
        reader_options={
            "combine": "nested",
            "concat_dim": "Time",
            "parallel": True,
        },
    )


def build_time_series_shoc_adapter(
    *,
    init_date: object = TIME_SERIES_DEFAULT_INIT_DATE,
) -> DataAdapter:
    """Build the SHOC MONAN adapter for the surface time-series scenario."""
    return DataAdapter(
        glob_pattern=build_time_series_monan_glob_pattern(
            scheme="shoc",
            init_date=init_date,
        ),
        file_format="netcdf",
        geometry_type="gridded",
        source_specification=build_time_series_shoc_source_specification(),
        reader_options={
            "combine": "nested",
            "concat_dim": "Time",
            "parallel": True,
        },
    )


def build_time_series_era5_adapter(
    *,
    init_date: object = TIME_SERIES_DEFAULT_INIT_DATE,
) -> DataAdapter:
    """Build the ERA5 adapter for the surface time-series scenario."""
    return DataAdapter(
        path=build_time_series_era5_path(init_date),
        file_format="grib",
        geometry_type="gridded",
        source_specification=build_time_series_era5_source_specification(),
        reader_options={"engine": "cfgrib"},
    )


def build_time_series_goamazon_surface_station_adapter(
    *,
    init_date: object = TIME_SERIES_DEFAULT_INIT_DATE,
) -> DataAdapter:
    """Build the GoAmazon station adapter for the time-series scenario."""
    return DataAdapter(
        glob_patterns=build_time_series_goamazon_surface_station_glob_patterns(
            init_date=init_date
        ),
        file_format="netcdf",
        geometry_type="fixed_point",
        source_specification=(
            build_time_series_goamazon_surface_station_source_specification()
        ),
        reader_options={},
    )


def build_surface_flux_time_series_mynn_adapter(
    *,
    init_date: object = TIME_SERIES_DEFAULT_INIT_DATE,
) -> DataAdapter:
    """Build the MYNN MONAN adapter for surface-flux time series."""
    return DataAdapter(
        glob_pattern=build_time_series_monan_glob_pattern(
            scheme="mynn",
            init_date=init_date,
        ),
        file_format="netcdf",
        geometry_type="gridded",
        source_specification=(
            build_surface_flux_time_series_mynn_source_specification()
        ),
        reader_options={
            "combine": "nested",
            "concat_dim": "Time",
            "parallel": True,
        },
    )


def build_surface_flux_time_series_shoc_adapter(
    *,
    init_date: object = TIME_SERIES_DEFAULT_INIT_DATE,
) -> DataAdapter:
    """Build the SHOC MONAN adapter for surface-flux time series."""
    return DataAdapter(
        glob_pattern=build_time_series_monan_glob_pattern(
            scheme="shoc",
            init_date=init_date,
        ),
        file_format="netcdf",
        geometry_type="gridded",
        source_specification=(
            build_surface_flux_time_series_shoc_source_specification()
        ),
        reader_options={
            "combine": "nested",
            "concat_dim": "Time",
            "parallel": True,
        },
    )


def build_surface_flux_time_series_era5_adapter(
    *,
    init_date: object = TIME_SERIES_DEFAULT_INIT_DATE,
) -> DataAdapter:
    """Build the ERA5 adapter for surface-flux time series."""
    return DataAdapter(
        path=build_time_series_era5_path(init_date),
        file_format="grib",
        geometry_type="gridded",
        source_specification=(
            build_surface_flux_time_series_era5_source_specification()
        ),
        reader_options={
            "engine": "cfgrib",
            "backend_kwargs": {
                "filter_by_keys": {
                    "shortName": ["sshf", "slhf"],
                },
            },
        },
    )


def build_surface_flux_goamazon_eddy_correlation_adapter(
    *,
    init_date: object = TIME_SERIES_DEFAULT_INIT_DATE,
) -> DataAdapter:
    """Build the GoAmazon eddy-correlation adapter for flux time series."""
    return DataAdapter(
        glob_patterns=(
            build_surface_flux_goamazon_eddy_correlation_glob_patterns(
                init_date=init_date
            )
        ),
        file_format="netcdf",
        geometry_type="fixed_point",
        source_specification=(
            build_surface_flux_goamazon_eddy_correlation_source_specification()
        ),
        reader_options={},
    )
