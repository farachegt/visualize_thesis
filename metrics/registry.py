from __future__ import annotations

from dataclasses import dataclass

from plot_core.scenarios.paths import (
    TIME_SERIES_DEFAULT_INIT_DATE,
    TIME_SERIES_INIT_DATE_TO_MONAN_SEASON,
    TIME_SERIES_SUPPORTED_INIT_DATES,
    normalize_time_series_init_date,
)


METEOROLOGICAL_RECIPE_FAMILY = "meteorological_time_series"
HPBL_RECIPE_FAMILY = "hpbl_time_series"
SURFACE_FLUX_RECIPE_FAMILY = "surface_flux_time_series"
VERTICAL_PROFILE_METRIC_FAMILY = "vertical_profile"

REFERENCE_OBSERVATION = "Observation"
REFERENCE_ERA5 = "ERA5"

BASE_METRIC_NAMES = ("bias", "mae", "rmse", "corr")
PRECIPITATION_TOTAL_METRIC_NAMES = (
    "total_candidate",
    "total_reference",
    "total_bias",
    "relative_total_bias_percent",
)

VARIABLE_LABELS = {
    "temperature_2m": "2 m temperature",
    "specific_humidity_2m": "2 m specific humidity",
    "wind_speed_10m": "10 m wind speed",
    "precipitation": "Precipitation",
    "hpbl": "PBL height",
    "sensible_heat_flux": "Sensible heat flux",
    "latent_heat_flux": "Latent heat flux",
    "theta": "Potential temperature",
    "qv": "Specific humidity",
    "wind_speed": "Wind speed",
}

VARIABLE_UNITS = {
    "temperature_2m": "degC",
    "specific_humidity_2m": "g kg^-1",
    "wind_speed_10m": "m s^-1",
    "precipitation": "mm h^-1",
    "hpbl": "m",
    "sensible_heat_flux": "W m^-2",
    "latent_heat_flux": "W m^-2",
    "theta": "K",
    "qv": "g kg^-1",
    "wind_speed": "m s^-1",
}

RECIPE_FAMILY_VARIABLES = {
    METEOROLOGICAL_RECIPE_FAMILY: (
        "temperature_2m",
        "specific_humidity_2m",
        "wind_speed_10m",
        "precipitation",
    ),
    HPBL_RECIPE_FAMILY: ("hpbl",),
    SURFACE_FLUX_RECIPE_FAMILY: (
        "sensible_heat_flux",
        "latent_heat_flux",
    ),
    VERTICAL_PROFILE_METRIC_FAMILY: (
        "theta",
        "qv",
        "wind_speed",
    ),
}


@dataclass(frozen=True)
class CaseMetadata:
    """Case metadata derived from the supported init date."""

    init_date: str
    season_slug: str


def build_case_metadata(
    init_date: object = TIME_SERIES_DEFAULT_INIT_DATE,
) -> CaseMetadata:
    """Return canonical case metadata for a supported init date."""
    compact_date = normalize_time_series_init_date(init_date)
    return CaseMetadata(
        init_date=compact_date,
        season_slug=TIME_SERIES_INIT_DATE_TO_MONAN_SEASON[compact_date],
    )


def iter_recipe_variable_pairs() -> tuple[tuple[str, str], ...]:
    """Return v1 recipe-family/variable combinations in output order."""
    pairs: list[tuple[str, str]] = []
    for recipe_family in (
        METEOROLOGICAL_RECIPE_FAMILY,
        HPBL_RECIPE_FAMILY,
        SURFACE_FLUX_RECIPE_FAMILY,
    ):
        for variable_name in RECIPE_FAMILY_VARIABLES[recipe_family]:
            pairs.append((recipe_family, variable_name))
    return tuple(pairs)


def select_reference_source(
    *,
    recipe_family: str,
    variable_name: str,
    case: CaseMetadata,
) -> str:
    """Return the configured reference source for one variable/case."""
    if recipe_family == METEOROLOGICAL_RECIPE_FAMILY:
        if variable_name == "precipitation":
            return REFERENCE_ERA5
        return REFERENCE_OBSERVATION

    if recipe_family == HPBL_RECIPE_FAMILY:
        return REFERENCE_OBSERVATION

    if recipe_family == SURFACE_FLUX_RECIPE_FAMILY:
        if case.season_slug == "wet_season":
            return REFERENCE_ERA5
        return REFERENCE_OBSERVATION

    raise ValueError(
        f"Unsupported recipe family for reference selection: {recipe_family!r}."
    )


def select_candidate_sources(
    *,
    variable_name: str,
    reference_source: str,
    available_sources: tuple[str, ...],
) -> tuple[str, ...]:
    """Return ordered sources to compare against the selected reference."""
    available_monan_sources = tuple(
        source
        for source in ("SHOC", "MYNN", "SHOCMF", "MYNNMF")
        if source in available_sources
    )
    if variable_name == "precipitation":
        ordered_sources = available_monan_sources
    elif reference_source == REFERENCE_OBSERVATION:
        ordered_sources = (*available_monan_sources, "ERA5")
    else:
        ordered_sources = available_monan_sources

    available_set = set(available_sources)
    return tuple(
        source
        for source in ordered_sources
        if source in available_set and source != reference_source
    )


def build_reference_summary_lines(case: CaseMetadata) -> tuple[str, ...]:
    """Return summary lines that describe the active reference rules."""
    surface_flux_reference = select_reference_source(
        recipe_family=SURFACE_FLUX_RECIPE_FAMILY,
        variable_name="sensible_heat_flux",
        case=case,
    )

    flux_note = (
        "Observation"
        if surface_flux_reference == REFERENCE_OBSERVATION
        else "ERA5 for wet season"
    )

    return (
        "temperature_2m reference: Observation",
        "specific_humidity_2m reference: Observation",
        "wind_speed_10m reference: Observation",
        "precipitation reference: ERA5 (Observation unavailable)",
        "hpbl reference: Observation",
        f"surface flux reference: {flux_note}",
    )


def metric_units(
    *,
    variable_name: str,
    metric_name: str,
) -> str:
    """Return output units for one metric row in the long table."""
    if metric_name == "corr":
        return "1"
    if metric_name == "relative_total_bias_percent":
        return "%"
    if metric_name in {
        "total_candidate",
        "total_reference",
        "total_bias",
    }:
        return "mm"
    return VARIABLE_UNITS[variable_name]


__all__ = [
    "BASE_METRIC_NAMES",
    "CaseMetadata",
    "HPBL_RECIPE_FAMILY",
    "METEOROLOGICAL_RECIPE_FAMILY",
    "PRECIPITATION_TOTAL_METRIC_NAMES",
    "REFERENCE_ERA5",
    "REFERENCE_OBSERVATION",
    "RECIPE_FAMILY_VARIABLES",
    "SURFACE_FLUX_RECIPE_FAMILY",
    "TIME_SERIES_DEFAULT_INIT_DATE",
    "TIME_SERIES_SUPPORTED_INIT_DATES",
    "VARIABLE_LABELS",
    "VARIABLE_UNITS",
    "VERTICAL_PROFILE_METRIC_FAMILY",
    "build_case_metadata",
    "build_reference_summary_lines",
    "iter_recipe_variable_pairs",
    "metric_units",
    "select_candidate_sources",
    "select_reference_source",
]
