from __future__ import annotations

from plot_core.specifications import SourceSpecification, VariableSpecification


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
            "pressure": VariableSpecification(
                source_name="pressure",
                input_units="Pa",
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
        },
    )
