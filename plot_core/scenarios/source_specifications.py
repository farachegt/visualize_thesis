from __future__ import annotations

from plot_core.specifications import SourceSpecification, VariableSpecification


def build_legacy_e3sm_source_specification() -> SourceSpecification:
    """Build the legacy E3SM source specification.

    Returns
    -------
    SourceSpecification
        Semantic description aligned with the old `visualizations.main()`
        comparison that used the E3SM files collocated onto the MONAN grid.
    """
    return SourceSpecification(
        label="E3SM",
        time_name="time",
        vertical_name="lev",
        latitude_name="latitude",
        longitude_name="longitude",
        longitude_convention="-180_180",
        variables={
            "qc": VariableSpecification(
                source_name="qc",
                input_units="kg kg-1",
            ),
            "qv": VariableSpecification(
                source_name="qv",
                input_units="kg kg-1",
            ),
            "qt": VariableSpecification(
                derivation_kind="qt_from_qc_qv",
                target_units="kg kg-1",
            ),
            "theta": VariableSpecification(
                source_name="PotentialTemperature",
                input_units="K",
            ),
            "tke_pbl": VariableSpecification(
                source_name="tke",
                input_units="m^2 s^-2",
            ),
            "hpbl": VariableSpecification(
                source_name="pbl_height",
                input_units="m",
            ),
            "u_wind": VariableSpecification(
                source_name="U",
                input_units="m s-1",
            ),
            "v_wind": VariableSpecification(
                source_name="V",
                input_units="m s-1",
            ),
            "wind_speed": VariableSpecification(
                derivation_kind="wind_speed_from_uv",
                target_units="m s-1",
            ),
            "sensible_heat_flux": VariableSpecification(
                source_name="surf_sens_flux",
                input_units="W m^-2",
            ),
            "pressure": VariableSpecification(
                source_name="lev",
                input_units="hPa",
                target_units="hPa",
            ),
        },
    )


def build_legacy_monan_e3sm_source_specification() -> SourceSpecification:
    """Build the legacy MONAN source specification used against E3SM.

    Returns
    -------
    SourceSpecification
        Semantic description aligned with the old `monan_data_subset`
        workflow used in MONAN versus E3SM plots.
    """
    return _build_legacy_monan_source_specification(label="MONAN")


def build_legacy_shoc_monan_source_specification() -> SourceSpecification:
    """Build the legacy SHOC MONAN source specification.

    Returns
    -------
    SourceSpecification
        Semantic description aligned with the old `visualizations.main()`
        comparison that used the SHOC MONAN run.
    """
    return _build_legacy_monan_source_specification(
        label="MONAN - SHOC scheme"
    )


def build_legacy_mynn_monan_source_specification() -> SourceSpecification:
    """Build the legacy MYNN MONAN source specification.

    Returns
    -------
    SourceSpecification
        Semantic description aligned with the old `visualizations.main()`
        comparison that used the MYNN MONAN run.
    """
    return _build_legacy_monan_source_specification(
        label="MONAN - MYNN scheme"
    )


def build_model_u_source_specification() -> SourceSpecification:
    """Build the source specification for the model wind test file.

    Returns
    -------
    SourceSpecification
        Semantic description of the model NetCDF file stored in
        `tests/datafiles/modelo_u.nc`.
    """
    return SourceSpecification(
        label="MONAN",
        time_name="Time",
        vertical_name="level",
        latitude_name="latitude",
        longitude_name="longitude",
        variables={
            "u_wind": VariableSpecification(
                source_name="u",
                input_units="m s-1",
            ),
            "pressure": VariableSpecification(
                source_name="pressure",
                input_units="Pa",
                target_units="hPa",
            ),
        },
    )


def build_radiosonde_u_source_specification() -> SourceSpecification:
    """Build the source specification for the radiosonde wind test file.

    Returns
    -------
    SourceSpecification
        Semantic description of the radiosonde NetCDF file stored in
        `tests/datafiles/observado_radiosonda_u.nc`.
    """
    return SourceSpecification(
        label="RADIOSONDA",
        time_name="time",
        variables={
            "u_wind": VariableSpecification(
                source_name="u_wind",
                input_units="m s-1",
            ),
            "pressure": VariableSpecification(
                source_name="pres",
                input_units="hPa",
                target_units="Pa",
            ),
        },
    )


def build_ceilometro_source_specification() -> SourceSpecification:
    """Build the source specification for the ceilometer CSV test file.

    Returns
    -------
    SourceSpecification
        Semantic description of the ceilometer CSV file stored in
        `tests/datafiles/observado_ceilometro.csv`.
    """
    return SourceSpecification(
        label="CEILOMETRO",
        time_name="datetime",
        site_label="CEILOMETRO",
        site_latitude=-2.148667,
        site_longitude=-59.003317,
        variables={
            "hpbl": VariableSpecification(
                source_name="ablh",
                input_units="m",
            ),
        },
    )


def build_time_series_mynn_source_specification() -> SourceSpecification:
    """Build the MYNN MONAN source spec for surface time-series comparison."""
    return _build_time_series_monan_surface_source_specification(
        label="MYNN"
    )


def build_time_series_shoc_source_specification() -> SourceSpecification:
    """Build the SHOC MONAN source spec for surface time-series comparison."""
    return _build_time_series_monan_surface_source_specification(
        label="SHOC"
    )


def build_surface_flux_time_series_mynn_source_specification(
) -> SourceSpecification:
    """Build the MYNN MONAN source spec for surface-flux time series."""
    return _build_surface_flux_time_series_monan_source_specification(
        label="MYNN"
    )


def build_surface_flux_time_series_shoc_source_specification(
) -> SourceSpecification:
    """Build the SHOC MONAN source spec for surface-flux time series."""
    return _build_surface_flux_time_series_monan_source_specification(
        label="SHOC"
    )


def build_time_series_era5_source_specification() -> SourceSpecification:
    """Build the ERA5 source specification for surface time-series panels."""
    return SourceSpecification(
        label="ERA5",
        time_name="time",
        latitude_name="latitude",
        longitude_name="longitude",
        longitude_convention="-180_180",
        variables={
            "temperature_2m": VariableSpecification(
                source_name="t2m",
                input_units="K",
                target_units="degC",
            ),
            "dewpoint_temperature_2m": VariableSpecification(
                source_name="d2m",
                input_units="K",
                target_units="K",
            ),
            "surface_pressure": VariableSpecification(
                source_name="sp",
                input_units="Pa",
                target_units="Pa",
            ),
            "u_wind": VariableSpecification(
                source_name="u10",
                input_units="m s-1",
            ),
            "v_wind": VariableSpecification(
                source_name="v10",
                input_units="m s-1",
            ),
            "wind_speed_10m": VariableSpecification(
                derivation_kind="wind_speed_from_uv",
                target_units="m s-1",
            ),
            "specific_humidity_2m": VariableSpecification(
                derivation_kind=(
                    "specific_humidity_from_dewpoint_surface_pressure"
                ),
                target_units="g kg-1",
            ),
        },
    )


def build_surface_flux_time_series_era5_source_specification(
) -> SourceSpecification:
    """Build the ERA5 source specification for surface-flux time series."""
    return SourceSpecification(
        label="ERA5",
        time_name="time",
        latitude_name="latitude",
        longitude_name="longitude",
        longitude_convention="-180_180",
        variables={
            "accumulated_sensible_heat_flux": VariableSpecification(
                source_name="sshf",
                input_units="J m^-2",
            ),
            "accumulated_latent_heat_flux": VariableSpecification(
                source_name="slhf",
                input_units="J m^-2",
            ),
            "sensible_heat_flux": VariableSpecification(
                derivation_kind=(
                    "sensible_heat_flux_from_hourly_accumulated_energy"
                ),
                derivation_options={
                    "sign_multiplier": -1.0,
                    "long_name": "Sensible heat flux",
                },
            ),
            "latent_heat_flux": VariableSpecification(
                derivation_kind=(
                    "latent_heat_flux_from_hourly_accumulated_energy"
                ),
                derivation_options={
                    "sign_multiplier": -1.0,
                    "long_name": "Latent heat flux",
                },
            ),
        },
    )


def build_time_series_goamazon_surface_station_source_specification(
) -> SourceSpecification:
    """Build the GoAmazon surface-station source specification."""
    return SourceSpecification(
        label="Observation",
        time_name="time",
        latitude_name="lat",
        longitude_name="lon",
        variables={
            "temperature_2m": VariableSpecification(
                source_name="temp_mean",
                input_units="degC",
                target_units="degC",
            ),
            "rh": VariableSpecification(
                source_name="rh_mean",
                input_units="percent",
                target_units="percent",
            ),
            "surface_pressure": VariableSpecification(
                source_name="atmos_pressure",
                input_units="kPa",
                target_units="Pa",
            ),
            "specific_humidity_2m": VariableSpecification(
                derivation_kind=(
                    "specific_humidity_from_temperature_relative_humidity_surface_pressure"
                ),
                target_units="g kg-1",
            ),
            "wind_speed_10m": VariableSpecification(
                source_name="wspd_arith_mean",
                input_units="m s-1",
                target_units="m s-1",
            ),
        },
    )


def build_surface_flux_goamazon_eddy_correlation_source_specification(
) -> SourceSpecification:
    """Build the GoAmazon eddy-correlation flux source specification."""
    return SourceSpecification(
        label="Observation",
        time_name="time",
        site_latitude=-3.21297,
        site_longitude=-60.5981,
        variables={
            "sensible_heat_flux": VariableSpecification(
                source_name="h",
                input_units="W m^-2",
            ),
            "latent_heat_flux": VariableSpecification(
                source_name="lv_e",
                input_units="W m^-2",
            ),
        },
    )


def _build_legacy_monan_source_specification(
    *,
    label: str,
) -> SourceSpecification:
    """Build the shared MONAN source specification used by legacy recipes.

    Parameters
    ----------
    label:
        Human-readable label identifying the MONAN configuration.

    Returns
    -------
    SourceSpecification
        Semantic description of the raw MONAN legacy files.
    """
    return SourceSpecification(
        label=label,
        time_name="Time",
        vertical_name="level",
        latitude_name="latitude",
        longitude_name="longitude",
        longitude_convention="-180_180",
        variables={
            "qc": VariableSpecification(
                source_name="qc",
                input_units="kg kg-1",
            ),
            "qv": VariableSpecification(
                source_name="qv",
                input_units="kg kg-1",
            ),
            "qt": VariableSpecification(
                derivation_kind="qt_from_qc_qv",
                target_units="kg kg-1",
            ),
            "theta": VariableSpecification(
                source_name="theta",
                input_units="K",
            ),
            "tke_pbl": VariableSpecification(
                source_name="tke_pbl",
                input_units="m^2 s^-2",
            ),
            "hpbl": VariableSpecification(
                source_name="hpbl",
                input_units="m",
            ),
            "pressure": VariableSpecification(
                source_name="pressure",
                input_units="Pa",
                target_units="hPa",
            ),
            "u_wind": VariableSpecification(
                source_name="u",
                input_units="m s-1",
            ),
            "v_wind": VariableSpecification(
                source_name="v",
                input_units="m s-1",
            ),
            "wind_speed": VariableSpecification(
                derivation_kind="wind_speed_from_uv",
                target_units="m s-1",
            ),
            "sensible_heat_flux": VariableSpecification(
                source_name="hfx",
                input_units="W m^-2",
            ),
            "rainnc": VariableSpecification(
                source_name="rainnc",
                input_units="mm",
            ),
            "rainc": VariableSpecification(
                source_name="rainc",
                input_units="mm",
            ),
            "precipitation": VariableSpecification(
                derivation_kind="precipitation_from_rainc_rainnc",
                target_units="mm",
            ),
        },
    )


def _build_time_series_monan_surface_source_specification(
    *,
    label: str,
) -> SourceSpecification:
    """Build shared MONAN surface mappings for time-series comparison."""
    return SourceSpecification(
        label=label,
        time_name="Time",
        latitude_name="latitude",
        longitude_name="longitude",
        longitude_convention="-180_180",
        variables={
            "temperature_2m": VariableSpecification(
                source_name="t2m",
                input_units="K",
                target_units="degC",
            ),
            "specific_humidity_2m": VariableSpecification(
                source_name="q2",
                input_units="kg kg-1",
                target_units="g kg-1",
            ),
            "u_wind": VariableSpecification(
                source_name="u10",
                input_units="m s-1",
            ),
            "v_wind": VariableSpecification(
                source_name="v10",
                input_units="m s-1",
            ),
            "wind_speed_10m": VariableSpecification(
                derivation_kind="wind_speed_from_uv",
                target_units="m s-1",
            ),
        },
    )


def _build_surface_flux_time_series_monan_source_specification(
    *,
    label: str,
) -> SourceSpecification:
    """Build shared MONAN surface-flux mappings for time-series comparison."""
    return SourceSpecification(
        label=label,
        time_name="Time",
        latitude_name="latitude",
        longitude_name="longitude",
        longitude_convention="-180_180",
        variables={
            "sensible_heat_flux": VariableSpecification(
                source_name="hfx",
                input_units="W m^-2",
            ),
            "latent_heat_flux": VariableSpecification(
                source_name="lh",
                input_units="W m^-2",
            ),
        },
    )
