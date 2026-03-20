from __future__ import annotations

from plot_core.specifications import SourceSpecification, VariableSpecification


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
