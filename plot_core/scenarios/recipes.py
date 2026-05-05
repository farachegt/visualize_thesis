from __future__ import annotations

from dataclasses import replace
from typing import Literal, Mapping, Sequence

import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.figure import Figure

from plot_core.adapter import DataAdapter
from plot_core.plot_data import (
    TimeSeriesBandPlotData,
    TimeSeriesPlotData,
    VerticalProfileBandPlotData,
    VerticalProfilePlotData,
)
from plot_core.recipes.cross_sections import (
    CrossSectionLayerInput,
    CrossSectionPanelInput,
    plot_cross_section_panels,
)
from plot_core.recipes.diurnal import (
    DiurnalAmplitudeRowInput,
    DiurnalAmplitudeSourceInput,
    DiurnalPeakPhaseRowInput,
    DiurnalPeakPhaseSourceInput,
    plot_diurnal_amplitude_rows,
    plot_diurnal_cycle_amplitude_pblh,
    plot_diurnal_peak_phase_pblh,
    plot_diurnal_peak_phase_rows,
)
from plot_core.recipes.diurnal_extrema_matrix import (
    DiurnalExtremaMatrixRowInput,
    DiurnalExtremaMatrixSourceInput,
    plot_diurnal_extrema_matrix_rows,
)
from plot_core.recipes.diurnal_matrix import (
    DiurnalAmplitudeMatrixRowInput,
    DiurnalAmplitudeMatrixSourceInput,
    plot_diurnal_amplitude_matrix_rows,
)
from plot_core.recipes.maps import (
    MapComparisonRowInput,
    MapComparisonSourceInput,
    MapLayerInput,
    MapPanelInput,
    plot_map_panels,
    plot_map_comparison_rows,
    plot_paper_grade_panel,
)
from plot_core.recipes.profiles import (
    PanelInput,
    PreparedVerticalProfileLayerInput,
    VerticalProfileCloudHatchInput,
    VerticalProfileLayerInput,
    VerticalProfileSourceInput,
    plot_vertical_profiles_panel_at_point,
    plot_vertical_profiles_panel,
)
from plot_core.recipes.time_series import (
    PreparedTimeSeriesLayerInput,
    TimeSeriesLayerInput,
    TimeSeriesPanelInput,
    plot_time_series_panels,
)
from plot_core.recipes.time_vertical import (
    HourlyMeanLayerInput,
    HourlyMeanPanelInput,
    plot_hourly_mean_panels,
)
from plot_core.rendering import (
    FigureSpecification,
    RenderSpecification,
    SharedColorbarSpecification,
)
from plot_core.requests import (
    HorizontalFieldRequest,
    TimeSeriesRequest,
    TimeVerticalSectionRequest,
    VerticalCrossSectionRequest,
    VerticalProfileRequest,
)

from .adapters import (
    build_surface_flux_goamazon_eddy_correlation_adapter,
    build_surface_flux_time_series_era5_adapter,
    build_surface_flux_time_series_mynn_adapter,
    build_surface_flux_time_series_shoc_adapter,
    build_goamazon_radiosonde_profile_adapter,
    build_legacy_e3sm_adapter,
    build_legacy_monan_e3sm_adapter,
    build_legacy_mynn_monan_adapter,
    build_legacy_shoc_monan_adapter,
    build_model_u_adapter,
    build_radiosonde_u_adapter,
    build_time_series_era5_adapter,
    build_time_series_goamazon_surface_station_adapter,
    build_time_series_mynn_adapter,
    build_time_series_shoc_adapter,
    build_vertical_profile_era5_adapter,
    build_vertical_profile_mynn_adapter,
    build_vertical_profile_shoc_adapter,
)
from .paths import (
    build_time_series_init_datetime_string,
    build_time_series_season_label,
    normalize_time_series_init_date,
)
from .requests import (
    TIME_SERIES_COMPARISON_DURATION_DAYS,
    TIME_SERIES_COMPARISON_INIT_DATE,
    build_time_series_comparison_gridded_request,
    build_time_series_comparison_station_request,
    build_legacy_chile_coast_vertical_profile_request,
    build_model_vertical_profile_request,
    build_radiosonde_vertical_profile_request,
    build_vertical_profile_comparison_gridded_request,
    build_vertical_profile_comparison_radiosonde_request,
    VERTICAL_PROFILE_COMPARISON_POINT_LAT,
    VERTICAL_PROFILE_COMPARISON_POINT_LON,
)

LEGACY_PROFILE_VARIABLE_NAMES = (
    "theta",
    "tke_pbl",
    "qt",
    "wind_speed",
)
LEGACY_PROFILE_PANEL_LABELS = (
    "Potential Temperature",
    "TKE",
    "Total Water Mixing Ratio",
    "Wind Speed",
)
LEGACY_PROFILE_X_UNITS = (
    "K",
    "m²/s²",
    "kg/kg",
    "m/s",
)
LEGACY_PROFILE_PRIMARY_LABEL = "MONAN - SHOC scheme"
LEGACY_PROFILE_SECONDARY_LABEL = "MONAN - MYNN scheme"
LEGACY_MONAN_E3SM_PROFILE_LABEL = "MONAN"
LEGACY_E3SM_PROFILE_LABEL = "E3SM"
LEGACY_MONAN_E3SM_PROFILE_TIME = np.datetime64("2014-02-24T00:00:00")
LEGACY_MONAN_E3SM_PROFILE_PRESSURE_BOTTOM_HPA = 1000.0
LEGACY_MONAN_E3SM_PROFILE_PRESSURE_TOP_HPA = 700.0
LEGACY_MONAN_E3SM_PROFILE_THETA_XLIM = (290.0, 320.0)
LEGACY_MONAN_E3SM_PROFILE_TKE_XLIM = (-0.01, 0.6)
LEGACY_MONAN_E3SM_PROFILE_QT_XLIM = (0.0, 0.018)
LEGACY_MONAN_E3SM_PROFILE_WIND_SPEED_XLIM = (0.0, 15.0)
LEGACY_HOURLY_MEAN_REGION_NAME = "Sahara Desert"
LEGACY_HOURLY_MEAN_POINT_LAT = 20.0
LEGACY_HOURLY_MEAN_POINT_LON = 0.0
LEGACY_HOURLY_MEAN_START_DATE = np.datetime64("2014-02-24T00:00:00")
LEGACY_HOURLY_MEAN_N_DAYS = 3
LEGACY_HOURLY_MEAN_HALF_BOX_DEG = 0.5
LEGACY_HOURLY_MEAN_TKE_VMIN = 0.0
LEGACY_HOURLY_MEAN_TKE_VMAX = 2.0
LEGACY_HOURLY_MEAN_QC_CONTOUR_MIN = 1e-5
LEGACY_HOURLY_MEAN_PRESSURE_TOP_HPA = 500.0
LEGACY_CROSS_SECTION_START_DATE = np.datetime64("2014-02-24T00:00")
LEGACY_CROSS_SECTION_END_DATE = np.datetime64("2014-02-27T00:00")
LEGACY_CROSS_SECTION_SPACING_KM = 30.0
LEGACY_CROSS_SECTION_START_LAT = -19.0
LEGACY_CROSS_SECTION_START_LON = -78.0
LEGACY_CROSS_SECTION_END_LAT = -29.0
LEGACY_CROSS_SECTION_END_LON = -73.0
LEGACY_CROSS_SECTION_MAIN_VARIABLE_NAME = "theta"
LEGACY_CROSS_SECTION_MAIN_FIELD_LABEL = "Potential Temperature"
LEGACY_CROSS_SECTION_MAIN_COLORBAR_LABEL = "Potential Temperature [K]"
LEGACY_CROSS_SECTION_FIELD_VMIN = 290.0
LEGACY_CROSS_SECTION_FIELD_VMAX = 350.0
LEGACY_CROSS_SECTION_PRESSURE_TOP_HPA = 600.0
LEGACY_CROSS_SECTION_QC_CONTOUR_MIN = 1e-5
LEGACY_SIDE_BY_SIDE_DATE = np.datetime64("2014-02-24T00:00")
LEGACY_SIDE_BY_SIDE_VARIABLE_NAME = "hpbl"
LEGACY_SIDE_BY_SIDE_FIELD_LABEL = "PBLH"
LEGACY_SIDE_BY_SIDE_COLORBAR_LABEL = (
    "Planetary Boundary Layer Height [m]"
)
LEGACY_SIDE_BY_SIDE_CMAP = "turbo"
LEGACY_SIDE_BY_SIDE_FIELD_VMIN = 0.0
LEGACY_SIDE_BY_SIDE_FIELD_VMAX = 3000.0
LEGACY_PAPER_GRADE_DATE = np.datetime64("2014-02-24T00:00")
LEGACY_PAPER_GRADE_VARIABLE_PAIRS = (
    ("hpbl", "hpbl"),
    ("sensible_heat_flux", "sensible_heat_flux"),
)
LEGACY_PAPER_GRADE_LABELS = ("PBL Height", "Sensible Heat Flux")
LEGACY_PAPER_GRADE_ABSOLUTE_COLORBAR_LABELS = (
    "PBLH [m]",
    "SHF [W/m^2]",
)
LEGACY_PAPER_GRADE_DIFFERENCE_COLORBAR_LABELS = (
    "Δ PBLH [m]",
    "Δ SHF [W m^-2]",
)
LEGACY_PAPER_GRADE_VMINS = (0.0, -100.0)
LEGACY_PAPER_GRADE_VMAXS = (3000.0, 500.0)
LEGACY_PAPER_GRADE_CMAPS_ABS = ("turbo", "Spectral_r")
LEGACY_PAPER_GRADE_CMAP_DIFF = "RdBu_r"
LEGACY_PAPER_GRADE_DIFF_LIMITS = (1500.0, 200.0)
LEGACY_DIURNAL_AMPLITUDE_START_DATE = np.datetime64("2014-02-24")
LEGACY_DIURNAL_AMPLITUDE_N_DAYS = 3
LEGACY_DIURNAL_AMPLITUDE_MONAN_VAR = "hpbl"
LEGACY_DIURNAL_AMPLITUDE_E3SM_VAR = "hpbl"
LEGACY_DIURNAL_AMPLITUDE_FIELD_LABEL = "Amplitude PBLH"
LEGACY_DIURNAL_AMPLITUDE_CMAP_ABS = "turbo"
LEGACY_DIURNAL_AMPLITUDE_CMAP_DIFF = "RdBu_r"
LEGACY_DIURNAL_AMPLITUDE_VMIN = 0.0
LEGACY_DIURNAL_AMPLITUDE_VMAX: float | None = 2500.0
LEGACY_DIURNAL_AMPLITUDE_DIFF_LIMIT: float | None = 1500.0
LEGACY_DIURNAL_AMPLITUDE_PANEL_VARIABLE_PAIRS = (
    ("hpbl", "hpbl"),
    ("sensible_heat_flux", "sensible_heat_flux"),
)
LEGACY_DIURNAL_AMPLITUDE_PANEL_ROW_LABELS = (
    "PBL Height",
    "Sensible Heat Flux",
)
LEGACY_DIURNAL_AMPLITUDE_PANEL_FIELD_LABELS = (
    "Amplitude PBLH",
    "Amplitude SHF",
)
LEGACY_DIURNAL_AMPLITUDE_PANEL_ABSOLUTE_COLORBAR_LABELS = (
    "Amplitude PBLH",
    "Amplitude SHF",
)
LEGACY_DIURNAL_AMPLITUDE_PANEL_DIFFERENCE_COLORBAR_LABELS = (
    "Δ Amplitude PBLH",
    "Δ Amplitude SHF",
)
LEGACY_DIURNAL_AMPLITUDE_PANEL_VMINS = (0.0, 0.0)
LEGACY_DIURNAL_AMPLITUDE_PANEL_VMAXS = (2500.0, 500.0)
LEGACY_DIURNAL_AMPLITUDE_PANEL_CMAPS_ABS = ("turbo", "Spectral_r")
LEGACY_DIURNAL_AMPLITUDE_PANEL_CMAP_DIFF = "RdBu_r"
LEGACY_DIURNAL_AMPLITUDE_PANEL_DIFF_LIMITS = (1500.0, 200.0)
LEGACY_DIURNAL_EXTREMA_VARIABLE_PAIRS = (
    ("hpbl", "hpbl"),
    ("sensible_heat_flux", "sensible_heat_flux"),
)
LEGACY_DIURNAL_EXTREMA_ROW_LABELS = (
    "PBL Height",
    "Sensible Heat Flux",
)
LEGACY_DIURNAL_EXTREMA_CMAPS_ABS = ("turbo", "Spectral_r")
LEGACY_DIURNAL_EXTREMA_CMAP_DIFF = "RdBu_r"
LEGACY_DIURNAL_EXTREMA_PBLH_MAX_VMIN = 0.0
LEGACY_DIURNAL_EXTREMA_PBLH_MAX_VMAX = 4000.0
LEGACY_DIURNAL_EXTREMA_PBLH_MIN_VMIN = 0.0
LEGACY_DIURNAL_EXTREMA_PBLH_MIN_VMAX = 2000.0
LEGACY_DIURNAL_EXTREMA_SHF_MIN_VMIN = -100.0
LEGACY_DIURNAL_EXTREMA_SHF_MIN_VMAX = 100.0
LEGACY_DIURNAL_EXTREMA_SHF_MAX_VMIN = 0.0
LEGACY_DIURNAL_EXTREMA_SHF_MAX_VMAX = 500.0
LEGACY_DIURNAL_EXTREMA_DIFF_MAX_LIMITS = (1500.0, 300.0)
LEGACY_DIURNAL_EXTREMA_DIFF_MIN_LIMITS = (600.0, 60.0)
LEGACY_DIURNAL_PHASE_START_DATE = np.datetime64("2014-02-24")
LEGACY_DIURNAL_PHASE_N_DAYS = 3
LEGACY_DIURNAL_PHASE_MONAN_VAR = "hpbl"
LEGACY_DIURNAL_PHASE_E3SM_VAR = "hpbl"
LEGACY_DIURNAL_PHASE_FIELD_LABEL = "Peak Hour PBLH"
LEGACY_DIURNAL_PHASE_CMAP_ABS = "twilight"
LEGACY_DIURNAL_PHASE_CMAP_DIFF = "RdBu_r"
LEGACY_DIURNAL_PHASE_VMIN = 0.0
LEGACY_DIURNAL_PHASE_VMAX = 23.0
LEGACY_DIURNAL_PHASE_DIFF_LIMIT = 12.0
LEGACY_DIURNAL_PHASE_MINIMUM_AMPLITUDE_FOR_PEAK_PHASE = 100.0
LEGACY_MONAN_PRECIPITATION_START_TIME = np.datetime64("2014-02-24T01:00")
LEGACY_MONAN_PRECIPITATION_END_TIME = np.datetime64("2014-02-27T00:00")
TimeSeriesComparisonMode = Literal["full", "hourly_mean"]
TIME_SERIES_COMPARISON_UTC_OFFSET_HOURS = -4
TIME_SERIES_COMPARISON_TICK_STEP_HOURS = 12
TIME_SERIES_COMPARISON_HOURLY_MEAN_TICK_STEP_HOURS = 3
TIME_SERIES_COMPARISON_SOURCE_STYLES = (
    ("SHOC", "blue"),
    ("MYNN", "orange"),
    ("ERA5", "gray"),
    ("Observation", "black"),
)
TIME_SERIES_COMPARISON_MONAN_SOURCE_LABELS = {"SHOC", "MYNN"}
TIME_SERIES_COMPARISON_STD_BAND_ALPHA = 0.18
TIME_SERIES_COMPARISON_PANELS = (
    ("temperature_2m", "2 m temperature [°C]"),
    ("specific_humidity_2m", "Specific humidity [g/kg]"),
    ("wind_speed_10m", "10 m wind speed [m/s]"),
)
TIME_SERIES_COMPARISON_Y_LIMITS = {
    "temperature_2m": (20.0, 35.0),
    "specific_humidity_2m": (14.0, 26.0),
    "wind_speed_10m": (0.0, 8.0),
}
SURFACE_FLUX_TIME_SERIES_COMPARISON_PANELS = (
    ("sensible_heat_flux", "Sensible heat flux [W/m²]"),
    ("latent_heat_flux", "Latent heat flux [W/m²]"),
)
SURFACE_FLUX_TIME_SERIES_NO_OBSERVATION_INIT_DATES = {"20140216"}
VERTICAL_PROFILE_COMPARISON_SOURCE_STYLES = (
    ("SHOC", "blue"),
    ("MYNN", "orange"),
    ("ERA5", "gray"),
    ("Observation", "black"),
)
VERTICAL_PROFILE_COMPARISON_PANELS = (
    ("theta", "Potential temperature", "K"),
    ("qv", "Specific humidity", "g/kg"),
    ("wind_speed", "Wind speed", "m/s"),
)
VERTICAL_PROFILE_COMPARISON_X_LIMITS = {
    "theta": (285.0, 320.0),
    "qv": (7.0, 20.0),
    "wind_speed": (0.0, 15.0),
}
VERTICAL_PROFILE_COMPARISON_SYNOPTIC_HOURS = (0, 6, 12, 18)
VERTICAL_PROFILE_COMPARISON_DISPLAY_ROW_ORDER = (1, 2, 3, 0)
VERTICAL_PROFILE_COMPARISON_PRESSURE_BOTTOM_HPA = 1000.0
VERTICAL_PROFILE_COMPARISON_PRESSURE_TOP_HPA = 700.0
VERTICAL_PROFILE_COMPARISON_PRESSURE_TICKS_HPA = np.arange(
    VERTICAL_PROFILE_COMPARISON_PRESSURE_TOP_HPA,
    VERTICAL_PROFILE_COMPARISON_PRESSURE_BOTTOM_HPA + 1.0,
    100.0,
)
VERTICAL_PROFILE_COMPARISON_UTC_OFFSET_HOURS = (
    TIME_SERIES_COMPARISON_UTC_OFFSET_HOURS
)
VERTICAL_PROFILE_STD_BAND_ALPHA = 0.18


# ============================================================================
# Public fixture builders
# ============================================================================

def build_vertical_profile_recipe_panel_input() -> PanelInput:
    """Build a complete panel input for the vertical-profile recipe.

    Returns
    -------
    PanelInput
        Panel input containing one model layer and one radiosonde layer for
        the `u_wind` variable.
    """
    model_adapter = build_model_u_adapter()
    radiosonde_adapter = build_radiosonde_u_adapter()

    return PanelInput(
        layers=[
            VerticalProfileLayerInput(
                adapter=model_adapter,
                request=build_model_vertical_profile_request(model_adapter),
                variable_name="u_wind",
                render_specification=RenderSpecification(
                    artist_method="plot",
                    artist_kwargs={
                        "color": "tab:blue",
                        "linewidth": 1.8,
                    },
                ),
                legend_label="MONAN",
            ),
            VerticalProfileLayerInput(
                adapter=radiosonde_adapter,
                request=build_radiosonde_vertical_profile_request(),
                variable_name="u_wind",
                render_specification=RenderSpecification(
                    artist_method="plot",
                    artist_kwargs={
                        "color": "black",
                        "linewidth": 1.2,
                    },
                ),
                legend_label="RADIOSONDA",
            ),
        ],
        axes_set_kwargs={
            "title": "U wind",
            "xlabel": "u (m s-1)",
            "ylabel": "Pressure (Pa)",
        },
        legend_kwargs={"loc": "best"},
        grid_kwargs={"visible": True, "alpha": 0.3},
    )


def build_vertical_profile_recipe_figure_specification(
    *,
    nrows: int = 1,
    ncols: int = 1,
) -> FigureSpecification:
    """Build the default figure specification for the recipe example.

    Parameters
    ----------
    nrows:
        Number of subplot rows.
    ncols:
        Number of subplot columns.

    Returns
    -------
    FigureSpecification
        Figure specification used by the example vertical-profile recipe.
    """
    return FigureSpecification(
        nrows=nrows,
        ncols=ncols,
        figure_kwargs={"figsize": (6, 8)},
    )


def build_vertical_profile_recipe_figure() -> Figure:
    """Execute the example vertical-profile recipe and return a figure.

    Returns
    -------
    Figure
        Figure built through the public recipe API using the test fixtures.
    """
    return plot_vertical_profiles_panel(
        panels=[build_vertical_profile_recipe_panel_input()],
        figure_specification=(
            build_vertical_profile_recipe_figure_specification()
        ),
    )


def build_legacy_vertical_profile_recipe_panels(
    *,
    primary_adapter: DataAdapter,
    primary_request: VerticalProfileRequest,
    secondary_adapter: DataAdapter,
    secondary_request: VerticalProfileRequest,
    primary_variable_names: Sequence[str] = LEGACY_PROFILE_VARIABLE_NAMES,
    secondary_variable_names: Sequence[str] | None = None,
) -> list[PanelInput]:
    """Build panel inputs using the metadata from the legacy `main()`.

    This fixture mirrors the old call in `visualizations.main()` for
    `plot_vertical_profiles_panel_at_point(...)`. It intentionally reuses the
    legacy variable names, panel labels, x-axis units, legend labels and 2x2
    layout assumptions, while leaving the adapters and requests external to
    the fixture.

    Parameters
    ----------
    primary_adapter:
        Adapter representing the first legacy source, originally SHOC MONAN.
    primary_request:
        Request applied to the first source.
    secondary_adapter:
        Adapter representing the second legacy source, originally MYNN MONAN.
    secondary_request:
        Request applied to the second source.
    primary_variable_names:
        Canonical variable names for the primary source.
    secondary_variable_names:
        Canonical variable names for the secondary source. When omitted, the
        same sequence used by the primary source is reused.

    Returns
    -------
    list[PanelInput]
        One panel per variable defined by the legacy profile comparison.

    Raises
    ------
    ValueError
        If the provided variable sequences do not match the legacy panel
        metadata length.
    """
    if secondary_variable_names is None:
        secondary_variable_names = primary_variable_names

    panel_count = len(LEGACY_PROFILE_PANEL_LABELS)
    if (
        len(primary_variable_names) != panel_count
        or len(secondary_variable_names) != panel_count
    ):
        raise ValueError(
            "Legacy vertical-profile recipe panels expect exactly four "
            "variables."
        )

    panel_inputs: list[PanelInput] = []
    for (
        primary_variable_name,
        secondary_variable_name,
        panel_label,
        x_unit,
    ) in zip(
        primary_variable_names,
        secondary_variable_names,
        LEGACY_PROFILE_PANEL_LABELS,
        LEGACY_PROFILE_X_UNITS,
    ):
        panel_inputs.append(
            PanelInput(
                layers=[
                    VerticalProfileLayerInput(
                        adapter=primary_adapter,
                        request=primary_request,
                        variable_name=primary_variable_name,
                        render_specification=RenderSpecification(
                            artist_method="plot",
                            artist_kwargs={
                                "color": "tab:blue",
                                "linewidth": 2.0,
                            },
                        ),
                        legend_label=LEGACY_PROFILE_PRIMARY_LABEL,
                    ),
                    VerticalProfileLayerInput(
                        adapter=secondary_adapter,
                        request=secondary_request,
                        variable_name=secondary_variable_name,
                        render_specification=RenderSpecification(
                            artist_method="plot",
                            artist_kwargs={
                                "color": "tab:orange",
                                "linewidth": 2.0,
                            },
                        ),
                        legend_label=LEGACY_PROFILE_SECONDARY_LABEL,
                    ),
                ],
                axes_set_kwargs={
                    "title": panel_label,
                    "xlabel": f"{panel_label} [{x_unit}]",
                    "ylabel": "Pressure [hPa]",
                },
                grid_kwargs={"visible": True, "alpha": 0.3},
                legend_kwargs={"loc": "best"},
            )
        )

    return panel_inputs


def build_legacy_vertical_profile_figure_specification(
) -> FigureSpecification:
    """Build the 2x2 figure layout used by the legacy profile comparison.

    Returns
    -------
    FigureSpecification
        Figure specification aligned with the old `plot_profiles.py`
        comparison layout.
    """
    return FigureSpecification(
        nrows=2,
        ncols=2,
        figure_kwargs={"figsize": (10.8, 10)},
    )


def build_legacy_main_vertical_profile_recipe_panels() -> list[PanelInput]:
    """Build legacy profile panels using the real SHOC and MYNN paths.

    Returns
    -------
    list[PanelInput]
        Four panel inputs mirroring the old `visualizations.main()` profile
        comparison over the Chilean coast.
    """
    shoc_adapter = build_legacy_shoc_monan_adapter()
    mynn_adapter = build_legacy_mynn_monan_adapter()
    request = build_legacy_chile_coast_vertical_profile_request()
    return build_legacy_vertical_profile_recipe_panels(
        primary_adapter=shoc_adapter,
        primary_request=request,
        secondary_adapter=mynn_adapter,
        secondary_request=request,
    )


def build_legacy_vertical_profiles_panel_at_point_figure(
    *,
    time_value: np.datetime64 = LEGACY_MONAN_E3SM_PROFILE_TIME,
    monan_adapter: DataAdapter | None = None,
    e3sm_adapter: DataAdapter | None = None,
) -> Figure:
    """Execute the legacy point-profile wrapper using MONAN and E3SM.

    Parameters
    ----------
    time_value:
        Requested time. The default matches the other MONAN/E3SM legacy
        fixtures already used in the project.
    monan_adapter:
        Optional adapter for the MONAN source. When omitted, the legacy
        MONAN adapter used in the MONAN/E3SM recipes is created.
    e3sm_adapter:
        Optional adapter for the E3SM source. When omitted, the legacy E3SM
        adapter is created.

    Returns
    -------
    Figure
        Figure produced by `plot_vertical_profiles_panel_at_point(...)`.
    """
    resolved_monan_adapter = (
        monan_adapter or build_legacy_monan_e3sm_adapter()
    )
    resolved_e3sm_adapter = e3sm_adapter or build_legacy_e3sm_adapter()
    request = build_legacy_chile_coast_vertical_profile_request(
        time_value=time_value,
    )
    return plot_vertical_profiles_panel_at_point(
        sources=[
            VerticalProfileSourceInput(
                adapter=resolved_monan_adapter,
                variable_names=LEGACY_PROFILE_VARIABLE_NAMES,
                legend_label=LEGACY_MONAN_E3SM_PROFILE_LABEL,
                render_specification=RenderSpecification(
                    artist_method="plot",
                    artist_kwargs={
                        "color": "tab:blue",
                        "linewidth": 2.0,
                    },
                ),
            ),
            VerticalProfileSourceInput(
                adapter=resolved_e3sm_adapter,
                variable_names=LEGACY_PROFILE_VARIABLE_NAMES,
                legend_label=LEGACY_E3SM_PROFILE_LABEL,
                render_specification=RenderSpecification(
                    artist_method="plot",
                    artist_kwargs={
                        "color": "tab:orange",
                        "linewidth": 2.0,
                    },
                ),
            ),
        ],
        point_lat=float(request.point_lat),
        point_lon=float(request.point_lon),
        time=request.times,
        panel_labels=LEGACY_PROFILE_PANEL_LABELS,
        x_units=LEGACY_PROFILE_X_UNITS,
        vertical_axis=request.vertical_axis,
        vertical_axis_label="Pressure [hPa]",
        panel_axes_set_kwargs=_build_legacy_profile_panel_axes_set_kwargs(),
        cloud_hatches=[
            VerticalProfileCloudHatchInput(
                adapter=resolved_monan_adapter,
                variable_name="qc",
                hatch="///",
                edgecolor="0.5",
                legend_label="Cloud layer (MONAN, qc > 1e-5)",
            ),
            VerticalProfileCloudHatchInput(
                adapter=resolved_e3sm_adapter,
                variable_name="qc",
                hatch="\\\\\\",
                edgecolor="0.3",
                legend_label="Cloud layer (E3SM, qc > 1e-5)",
            ),
        ],
        figure_specification=(
            _build_legacy_vertical_profiles_panel_at_point_figure_specification(
                time_value=time_value,
                point_lat=float(request.point_lat),
                point_lon=float(request.point_lon),
            )
        ),
    )


def build_legacy_monan_precipitation_figure(
    *,
    date: np.datetime64 = LEGACY_MONAN_PRECIPITATION_START_TIME,
    monan_adapter: DataAdapter | None = None,
) -> Figure:
    """Execute the legacy MONAN precipitation wrapper.

    Parameters
    ----------
    date:
        UTC instant represented by the hourly precipitation map.
    monan_adapter:
        Optional MONAN adapter. When omitted, the legacy MONAN adapter used
        in the MONAN/E3SM recipes is created.

    Returns
    -------
    Figure
        Figure produced by `plot_precipitation_monan(...)`.
    """
    resolved_monan_adapter = (
        monan_adapter or build_legacy_monan_e3sm_adapter()
    )
    return plot_precipitation_monan(
        monan_adapter=resolved_monan_adapter,
        date=date,
    )


def _build_legacy_vertical_profiles_panel_at_point_figure_specification(
    *,
    time_value: np.datetime64,
    point_lat: float,
    point_lon: float,
) -> FigureSpecification:
    """Build the official figure specification for the point-profile plot."""
    simulation_label = np.datetime_as_string(
        LEGACY_MONAN_E3SM_PROFILE_TIME,
        unit="m",
    )
    hindcast_label = np.datetime_as_string(time_value, unit="m")
    point_label = _format_latlon_label(point_lat, point_lon)
    return FigureSpecification(
        nrows=2,
        ncols=2,
        suptitle=(
            f"Initialization {simulation_label} - "
            f"Forecast {hindcast_label} "
            f"({point_label})"
        ),
        figure_kwargs={"figsize": (10.8, 10), "constrained_layout": True},
    )


def build_legacy_monan_e3sm_hourly_mean_inputs(
    *,
    region_name: str = LEGACY_HOURLY_MEAN_REGION_NAME,
    point_lat: float = LEGACY_HOURLY_MEAN_POINT_LAT,
    point_lon: float = LEGACY_HOURLY_MEAN_POINT_LON,
    start_date: np.datetime64 = LEGACY_HOURLY_MEAN_START_DATE,
    n_days: int = LEGACY_HOURLY_MEAN_N_DAYS,
    half_box_deg: float = LEGACY_HOURLY_MEAN_HALF_BOX_DEG,
    tke_vmin: float = LEGACY_HOURLY_MEAN_TKE_VMIN,
    tke_vmax: float = LEGACY_HOURLY_MEAN_TKE_VMAX,
    monan_adapter: DataAdapter | None = None,
    e3sm_adapter: DataAdapter | None = None,
) -> tuple[list[HourlyMeanPanelInput], FigureSpecification, float]:
    """Build the full input set for the generic MONAN/E3SM recipe.

    Parameters
    ----------
    region_name:
        Human-readable region name used in the figure title.
    point_lat:
        Region-centre latitude in degrees.
    point_lon:
        Region-centre longitude in degrees.
    start_date:
        Initial UTC instant of the requested time span.
    n_days:
        Number of days included in the request.
    half_box_deg:
        Half-size of the square bounding box in degrees.
    tke_vmin:
        Minimum color value used by the TKE shading.
    tke_vmax:
        Maximum color value used by the TKE shading.
    monan_adapter:
        Optional pre-built MONAN adapter reused across multiple calls.
    e3sm_adapter:
        Optional pre-built E3SM adapter reused across multiple calls.

    Returns
    -------
    tuple[list[HourlyMeanPanelInput], FigureSpecification, float]
        Tuple containing:
        - the panel list consumed by `plot_hourly_mean_panels(...)`;
        - the matching `FigureSpecification`;
        - the reference longitude used for local-hour conversion.
    """
    panels = _build_legacy_monan_e3sm_hourly_mean_panels(
        point_lat=point_lat,
        point_lon=point_lon,
        start_date=start_date,
        n_days=n_days,
        half_box_deg=half_box_deg,
        tke_vmin=tke_vmin,
        tke_vmax=tke_vmax,
        monan_adapter=monan_adapter,
        e3sm_adapter=e3sm_adapter,
    )
    _apply_common_hourly_mean_pressure_ylim(
        panels,
        panel_indices=[0, 1],
    )
    figure_specification = (
        _build_legacy_monan_e3sm_hourly_mean_figure_specification(
            region_name=region_name,
            point_lat=point_lat,
            point_lon=point_lon,
        )
    )
    return panels, figure_specification, point_lon


def build_legacy_monan_e3sm_hourly_mean_figure(
    *,
    region_name: str = LEGACY_HOURLY_MEAN_REGION_NAME,
    point_lat: float = LEGACY_HOURLY_MEAN_POINT_LAT,
    point_lon: float = LEGACY_HOURLY_MEAN_POINT_LON,
    start_date: np.datetime64 = LEGACY_HOURLY_MEAN_START_DATE,
    n_days: int = LEGACY_HOURLY_MEAN_N_DAYS,
    half_box_deg: float = LEGACY_HOURLY_MEAN_HALF_BOX_DEG,
    tke_vmin: float = LEGACY_HOURLY_MEAN_TKE_VMIN,
    tke_vmax: float = LEGACY_HOURLY_MEAN_TKE_VMAX,
    monan_adapter: DataAdapter | None = None,
    e3sm_adapter: DataAdapter | None = None,
) -> Figure:
    """Execute the generic MONAN/E3SM hourly-mean recipe example.

    Parameters
    ----------
    region_name:
        Human-readable region name used in panel titles.
    point_lat:
        Region-centre latitude in degrees.
    point_lon:
        Region-centre longitude in degrees.
    start_date:
        Initial UTC instant of the requested time span.
    n_days:
        Number of days included in the request.
    half_box_deg:
        Half-size of the square bounding box in degrees.
    tke_vmin:
        Minimum color value used by the TKE shading.
    tke_vmax:
        Maximum color value used by the TKE shading.
    monan_adapter:
        Optional pre-built MONAN adapter reused across multiple calls.
    e3sm_adapter:
        Optional pre-built E3SM adapter reused across multiple calls.

    Returns
    -------
    Figure
        Figure produced by the generic `plot_hourly_mean_panels(...)`
        recipe.
    """
    (
        panels,
        figure_specification,
        reference_longitude,
    ) = build_legacy_monan_e3sm_hourly_mean_inputs(
        region_name=region_name,
        point_lat=point_lat,
        point_lon=point_lon,
        start_date=start_date,
        n_days=n_days,
        half_box_deg=half_box_deg,
        tke_vmin=tke_vmin,
        tke_vmax=tke_vmax,
        monan_adapter=monan_adapter,
        e3sm_adapter=e3sm_adapter,
    )
    figure = plot_hourly_mean_panels(
        panels=panels,
        figure_specification=figure_specification,
        reference_longitude=reference_longitude,
    )
    _synchronize_panel_y_limits(
        figure=figure,
        panel_count=len(panels),
        panel_indices=[2, 3],
    )
    return figure


def build_legacy_monan_e3sm_hourly_mean_region_map_figure(
    *,
    region_coordinates: Mapping[str, tuple[float, float]],
) -> Figure:
    """Build a world reference map with markers for hourly-mean regions."""
    longitudes = np.asarray(
        [longitude for _, longitude in region_coordinates.values()],
        dtype=float,
    )
    latitudes = np.asarray(
        [latitude for latitude, _ in region_coordinates.values()],
        dtype=float,
    )
    figure = plt.figure(figsize=(12, 6), constrained_layout=True)
    axis = figure.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())
    axis.set_global()
    axis.set_title("Hourly Mean Regions")
    axis.coastlines(linewidth=0.8)
    axis.add_feature(cfeature.BORDERS, linewidth=0.5)
    gridliner = axis.gridlines(
        crs=ccrs.PlateCarree(),
        draw_labels=True,
        linewidth=0.6,
        alpha=0.3,
        x_inline=False,
        y_inline=False,
    )
    gridliner.top_labels = False
    gridliner.right_labels = False
    axis.scatter(
        longitudes,
        latitudes,
        transform=ccrs.PlateCarree(),
        marker="x",
        s=120.0,
        linewidths=2.5,
        color="crimson",
        zorder=6,
    )
    figure.suptitle("Hourly Mean Reference Regions")
    return figure


def build_legacy_monan_e3sm_cross_section_inputs(
    *,
    time: np.datetime64 = LEGACY_CROSS_SECTION_START_DATE,
    start_lat: float = LEGACY_CROSS_SECTION_START_LAT,
    start_lon: float = LEGACY_CROSS_SECTION_START_LON,
    end_lat: float = LEGACY_CROSS_SECTION_END_LAT,
    end_lon: float = LEGACY_CROSS_SECTION_END_LON,
    spacing_km: float = LEGACY_CROSS_SECTION_SPACING_KM,
    main_variable_name: str = LEGACY_CROSS_SECTION_MAIN_VARIABLE_NAME,
    main_field_label: str = LEGACY_CROSS_SECTION_MAIN_FIELD_LABEL,
    colorbar_label: str = LEGACY_CROSS_SECTION_MAIN_COLORBAR_LABEL,
    field_vmin: float | None = LEGACY_CROSS_SECTION_FIELD_VMIN,
    field_vmax: float | None = LEGACY_CROSS_SECTION_FIELD_VMAX,
    monan_adapter: DataAdapter | None = None,
    e3sm_adapter: DataAdapter | None = None,
) -> tuple[list[CrossSectionPanelInput], FigureSpecification]:
    """Build the full input set for the legacy MONAN/E3SM transect plot.

    Parameters
    ----------
    time:
        UTC instant represented by the cross section.
    start_lat:
        Starting latitude of the transect in degrees.
    start_lon:
        Starting longitude of the transect in degrees.
    end_lat:
        Ending latitude of the transect in degrees.
    end_lon:
        Ending longitude of the transect in degrees.
    spacing_km:
        Approximate spacing, in kilometres, between sampled transect
        points.
    main_variable_name:
        Canonical variable name used as the shaded field.
    main_field_label:
        Human-readable label used in the figure suptitle.
    colorbar_label:
        Label applied to the shared colorbar.
    field_vmin:
        Optional minimum color value used by the shaded field.
    field_vmax:
        Optional maximum color value used by the shaded field.
    monan_adapter:
        Optional pre-built MONAN adapter reused across multiple calls.
    e3sm_adapter:
        Optional pre-built E3SM adapter reused across multiple calls.

    Returns
    -------
    tuple[list[CrossSectionPanelInput], FigureSpecification]
        Tuple containing:
        - the panel list consumed by `plot_cross_section_panels(...)`;
        - the matching `FigureSpecification`.
    """
    panels = _build_legacy_monan_e3sm_cross_section_panels(
        time=time,
        start_lat=start_lat,
        start_lon=start_lon,
        end_lat=end_lat,
        end_lon=end_lon,
        spacing_km=spacing_km,
        main_variable_name=main_variable_name,
        field_vmin=field_vmin,
        field_vmax=field_vmax,
        monan_adapter=monan_adapter,
        e3sm_adapter=e3sm_adapter,
    )
    figure_specification = (
        _build_legacy_monan_e3sm_cross_section_figure_specification(
            time=time,
            start_lat=start_lat,
            start_lon=start_lon,
            end_lat=end_lat,
            end_lon=end_lon,
            main_variable_name=main_variable_name,
            main_field_label=main_field_label,
            colorbar_label=colorbar_label,
        )
    )
    return panels, figure_specification


def build_legacy_monan_e3sm_cross_section_figure(
    *,
    time: np.datetime64 = LEGACY_CROSS_SECTION_START_DATE,
    start_lat: float = LEGACY_CROSS_SECTION_START_LAT,
    start_lon: float = LEGACY_CROSS_SECTION_START_LON,
    end_lat: float = LEGACY_CROSS_SECTION_END_LAT,
    end_lon: float = LEGACY_CROSS_SECTION_END_LON,
    spacing_km: float = LEGACY_CROSS_SECTION_SPACING_KM,
    main_variable_name: str = LEGACY_CROSS_SECTION_MAIN_VARIABLE_NAME,
    main_field_label: str = LEGACY_CROSS_SECTION_MAIN_FIELD_LABEL,
    colorbar_label: str = LEGACY_CROSS_SECTION_MAIN_COLORBAR_LABEL,
    field_vmin: float | None = LEGACY_CROSS_SECTION_FIELD_VMIN,
    field_vmax: float | None = LEGACY_CROSS_SECTION_FIELD_VMAX,
    monan_adapter: DataAdapter | None = None,
    e3sm_adapter: DataAdapter | None = None,
) -> Figure:
    """Execute the legacy MONAN/E3SM transect recipe example.

    Parameters
    ----------
    time:
        UTC instant represented by the cross section.
    start_lat:
        Starting latitude of the transect in degrees.
    start_lon:
        Starting longitude of the transect in degrees.
    end_lat:
        Ending latitude of the transect in degrees.
    end_lon:
        Ending longitude of the transect in degrees.
    spacing_km:
        Approximate spacing, in kilometres, between sampled transect
        points.
    main_variable_name:
        Canonical variable name used as the shaded field.
    main_field_label:
        Human-readable label used in the figure suptitle.
    colorbar_label:
        Label applied to the shared colorbar.
    field_vmin:
        Optional minimum color value used by the shaded field.
    field_vmax:
        Optional maximum color value used by the shaded field.
    monan_adapter:
        Optional pre-built MONAN adapter reused across multiple calls.
    e3sm_adapter:
        Optional pre-built E3SM adapter reused across multiple calls.

    Returns
    -------
    Figure
        Figure produced by the generic `plot_cross_section_panels(...)`
        recipe.
    """
    panels, figure_specification = (
        build_legacy_monan_e3sm_cross_section_inputs(
            time=time,
            start_lat=start_lat,
            start_lon=start_lon,
            end_lat=end_lat,
            end_lon=end_lon,
            spacing_km=spacing_km,
            main_variable_name=main_variable_name,
            main_field_label=main_field_label,
            colorbar_label=colorbar_label,
            field_vmin=field_vmin,
            field_vmax=field_vmax,
            monan_adapter=monan_adapter,
            e3sm_adapter=e3sm_adapter,
        )
    )
    return plot_cross_section_panels(
        panels=panels,
        figure_specification=figure_specification,
        share_main_field_limits=(
            field_vmin is None or field_vmax is None
        ),
        synchronize_y_limits=True,
    )


def build_legacy_monan_e3sm_side_by_side_inputs(
    *,
    time: np.datetime64 = LEGACY_SIDE_BY_SIDE_DATE,
    variable_name: str = LEGACY_SIDE_BY_SIDE_VARIABLE_NAME,
    field_label: str = LEGACY_SIDE_BY_SIDE_FIELD_LABEL,
    colorbar_label: str = LEGACY_SIDE_BY_SIDE_COLORBAR_LABEL,
    cmap: str = LEGACY_SIDE_BY_SIDE_CMAP,
    field_vmin: float | None = LEGACY_SIDE_BY_SIDE_FIELD_VMIN,
    field_vmax: float | None = LEGACY_SIDE_BY_SIDE_FIELD_VMAX,
    monan_adapter: DataAdapter | None = None,
    e3sm_adapter: DataAdapter | None = None,
) -> tuple[list[MapPanelInput], FigureSpecification]:
    """Build the full input set for the legacy MONAN/E3SM map recipe.

    Parameters
    ----------
    time:
        UTC instant represented by the side-by-side comparison.
    variable_name:
        Canonical variable name used as the shaded field.
    field_label:
        Human-readable label used in panel titles.
    colorbar_label:
        Label applied to the shared colorbar.
    cmap:
        Colormap used by the absolute fields.
    field_vmin:
        Optional minimum color value used by the shaded field.
    field_vmax:
        Optional maximum color value used by the shaded field.
    monan_adapter:
        Optional pre-built MONAN adapter reused across multiple calls.
    e3sm_adapter:
        Optional pre-built E3SM adapter reused across multiple calls.

    Returns
    -------
    tuple[list[MapPanelInput], FigureSpecification]
        Tuple containing:
        - the panel list consumed by `plot_map_panels(...)`;
        - the matching `FigureSpecification`.
    """
    panels = _build_legacy_monan_e3sm_side_by_side_panels(
        time=time,
        variable_name=variable_name,
        cmap=cmap,
        field_vmin=field_vmin,
        field_vmax=field_vmax,
        monan_adapter=monan_adapter,
        e3sm_adapter=e3sm_adapter,
    )
    figure_specification = (
        _build_legacy_monan_e3sm_side_by_side_figure_specification(
            time=time,
            field_label=field_label,
            colorbar_label=colorbar_label,
        )
    )
    return panels, figure_specification


def build_legacy_monan_e3sm_side_by_side_figure(
    *,
    time: np.datetime64 = LEGACY_SIDE_BY_SIDE_DATE,
    variable_name: str = LEGACY_SIDE_BY_SIDE_VARIABLE_NAME,
    field_label: str = LEGACY_SIDE_BY_SIDE_FIELD_LABEL,
    colorbar_label: str = LEGACY_SIDE_BY_SIDE_COLORBAR_LABEL,
    cmap: str = LEGACY_SIDE_BY_SIDE_CMAP,
    field_vmin: float | None = LEGACY_SIDE_BY_SIDE_FIELD_VMIN,
    field_vmax: float | None = LEGACY_SIDE_BY_SIDE_FIELD_VMAX,
    monan_adapter: DataAdapter | None = None,
    e3sm_adapter: DataAdapter | None = None,
) -> Figure:
    """Execute the legacy MONAN/E3SM side-by-side map recipe example.

    Parameters
    ----------
    time:
        UTC instant represented by the side-by-side comparison.
    variable_name:
        Canonical variable name used as the shaded field.
    field_label:
        Human-readable label used in panel titles.
    colorbar_label:
        Label applied to the shared colorbar.
    cmap:
        Colormap used by the absolute fields.
    field_vmin:
        Optional minimum color value used by the shaded field.
    field_vmax:
        Optional maximum color value used by the shaded field.
    monan_adapter:
        Optional pre-built MONAN adapter reused across multiple calls.
    e3sm_adapter:
        Optional pre-built E3SM adapter reused across multiple calls.

    Returns
    -------
    Figure
        Figure produced by the generic `plot_map_panels(...)` recipe.
    """
    panels, figure_specification = (
        build_legacy_monan_e3sm_side_by_side_inputs(
            time=time,
            variable_name=variable_name,
            field_label=field_label,
            colorbar_label=colorbar_label,
            cmap=cmap,
            field_vmin=field_vmin,
            field_vmax=field_vmax,
            monan_adapter=monan_adapter,
            e3sm_adapter=e3sm_adapter,
        )
    )
    return plot_map_panels(
        panels=panels,
        figure_specification=figure_specification,
        share_main_field_limits=(field_vmin is None or field_vmax is None),
    )


def build_legacy_monan_e3sm_paper_grade_inputs(
    *,
    time: np.datetime64 = LEGACY_PAPER_GRADE_DATE,
    variable_pairs: Sequence[tuple[str, str]] = (
        LEGACY_PAPER_GRADE_VARIABLE_PAIRS
    ),
    labels: Sequence[str] = LEGACY_PAPER_GRADE_LABELS,
    vmins: Sequence[float] = LEGACY_PAPER_GRADE_VMINS,
    vmaxs: Sequence[float] = LEGACY_PAPER_GRADE_VMAXS,
    cmaps_abs: Sequence[str] = LEGACY_PAPER_GRADE_CMAPS_ABS,
    cmap_diff: str = LEGACY_PAPER_GRADE_CMAP_DIFF,
    diff_limits: Sequence[float | None] = LEGACY_PAPER_GRADE_DIFF_LIMITS,
    absolute_colorbar_labels: Sequence[str] = (
        LEGACY_PAPER_GRADE_ABSOLUTE_COLORBAR_LABELS
    ),
    difference_colorbar_labels: Sequence[str] = (
        LEGACY_PAPER_GRADE_DIFFERENCE_COLORBAR_LABELS
    ),
    monan_adapter: DataAdapter | None = None,
    e3sm_adapter: DataAdapter | None = None,
) -> tuple[list[MapComparisonRowInput], FigureSpecification]:
    """Build the full input set for the legacy paper-grade map recipe.

    Parameters
    ----------
    time:
        UTC instant represented by the panel.
    variable_pairs:
        Canonical variable pairs in `(monan_variable, e3sm_variable)` order,
        one pair per row.
    labels:
        Human-readable row labels.
    vmins:
        Minimum absolute-field limits, one per row.
    vmaxs:
        Maximum absolute-field limits, one per row.
    cmaps_abs:
        Colormaps used by the absolute fields, one per row.
    cmap_diff:
        Colormap used by every difference panel.
    diff_limits:
        Optional symmetric limits used by each difference panel.
    absolute_colorbar_labels:
        Labels used by the absolute-field colorbars, one per row.
    difference_colorbar_labels:
        Labels used by the difference colorbars, one per row.
    monan_adapter:
        Optional pre-built MONAN adapter reused across multiple calls.
    e3sm_adapter:
        Optional pre-built E3SM adapter reused across multiple calls.

    Returns
    -------
    tuple[list[MapComparisonRowInput], FigureSpecification]
        Tuple containing:
        - the comparison rows consumed by `plot_map_comparison_rows(...)`;
        - the matching `FigureSpecification`.

    Raises
    ------
    ValueError
        If the row-wise parameter sequences do not all have the same
        length.
    """
    rows = _build_legacy_monan_e3sm_paper_grade_rows(
        time=time,
        variable_pairs=variable_pairs,
        labels=labels,
        vmins=vmins,
        vmaxs=vmaxs,
        cmaps_abs=cmaps_abs,
        cmap_diff=cmap_diff,
        diff_limits=diff_limits,
        absolute_colorbar_labels=absolute_colorbar_labels,
        difference_colorbar_labels=difference_colorbar_labels,
        monan_adapter=monan_adapter,
        e3sm_adapter=e3sm_adapter,
    )
    figure_specification = (
        _build_legacy_monan_e3sm_paper_grade_figure_specification(
            time=time,
            row_count=len(rows),
        )
    )
    return rows, figure_specification


def build_legacy_monan_e3sm_paper_grade_figure(
    *,
    time: np.datetime64 = LEGACY_PAPER_GRADE_DATE,
    variable_pairs: Sequence[tuple[str, str]] = (
        LEGACY_PAPER_GRADE_VARIABLE_PAIRS
    ),
    labels: Sequence[str] = LEGACY_PAPER_GRADE_LABELS,
    vmins: Sequence[float] = LEGACY_PAPER_GRADE_VMINS,
    vmaxs: Sequence[float] = LEGACY_PAPER_GRADE_VMAXS,
    cmaps_abs: Sequence[str] = LEGACY_PAPER_GRADE_CMAPS_ABS,
    cmap_diff: str = LEGACY_PAPER_GRADE_CMAP_DIFF,
    diff_limits: Sequence[float | None] = LEGACY_PAPER_GRADE_DIFF_LIMITS,
    absolute_colorbar_labels: Sequence[str] = (
        LEGACY_PAPER_GRADE_ABSOLUTE_COLORBAR_LABELS
    ),
    difference_colorbar_labels: Sequence[str] = (
        LEGACY_PAPER_GRADE_DIFFERENCE_COLORBAR_LABELS
    ),
    monan_adapter: DataAdapter | None = None,
    e3sm_adapter: DataAdapter | None = None,
) -> Figure:
    """Execute the legacy MONAN/E3SM paper-grade recipe example.

    Parameters
    ----------
    time:
        UTC instant represented by the panel.
    variable_pairs:
        Canonical variable pairs in `(monan_variable, e3sm_variable)` order,
        one pair per row.
    labels:
        Human-readable row labels.
    vmins:
        Minimum absolute-field limits, one per row.
    vmaxs:
        Maximum absolute-field limits, one per row.
    cmaps_abs:
        Colormaps used by the absolute fields, one per row.
    cmap_diff:
        Colormap used by every difference panel.
    diff_limits:
        Optional symmetric limits used by each difference panel.
    absolute_colorbar_labels:
        Labels used by the absolute-field colorbars, one per row.
    difference_colorbar_labels:
        Labels used by the difference colorbars, one per row.
    monan_adapter:
        Optional pre-built MONAN adapter reused across multiple calls.
    e3sm_adapter:
        Optional pre-built E3SM adapter reused across multiple calls.

    Returns
    -------
    Figure
        Figure produced by the legacy `plot_paper_grade_panel(...)`
        wrapper.

    Raises
    ------
    ValueError
        If the row-wise parameter sequences do not all have the same
        length.
    """
    return plot_paper_grade_panel(
        monan_adapter=(
            monan_adapter or build_legacy_monan_e3sm_adapter()
        ),
        e3sm_adapter=e3sm_adapter or build_legacy_e3sm_adapter(),
        date=time,
        variable_pairs=variable_pairs,
        labels=labels,
        vmins=vmins,
        vmaxs=vmaxs,
        cmaps_abs=cmaps_abs,
        cmap_diff=cmap_diff,
        diff_limits=diff_limits,
        absolute_colorbar_labels=absolute_colorbar_labels,
        difference_colorbar_labels=difference_colorbar_labels,
    )


def build_legacy_monan_e3sm_diurnal_amplitude_inputs(
    *,
    day_start: np.datetime64 = LEGACY_DIURNAL_AMPLITUDE_START_DATE,
    monan_var: str = LEGACY_DIURNAL_AMPLITUDE_MONAN_VAR,
    e3sm_var: str = LEGACY_DIURNAL_AMPLITUDE_E3SM_VAR,
    field_label: str = LEGACY_DIURNAL_AMPLITUDE_FIELD_LABEL,
    cmap_abs: str = LEGACY_DIURNAL_AMPLITUDE_CMAP_ABS,
    cmap_diff: str = LEGACY_DIURNAL_AMPLITUDE_CMAP_DIFF,
    vmin: float = LEGACY_DIURNAL_AMPLITUDE_VMIN,
    vmax: float | None = LEGACY_DIURNAL_AMPLITUDE_VMAX,
    diff_limit: float | None = LEGACY_DIURNAL_AMPLITUDE_DIFF_LIMIT,
    monan_adapter: DataAdapter | None = None,
    e3sm_adapter: DataAdapter | None = None,
) -> tuple[list[DiurnalAmplitudeRowInput], FigureSpecification]:
    """Build the full input set for the legacy diurnal-amplitude recipe.

    Parameters
    ----------
    day_start:
        First instant of the day represented by the figure.
    monan_var:
        Canonical variable name used by the MONAN source.
    e3sm_var:
        Canonical variable name used by the E3SM source.
    field_label:
        Human-readable label used in panel titles and colorbars.
    cmap_abs:
        Colormap used by the absolute fields.
    cmap_diff:
        Colormap used by the difference field.
    vmin:
        Minimum color value used by the absolute fields.
    vmax:
        Optional maximum color value used by the absolute fields.
    diff_limit:
        Optional symmetric difference limit.
    monan_adapter:
        Optional pre-built MONAN adapter reused across multiple calls.
    e3sm_adapter:
        Optional pre-built E3SM adapter reused across multiple calls.

    Returns
    -------
    tuple[list[DiurnalAmplitudeRowInput], FigureSpecification]
        Tuple containing:
        - the comparison rows consumed by
          `plot_diurnal_amplitude_rows(...)`;
        - the matching `FigureSpecification`.
    """
    rows = _build_legacy_monan_e3sm_diurnal_amplitude_rows(
        day_start=day_start,
        monan_var=monan_var,
        e3sm_var=e3sm_var,
        field_label=field_label,
        cmap_abs=cmap_abs,
        cmap_diff=cmap_diff,
        vmin=vmin,
        vmax=vmax,
        diff_limit=diff_limit,
        monan_adapter=monan_adapter,
        e3sm_adapter=e3sm_adapter,
    )
    figure_specification = (
        _build_legacy_monan_e3sm_diurnal_amplitude_figure_specification(
            day_start=day_start,
        )
    )
    return rows, figure_specification


def build_legacy_monan_e3sm_diurnal_amplitude_figure(
    *,
    day_start: np.datetime64 = LEGACY_DIURNAL_AMPLITUDE_START_DATE,
    monan_var: str = LEGACY_DIURNAL_AMPLITUDE_MONAN_VAR,
    e3sm_var: str = LEGACY_DIURNAL_AMPLITUDE_E3SM_VAR,
    cmap_abs: str = LEGACY_DIURNAL_AMPLITUDE_CMAP_ABS,
    cmap_diff: str = LEGACY_DIURNAL_AMPLITUDE_CMAP_DIFF,
    vmin: float = LEGACY_DIURNAL_AMPLITUDE_VMIN,
    vmax: float | None = LEGACY_DIURNAL_AMPLITUDE_VMAX,
    diff_limit: float | None = LEGACY_DIURNAL_AMPLITUDE_DIFF_LIMIT,
    monan_adapter: DataAdapter | None = None,
    e3sm_adapter: DataAdapter | None = None,
) -> Figure:
    """Execute the legacy MONAN/E3SM diurnal-amplitude recipe example.

    Parameters
    ----------
    day_start:
        First instant of the day represented by the figure.
    monan_var:
        Canonical variable name used by the MONAN source.
    e3sm_var:
        Canonical variable name used by the E3SM source.
    cmap_abs:
        Colormap used by the absolute fields.
    cmap_diff:
        Colormap used by the difference field.
    vmin:
        Minimum color value used by the absolute fields.
    vmax:
        Optional maximum color value used by the absolute fields.
    diff_limit:
        Optional symmetric difference limit.
    monan_adapter:
        Optional pre-built MONAN adapter reused across multiple calls.
    e3sm_adapter:
        Optional pre-built E3SM adapter reused across multiple calls.

    Returns
    -------
    Figure
        Figure produced by the legacy
        `plot_diurnal_cycle_amplitude_pblh(...)` wrapper.
    """
    return plot_diurnal_cycle_amplitude_pblh(
        monan_adapter=(
            monan_adapter or build_legacy_monan_e3sm_adapter()
        ),
        e3sm_adapter=e3sm_adapter or build_legacy_e3sm_adapter(),
        day_start=day_start,
        monan_var=monan_var,
        e3sm_var=e3sm_var,
        cmap_abs=cmap_abs,
        cmap_diff=cmap_diff,
        vmin=vmin,
        vmax=vmax,
        diff_limit=diff_limit,
    )


def build_legacy_monan_e3sm_diurnal_amplitude_panel_inputs(
    *,
    day_start: np.datetime64 = LEGACY_DIURNAL_AMPLITUDE_START_DATE,
    variable_pairs: Sequence[tuple[str, str]] = (
        LEGACY_DIURNAL_AMPLITUDE_PANEL_VARIABLE_PAIRS
    ),
    row_labels: Sequence[str] = (
        LEGACY_DIURNAL_AMPLITUDE_PANEL_ROW_LABELS
    ),
    field_labels: Sequence[str] = (
        LEGACY_DIURNAL_AMPLITUDE_PANEL_FIELD_LABELS
    ),
    vmins: Sequence[float] = LEGACY_DIURNAL_AMPLITUDE_PANEL_VMINS,
    vmaxs: Sequence[float | None] = LEGACY_DIURNAL_AMPLITUDE_PANEL_VMAXS,
    cmaps_abs: Sequence[str] = (
        LEGACY_DIURNAL_AMPLITUDE_PANEL_CMAPS_ABS
    ),
    cmap_diff: str = LEGACY_DIURNAL_AMPLITUDE_PANEL_CMAP_DIFF,
    diff_limits: Sequence[float | None] = (
        LEGACY_DIURNAL_AMPLITUDE_PANEL_DIFF_LIMITS
    ),
    absolute_colorbar_labels: Sequence[str] = (
        LEGACY_DIURNAL_AMPLITUDE_PANEL_ABSOLUTE_COLORBAR_LABELS
    ),
    difference_colorbar_labels: Sequence[str] = (
        LEGACY_DIURNAL_AMPLITUDE_PANEL_DIFFERENCE_COLORBAR_LABELS
    ),
    monan_adapter: DataAdapter | None = None,
    e3sm_adapter: DataAdapter | None = None,
) -> tuple[list[DiurnalAmplitudeMatrixRowInput], FigureSpecification]:
    """Build the full input set for the legacy diurnal-amplitude panel."""
    rows = _build_legacy_monan_e3sm_diurnal_amplitude_panel_rows(
        day_start=day_start,
        variable_pairs=variable_pairs,
        row_labels=row_labels,
        field_labels=field_labels,
        vmins=vmins,
        vmaxs=vmaxs,
        cmaps_abs=cmaps_abs,
        cmap_diff=cmap_diff,
        diff_limits=diff_limits,
        absolute_colorbar_labels=absolute_colorbar_labels,
        difference_colorbar_labels=difference_colorbar_labels,
        monan_adapter=monan_adapter,
        e3sm_adapter=e3sm_adapter,
    )
    figure_specification = (
        _build_legacy_monan_e3sm_diurnal_amplitude_panel_figure_specification(
            day_start=day_start,
            row_count=len(variable_pairs),
        )
    )
    return rows, figure_specification


def build_legacy_monan_e3sm_diurnal_amplitude_panel_figure(
    *,
    day_start: np.datetime64 = LEGACY_DIURNAL_AMPLITUDE_START_DATE,
    variable_pairs: Sequence[tuple[str, str]] = (
        LEGACY_DIURNAL_AMPLITUDE_PANEL_VARIABLE_PAIRS
    ),
    row_labels: Sequence[str] = (
        LEGACY_DIURNAL_AMPLITUDE_PANEL_ROW_LABELS
    ),
    field_labels: Sequence[str] = (
        LEGACY_DIURNAL_AMPLITUDE_PANEL_FIELD_LABELS
    ),
    vmins: Sequence[float] = LEGACY_DIURNAL_AMPLITUDE_PANEL_VMINS,
    vmaxs: Sequence[float | None] = LEGACY_DIURNAL_AMPLITUDE_PANEL_VMAXS,
    cmaps_abs: Sequence[str] = (
        LEGACY_DIURNAL_AMPLITUDE_PANEL_CMAPS_ABS
    ),
    cmap_diff: str = LEGACY_DIURNAL_AMPLITUDE_PANEL_CMAP_DIFF,
    diff_limits: Sequence[float | None] = (
        LEGACY_DIURNAL_AMPLITUDE_PANEL_DIFF_LIMITS
    ),
    absolute_colorbar_labels: Sequence[str] = (
        LEGACY_DIURNAL_AMPLITUDE_PANEL_ABSOLUTE_COLORBAR_LABELS
    ),
    difference_colorbar_labels: Sequence[str] = (
        LEGACY_DIURNAL_AMPLITUDE_PANEL_DIFFERENCE_COLORBAR_LABELS
    ),
    monan_adapter: DataAdapter | None = None,
    e3sm_adapter: DataAdapter | None = None,
) -> Figure:
    """Execute the legacy MONAN/E3SM diurnal-amplitude panel recipe."""
    rows, figure_specification = (
        build_legacy_monan_e3sm_diurnal_amplitude_panel_inputs(
            day_start=day_start,
            variable_pairs=variable_pairs,
            row_labels=row_labels,
            field_labels=field_labels,
            vmins=vmins,
            vmaxs=vmaxs,
            cmaps_abs=cmaps_abs,
            cmap_diff=cmap_diff,
            diff_limits=diff_limits,
            absolute_colorbar_labels=absolute_colorbar_labels,
            difference_colorbar_labels=difference_colorbar_labels,
            monan_adapter=monan_adapter,
            e3sm_adapter=e3sm_adapter,
        )
    )
    return plot_diurnal_amplitude_matrix_rows(
        rows=rows,
        figure_specification=figure_specification,
    )


def build_monan_e3sm_diurnal_extrema_panel_inputs(
    *,
    day_start: np.datetime64 = LEGACY_DIURNAL_AMPLITUDE_START_DATE,
    time_reduce: str = "min",
    variable_pairs: Sequence[tuple[str, str]] = (
        LEGACY_DIURNAL_EXTREMA_VARIABLE_PAIRS
    ),
    row_labels: Sequence[str] = LEGACY_DIURNAL_EXTREMA_ROW_LABELS,
    cmaps_abs: Sequence[str] = LEGACY_DIURNAL_EXTREMA_CMAPS_ABS,
    cmap_diff: str = LEGACY_DIURNAL_EXTREMA_CMAP_DIFF,
    diff_limits: Sequence[float | None] = (
        LEGACY_DIURNAL_EXTREMA_DIFF_MIN_LIMITS
    ),
    monan_adapter: DataAdapter | None = None,
    e3sm_adapter: DataAdapter | None = None,
) -> tuple[list[DiurnalExtremaMatrixRowInput], FigureSpecification]:
    """Build the full input set for the official extrema panel recipe."""
    (
        field_labels,
        absolute_colorbar_labels,
        difference_colorbar_labels,
        vmins,
        vmaxs,
    ) = _build_diurnal_extrema_defaults(time_reduce)
    rows = _build_monan_e3sm_diurnal_extrema_panel_rows(
        day_start=day_start,
        time_reduce=time_reduce,
        variable_pairs=variable_pairs,
        row_labels=row_labels,
        field_labels=field_labels,
        vmins=vmins,
        vmaxs=vmaxs,
        cmaps_abs=cmaps_abs,
        cmap_diff=cmap_diff,
        diff_limits=diff_limits,
        absolute_colorbar_labels=absolute_colorbar_labels,
        difference_colorbar_labels=difference_colorbar_labels,
        monan_adapter=monan_adapter,
        e3sm_adapter=e3sm_adapter,
    )
    figure_specification = (
        _build_monan_e3sm_diurnal_extrema_panel_figure_specification(
            day_start=day_start,
            time_reduce=time_reduce,
            row_count=len(variable_pairs),
        )
    )
    return rows, figure_specification


def build_monan_e3sm_diurnal_extrema_panel_figure(
    *,
    day_start: np.datetime64 = LEGACY_DIURNAL_AMPLITUDE_START_DATE,
    time_reduce: str = "min",
    variable_pairs: Sequence[tuple[str, str]] = (
        LEGACY_DIURNAL_EXTREMA_VARIABLE_PAIRS
    ),
    row_labels: Sequence[str] = LEGACY_DIURNAL_EXTREMA_ROW_LABELS,
    cmaps_abs: Sequence[str] = LEGACY_DIURNAL_EXTREMA_CMAPS_ABS,
    cmap_diff: str = LEGACY_DIURNAL_EXTREMA_CMAP_DIFF,
    diff_limits: Sequence[float | None] = (
        LEGACY_DIURNAL_EXTREMA_DIFF_MIN_LIMITS
    ),
    monan_adapter: DataAdapter | None = None,
    e3sm_adapter: DataAdapter | None = None,
) -> Figure:
    """Execute the MONAN/E3SM extrema panel recipe."""
    if time_reduce == "min":
        diff_limits = LEGACY_DIURNAL_EXTREMA_DIFF_MIN_LIMITS
    else:
        diff_limits = LEGACY_DIURNAL_EXTREMA_DIFF_MAX_LIMITS

    rows, figure_specification = (
        build_monan_e3sm_diurnal_extrema_panel_inputs(
            day_start=day_start,
            time_reduce=time_reduce,
            variable_pairs=variable_pairs,
            row_labels=row_labels,
            cmaps_abs=cmaps_abs,
            cmap_diff=cmap_diff,
            diff_limits=diff_limits,
            monan_adapter=monan_adapter,
            e3sm_adapter=e3sm_adapter,
        )
    )
    return plot_diurnal_extrema_matrix_rows(
        rows=rows,
        figure_specification=figure_specification,
    )


def build_legacy_monan_e3sm_diurnal_peak_phase_inputs(
    *,
    day_start: np.datetime64 = LEGACY_DIURNAL_PHASE_START_DATE,
    monan_var: str = LEGACY_DIURNAL_PHASE_MONAN_VAR,
    e3sm_var: str = LEGACY_DIURNAL_PHASE_E3SM_VAR,
    field_label: str = LEGACY_DIURNAL_PHASE_FIELD_LABEL,
    cmap_phase: str = LEGACY_DIURNAL_PHASE_CMAP_ABS,
    cmap_diff: str = LEGACY_DIURNAL_PHASE_CMAP_DIFF,
    phase_vmin: float = LEGACY_DIURNAL_PHASE_VMIN,
    phase_vmax: float = LEGACY_DIURNAL_PHASE_VMAX,
    diff_limit: float = LEGACY_DIURNAL_PHASE_DIFF_LIMIT,
    minimum_amplitude_for_peak_phase: float | None = (
        LEGACY_DIURNAL_PHASE_MINIMUM_AMPLITUDE_FOR_PEAK_PHASE
    ),
    monan_adapter: DataAdapter | None = None,
    e3sm_adapter: DataAdapter | None = None,
) -> tuple[list[DiurnalPeakPhaseRowInput], FigureSpecification]:
    """Build the full input set for the legacy diurnal peak-phase recipe.

    Parameters
    ----------
    day_start:
        First instant of the day represented by the figure.
    monan_var:
        Canonical variable name used by the MONAN source.
    e3sm_var:
        Canonical variable name used by the E3SM source.
    field_label:
        Human-readable label used in panel titles and colorbars.
    cmap_phase:
        Colormap used by the absolute phase fields.
    cmap_diff:
        Colormap used by the difference field.
    phase_vmin:
        Minimum color value used by the absolute phase fields.
    phase_vmax:
        Maximum color value used by the absolute phase fields.
    diff_limit:
        Symmetric difference limit centred on zero.
    minimum_amplitude_for_peak_phase:
        Optional minimum daily PBLH amplitude required to keep one grid
        point in the phase maps. Pass `None` to disable the filter.
    monan_adapter:
        Optional pre-built MONAN adapter reused across multiple calls.
    e3sm_adapter:
        Optional pre-built E3SM adapter reused across multiple calls.

    Returns
    -------
    tuple[list[DiurnalPeakPhaseRowInput], FigureSpecification]
        Tuple containing:
        - the comparison rows consumed by
          `plot_diurnal_peak_phase_rows(...)`;
        - the matching `FigureSpecification`.
    """
    rows = _build_legacy_monan_e3sm_diurnal_peak_phase_rows(
        day_start=day_start,
        monan_var=monan_var,
        e3sm_var=e3sm_var,
        field_label=field_label,
        cmap_phase=cmap_phase,
        cmap_diff=cmap_diff,
        phase_vmin=phase_vmin,
        phase_vmax=phase_vmax,
        diff_limit=diff_limit,
        minimum_amplitude_for_peak_phase=(
            minimum_amplitude_for_peak_phase
        ),
        monan_adapter=monan_adapter,
        e3sm_adapter=e3sm_adapter,
    )
    figure_specification = (
        _build_legacy_monan_e3sm_diurnal_peak_phase_figure_specification(
            day_start=day_start,
        )
    )
    return rows, figure_specification


def build_legacy_monan_e3sm_diurnal_peak_phase_figure(
    *,
    day_start: np.datetime64 = LEGACY_DIURNAL_PHASE_START_DATE,
    monan_var: str = LEGACY_DIURNAL_PHASE_MONAN_VAR,
    e3sm_var: str = LEGACY_DIURNAL_PHASE_E3SM_VAR,
    cmap_phase: str = LEGACY_DIURNAL_PHASE_CMAP_ABS,
    cmap_diff: str = LEGACY_DIURNAL_PHASE_CMAP_DIFF,
    phase_vmin: float = LEGACY_DIURNAL_PHASE_VMIN,
    phase_vmax: float = LEGACY_DIURNAL_PHASE_VMAX,
    diff_limit: float = LEGACY_DIURNAL_PHASE_DIFF_LIMIT,
    minimum_amplitude_for_peak_phase: float | None = (
        LEGACY_DIURNAL_PHASE_MINIMUM_AMPLITUDE_FOR_PEAK_PHASE
    ),
    monan_adapter: DataAdapter | None = None,
    e3sm_adapter: DataAdapter | None = None,
) -> Figure:
    """Execute the legacy MONAN/E3SM diurnal peak-phase recipe example.

    Parameters
    ----------
    day_start:
        First instant of the day represented by the figure.
    monan_var:
        Canonical variable name used by the MONAN source.
    e3sm_var:
        Canonical variable name used by the E3SM source.
    cmap_phase:
        Colormap used by the absolute phase fields.
    cmap_diff:
        Colormap used by the difference field.
    phase_vmin:
        Minimum color value used by the absolute phase fields.
    phase_vmax:
        Maximum color value used by the absolute phase fields.
    diff_limit:
        Symmetric difference limit centred on zero.
    minimum_amplitude_for_peak_phase:
        Optional minimum daily PBLH amplitude required to keep one grid
        point in the phase maps. Pass `None` to disable the filter.
    monan_adapter:
        Optional pre-built MONAN adapter reused across multiple calls.
    e3sm_adapter:
        Optional pre-built E3SM adapter reused across multiple calls.

    Returns
    -------
    Figure
        Figure produced by the legacy `plot_diurnal_peak_phase_pblh(...)`
        wrapper.
    """
    return plot_diurnal_peak_phase_pblh(
        monan_adapter=(
            monan_adapter or build_legacy_monan_e3sm_adapter()
        ),
        e3sm_adapter=e3sm_adapter or build_legacy_e3sm_adapter(),
        day_start=day_start,
        monan_var=monan_var,
        e3sm_var=e3sm_var,
        cmap_phase=cmap_phase,
        cmap_diff=cmap_diff,
        phase_vmin=phase_vmin,
        phase_vmax=phase_vmax,
        diff_limit=diff_limit,
        minimum_amplitude_for_peak_phase=(
            minimum_amplitude_for_peak_phase
        ),
    )


# ============================================================================
# Private fixture helpers
# ============================================================================


def _build_legacy_monan_e3sm_hourly_mean_bbox(
    *,
    point_lat: float = LEGACY_HOURLY_MEAN_POINT_LAT,
    point_lon: float = LEGACY_HOURLY_MEAN_POINT_LON,
    half_box_deg: float = LEGACY_HOURLY_MEAN_HALF_BOX_DEG,
) -> tuple[float, float, float, float]:
    """Build the legacy lat/lon box used by hourly-mean MONAN/E3SM plots."""
    min_lat = max(-90.0, point_lat - half_box_deg)
    max_lat = min(90.0, point_lat + half_box_deg)
    min_lon = max(-180.0, point_lon - half_box_deg)
    max_lon = min(180.0, point_lon + half_box_deg)
    return (min_lon, max_lon, min_lat, max_lat)


def _build_legacy_profile_panel_axes_set_kwargs(
) -> list[dict[str, object]]:
    """Return per-panel axis limits for the legacy MONAN/E3SM profiles."""
    pressure_limits = (
        LEGACY_MONAN_E3SM_PROFILE_PRESSURE_TOP_HPA,
        LEGACY_MONAN_E3SM_PROFILE_PRESSURE_BOTTOM_HPA,
    )
    pressure_ticks = np.arange(
        LEGACY_MONAN_E3SM_PROFILE_PRESSURE_BOTTOM_HPA,
        LEGACY_MONAN_E3SM_PROFILE_PRESSURE_TOP_HPA - 1.0,
        -50.0,
    )
    return [
        {
            "xlim": LEGACY_MONAN_E3SM_PROFILE_THETA_XLIM,
            "ylim": pressure_limits,
            "yticks": pressure_ticks,
        },
        {
            "xlim": LEGACY_MONAN_E3SM_PROFILE_TKE_XLIM,
            "xticks": np.arange(0.0, 0.61, 0.1),
            "ylim": pressure_limits,
            "yticks": pressure_ticks,
        },
        {
            "xlim": LEGACY_MONAN_E3SM_PROFILE_QT_XLIM,
            "ylim": pressure_limits,
            "yticks": pressure_ticks,
        },
        {
            "xlim": LEGACY_MONAN_E3SM_PROFILE_WIND_SPEED_XLIM,
            "ylim": pressure_limits,
            "yticks": pressure_ticks,
        },
    ]


def _build_legacy_monan_e3sm_side_by_side_request(
    *,
    time: np.datetime64 = LEGACY_SIDE_BY_SIDE_DATE,
) -> HorizontalFieldRequest:
    """Build the legacy horizontal-field request for MONAN/E3SM maps."""
    return HorizontalFieldRequest(
        times=np.asarray([time], dtype="datetime64[ns]"),
    )


def _synchronize_panel_y_limits(
    *,
    figure: Figure,
    panel_count: int,
    panel_indices: list[int],
) -> None:
    """Apply one shared y-axis range to the selected subplot panels."""
    main_axes = figure.axes[:panel_count]
    selected_axes = [
        main_axes[panel_index]
        for panel_index in panel_indices
        if 0 <= panel_index < len(main_axes)
    ]
    if len(selected_axes) < 2:
        return

    y_limits = [axis.get_ylim() for axis in selected_axes]
    shared_ymin = min(limit[0] for limit in y_limits)
    shared_ymax = max(limit[1] for limit in y_limits)
    for axis in selected_axes:
        axis.set_ylim(shared_ymin, shared_ymax)


def _apply_common_hourly_mean_pressure_ylim(
    panels: Sequence[HourlyMeanPanelInput],
    *,
    panel_indices: Sequence[int],
) -> None:
    """Apply one shared pressure range to the selected upper panels.

    The shared interval is computed from the actual valid TKE data of each
    selected panel, not from a fixed pressure window. This keeps the
    comparison fair when one source does not provide values near the
    surface.
    """
    pressure_intervals: list[tuple[float, float]] = []
    for panel_index in panel_indices:
        if panel_index >= len(panels):
            continue

        panel = panels[panel_index]
        if not panel.layers:
            continue

        layer = panel.layers[0]
        if layer.data_kind != "time_vertical":
            continue
        if not isinstance(layer.request, TimeVerticalSectionRequest):
            continue

        try:
            plot_data = layer.adapter.to_time_vertical_section_plot_data(
                variable_name=layer.variable_name,
                request=layer.request,
            )
        except (FileNotFoundError, OSError):
            return
        pressure_interval = _compute_valid_pressure_interval(
            plot_data.field,
            plot_data.vertical_values,
        )
        if pressure_interval is not None:
            pressure_intervals.append(pressure_interval)

    if len(pressure_intervals) < 2:
        return

    shared_pressure_top = max(
        interval[0] for interval in pressure_intervals
    )
    shared_pressure_bottom = min(
        interval[1] for interval in pressure_intervals
    )
    if shared_pressure_top >= shared_pressure_bottom:
        return

    shared_pressure_top = max(
        shared_pressure_top,
        LEGACY_HOURLY_MEAN_PRESSURE_TOP_HPA,
    )
    if shared_pressure_top >= shared_pressure_bottom:
        return

    shared_ylim = (shared_pressure_bottom, shared_pressure_top)
    for panel_index in panel_indices:
        if panel_index >= len(panels):
            continue
        panels[panel_index].axes_set_kwargs["ylim"] = shared_ylim
        panels[panel_index].axes_set_kwargs["yticks"] = (
            _build_pressure_yticks(*shared_ylim)
        )


def _apply_common_cross_section_pressure_ylim(
    panels: Sequence[CrossSectionPanelInput],
    *,
    panel_indices: Sequence[int],
) -> None:
    """Apply one shared pressure range to the selected cross-section panels.

    The shared interval is computed from the actual valid TKE data of each
    selected panel. This keeps the comparison fair when one source does not
    provide valid values near the surface or near the top of the section.
    """
    pressure_intervals: list[tuple[float, float]] = []
    for panel_index in panel_indices:
        if panel_index >= len(panels):
            continue

        panel = panels[panel_index]
        if not panel.layers:
            continue

        layer = panel.layers[0]
        try:
            plot_data = layer.adapter.to_vertical_cross_section_plot_data(
                variable_name=layer.variable_name,
                request=layer.request,
            )
        except (FileNotFoundError, OSError):
            return

        pressure_interval = _compute_valid_pressure_interval(
            plot_data.field,
            plot_data.vertical_values,
        )
        if pressure_interval is not None:
            pressure_intervals.append(pressure_interval)

    if len(pressure_intervals) < 2:
        return

    shared_pressure_top = max(
        interval[0] for interval in pressure_intervals
    )
    shared_pressure_bottom = min(
        interval[1] for interval in pressure_intervals
    )
    if shared_pressure_top >= shared_pressure_bottom:
        return

    shared_ylim = (shared_pressure_bottom, shared_pressure_top)
    for panel_index in panel_indices:
        if panel_index >= len(panels):
            continue
        panels[panel_index].axes_set_kwargs["ylim"] = shared_ylim
        panels[panel_index].axes_set_kwargs["yticks"] = (
            _build_pressure_yticks(*shared_ylim)
        )


def _compute_valid_pressure_interval(
    field: np.ndarray,
    vertical_values: np.ndarray,
) -> tuple[float, float] | None:
    """Return the pressure interval where the section contains valid data."""
    valid_rows = np.any(np.isfinite(field), axis=1)
    if not np.any(valid_rows):
        return None

    pressure_values = _convert_pressure_values_to_hpa(
        np.asarray(vertical_values, dtype=float)
    )
    valid_pressure_values = pressure_values[valid_rows]
    if valid_pressure_values.size == 0:
        return None

    pressure_top = float(np.nanmin(valid_pressure_values))
    pressure_bottom = float(np.nanmax(valid_pressure_values))
    return pressure_top, pressure_bottom


def _convert_pressure_values_to_hpa(values: np.ndarray) -> np.ndarray:
    """Convert pressure values to hPa when they appear to be in Pa."""
    pressure_values = np.asarray(values, dtype=float)
    if pressure_values.size == 0:
        return pressure_values
    if float(np.nanmax(np.abs(pressure_values))) > 2000.0:
        return pressure_values / 100.0

    return pressure_values


def _build_pressure_yticks(
    pressure_bottom: float,
    pressure_top: float,
    tick_count: int = 6,
) -> np.ndarray:
    """Build pressure y-ticks with min, max and intermediate values."""
    safe_tick_count = max(int(tick_count), 3)
    tick_values = np.linspace(
        float(pressure_bottom),
        float(pressure_top),
        safe_tick_count,
    )
    return np.round(tick_values, 1)


def _build_legacy_monan_e3sm_hourly_mean_times(
    *,
    start_date: np.datetime64 = LEGACY_HOURLY_MEAN_START_DATE,
    n_days: int = LEGACY_HOURLY_MEAN_N_DAYS,
) -> np.ndarray:
    """Build the legacy time window used by hourly-mean MONAN/E3SM plots."""
    end_date = start_date + np.timedelta64(n_days, "D")
    return np.asarray([start_date, end_date], dtype="datetime64[ns]")


def _build_legacy_monan_e3sm_time_vertical_request(
    *,
    point_lat: float = LEGACY_HOURLY_MEAN_POINT_LAT,
    point_lon: float = LEGACY_HOURLY_MEAN_POINT_LON,
    start_date: np.datetime64 = LEGACY_HOURLY_MEAN_START_DATE,
    n_days: int = LEGACY_HOURLY_MEAN_N_DAYS,
    half_box_deg: float = LEGACY_HOURLY_MEAN_HALF_BOX_DEG,
) -> TimeVerticalSectionRequest:
    """Build the legacy time-vertical request for MONAN/E3SM comparison."""
    return TimeVerticalSectionRequest(
        times=_build_legacy_monan_e3sm_hourly_mean_times(
            start_date=start_date,
            n_days=n_days,
        ),
        vertical_axis="pressure",
        bbox=_build_legacy_monan_e3sm_hourly_mean_bbox(
            point_lat=point_lat,
            point_lon=point_lon,
            half_box_deg=half_box_deg,
        ),
    )


def _build_legacy_monan_e3sm_time_series_request(
    *,
    point_lat: float = LEGACY_HOURLY_MEAN_POINT_LAT,
    point_lon: float = LEGACY_HOURLY_MEAN_POINT_LON,
    start_date: np.datetime64 = LEGACY_HOURLY_MEAN_START_DATE,
    n_days: int = LEGACY_HOURLY_MEAN_N_DAYS,
    half_box_deg: float = LEGACY_HOURLY_MEAN_HALF_BOX_DEG,
) -> TimeSeriesRequest:
    """Build the legacy regional-mean time-series request for MONAN/E3SM."""
    return TimeSeriesRequest(
        times=_build_legacy_monan_e3sm_hourly_mean_times(
            start_date=start_date,
            n_days=n_days,
        ),
        bbox=_build_legacy_monan_e3sm_hourly_mean_bbox(
            point_lat=point_lat,
            point_lon=point_lon,
            half_box_deg=half_box_deg,
        ),
    )


def _build_legacy_monan_e3sm_hourly_mean_panels(
    *,
    point_lat: float = LEGACY_HOURLY_MEAN_POINT_LAT,
    point_lon: float = LEGACY_HOURLY_MEAN_POINT_LON,
    start_date: np.datetime64 = LEGACY_HOURLY_MEAN_START_DATE,
    n_days: int = LEGACY_HOURLY_MEAN_N_DAYS,
    half_box_deg: float = LEGACY_HOURLY_MEAN_HALF_BOX_DEG,
    tke_vmin: float = LEGACY_HOURLY_MEAN_TKE_VMIN,
    tke_vmax: float = LEGACY_HOURLY_MEAN_TKE_VMAX,
    monan_adapter: DataAdapter | None = None,
    e3sm_adapter: DataAdapter | None = None,
) -> list[HourlyMeanPanelInput]:
    """Build the generic hourly-mean panels for the MONAN/E3SM recipe."""
    if monan_adapter is None:
        monan_adapter = build_legacy_monan_e3sm_adapter()
    if e3sm_adapter is None:
        e3sm_adapter = build_legacy_e3sm_adapter()

    time_vertical_request = _build_legacy_monan_e3sm_time_vertical_request(
        point_lat=point_lat,
        point_lon=point_lon,
        start_date=start_date,
        n_days=n_days,
        half_box_deg=half_box_deg,
    )
    time_series_request = _build_legacy_monan_e3sm_time_series_request(
        point_lat=point_lat,
        point_lon=point_lon,
        start_date=start_date,
        n_days=n_days,
        half_box_deg=half_box_deg,
    )

    return [
        _build_legacy_hourly_mean_upper_panel(
            adapter=monan_adapter,
            label="MONAN",
            time_vertical_request=time_vertical_request,
            time_series_request=time_series_request,
            tke_vmin=tke_vmin,
            tke_vmax=tke_vmax,
        ),
        _build_legacy_hourly_mean_upper_panel(
            adapter=e3sm_adapter,
            label="E3SM",
            time_vertical_request=time_vertical_request,
            time_series_request=time_series_request,
            tke_vmin=tke_vmin,
            tke_vmax=tke_vmax,
        ),
        _build_legacy_hourly_mean_lower_panel(
            adapter=monan_adapter,
            label="MONAN",
            time_series_request=time_series_request,
        ),
        _build_legacy_hourly_mean_lower_panel(
            adapter=e3sm_adapter,
            label="E3SM",
            time_series_request=time_series_request,
        ),
    ]


def _build_legacy_monan_e3sm_hourly_mean_figure_specification(
    *,
    region_name: str = LEGACY_HOURLY_MEAN_REGION_NAME,
    point_lat: float = LEGACY_HOURLY_MEAN_POINT_LAT,
    point_lon: float = LEGACY_HOURLY_MEAN_POINT_LON,
) -> FigureSpecification:
    """Build the figure specification for the generic MONAN/E3SM example."""
    latitude_hemisphere = "N" if point_lat >= 0.0 else "S"
    longitude_hemisphere = "E" if point_lon >= 0.0 else "W"
    suptitle = (
        "TKE Vertical Profile Hourly Mean - "
        f"{region_name} "
        f"({abs(point_lat):.2f}°{latitude_hemisphere}, "
        f"{abs(point_lon):.2f}°{longitude_hemisphere})"
    )
    return FigureSpecification(
        nrows=2,
        ncols=2,
        suptitle=suptitle,
        figure_kwargs={"figsize": (16, 12), "constrained_layout": True},
        shared_colorbar_specifications=[
            SharedColorbarSpecification(
                source_panel_index=0,
                source_layer_index=0,
                target_panel_indices=[0, 1],
                label="Turbulent Kinetic Energy [m²/s²]",
                colorbar_kwargs={"pad": 0.03},
            )
        ],
    )


def _build_legacy_hourly_mean_upper_panel(
    *,
    adapter: DataAdapter,
    label: str,
    time_vertical_request: TimeVerticalSectionRequest,
    time_series_request: TimeSeriesRequest,
    tke_vmin: float,
    tke_vmax: float,
) -> HourlyMeanPanelInput:
    """Build one upper hourly-mean `time x pressure` panel."""
    return HourlyMeanPanelInput(
        layers=[
            HourlyMeanLayerInput(
                adapter=adapter,
                request=time_vertical_request,
                variable_name="tke_pbl",
                data_kind="time_vertical",
                render_specification=RenderSpecification(
                    artist_method="pcolormesh",
                    artist_kwargs={
                        "cmap": "viridis",
                        "vmin": tke_vmin,
                        "vmax": tke_vmax,
                        "shading": "auto",
                    },
                ),
            ),
            HourlyMeanLayerInput(
                adapter=adapter,
                request=time_vertical_request,
                variable_name="qc",
                data_kind="time_vertical",
                render_specification=RenderSpecification(
                    artist_method="contour",
                    artist_kwargs={
                        "colors": "white",
                        "linewidths": 0.8,
                        "alpha": 0.8,
                    },
                    artist_calls=[
                        {
                            "method": "clabel",
                            "kwargs": {
                                "inline": True,
                                "fontsize": 7,
                                "fmt": "%.1e",
                            },
                        }
                    ],
                ),
                minimum_contour_level=LEGACY_HOURLY_MEAN_QC_CONTOUR_MIN,
            ),
            HourlyMeanLayerInput(
                adapter=adapter,
                request=time_series_request,
                variable_name="hpbl",
                data_kind="time_series",
                render_specification=RenderSpecification(
                    artist_method="plot",
                    artist_kwargs={
                        "color": "black",
                        "linewidth": 2.0,
                    },
                ),
                legend_label="HPBL (pressure-equivalent)",
                convert_height_to_pressure=True,
            ),
        ],
        axes_set_kwargs={
            "title": f"{label} - TKE Hourly Mean",
            "xlabel": "Local hour",
            "ylabel": "pressure [hPa]",
            "xlim": (0, 23),
            "ylim": (1000, LEGACY_HOURLY_MEAN_PRESSURE_TOP_HPA),
            "yticks": _build_pressure_yticks(
                1000.0,
                LEGACY_HOURLY_MEAN_PRESSURE_TOP_HPA,
            ),
        },
        grid_kwargs={"visible": True, "alpha": 0.3},
        legend_kwargs={"loc": "upper right"},
        axes_calls=[
            {"method": "set_xticks", "args": (np.arange(0, 24, 3),)},
        ],
    )


def _build_legacy_hourly_mean_lower_panel(
    *,
    adapter: DataAdapter,
    label: str,
    time_series_request: TimeSeriesRequest,
) -> HourlyMeanPanelInput:
    """Build one lower hourly-mean sensible-heat-flux panel."""
    return HourlyMeanPanelInput(
        layers=[
            HourlyMeanLayerInput(
                adapter=adapter,
                request=time_series_request,
                variable_name="sensible_heat_flux",
                data_kind="time_series",
                render_specification=RenderSpecification(
                    artist_method="plot",
                    artist_kwargs={
                        "color": "tab:red",
                        "linewidth": 2.0,
                    },
                ),
            )
        ],
        axes_set_kwargs={
            "title": f"{label} - Sensible Heat Flux Hourly Mean",
            "xlabel": "Local hour",
            "ylabel": "Sensible Heat Flux [W/m²]",
            "xlim": (0, 23),
        },
        grid_kwargs={"visible": True, "alpha": 0.3},
        axes_calls=[
            {"method": "set_xticks", "args": (np.arange(0, 24, 3),)},
        ],
    )


def _build_legacy_monan_e3sm_cross_section_request(
    *,
    time: np.datetime64 = LEGACY_CROSS_SECTION_START_DATE,
    start_lat: float = LEGACY_CROSS_SECTION_START_LAT,
    start_lon: float = LEGACY_CROSS_SECTION_START_LON,
    end_lat: float = LEGACY_CROSS_SECTION_END_LAT,
    end_lon: float = LEGACY_CROSS_SECTION_END_LON,
    spacing_km: float = LEGACY_CROSS_SECTION_SPACING_KM,
) -> VerticalCrossSectionRequest:
    """Build the legacy cross-section request for MONAN/E3SM comparison."""
    return VerticalCrossSectionRequest(
        times=np.asarray([time], dtype="datetime64[ns]"),
        start_lat=start_lat,
        start_lon=start_lon,
        end_lat=end_lat,
        end_lon=end_lon,
        vertical_axis="pressure",
        spacing_km=spacing_km,
    )


def _build_legacy_monan_e3sm_cross_section_panels(
    *,
    time: np.datetime64 = LEGACY_CROSS_SECTION_START_DATE,
    start_lat: float = LEGACY_CROSS_SECTION_START_LAT,
    start_lon: float = LEGACY_CROSS_SECTION_START_LON,
    end_lat: float = LEGACY_CROSS_SECTION_END_LAT,
    end_lon: float = LEGACY_CROSS_SECTION_END_LON,
    spacing_km: float = LEGACY_CROSS_SECTION_SPACING_KM,
    main_variable_name: str = LEGACY_CROSS_SECTION_MAIN_VARIABLE_NAME,
    field_vmin: float | None = LEGACY_CROSS_SECTION_FIELD_VMIN,
    field_vmax: float | None = LEGACY_CROSS_SECTION_FIELD_VMAX,
    monan_adapter: DataAdapter | None = None,
    e3sm_adapter: DataAdapter | None = None,
) -> list[CrossSectionPanelInput]:
    """Build the legacy MONAN/E3SM transect panels."""
    if monan_adapter is None:
        monan_adapter = build_legacy_monan_e3sm_adapter()
    if e3sm_adapter is None:
        e3sm_adapter = build_legacy_e3sm_adapter()

    request = _build_legacy_monan_e3sm_cross_section_request(
        time=time,
        start_lat=start_lat,
        start_lon=start_lon,
        end_lat=end_lat,
        end_lon=end_lon,
        spacing_km=spacing_km,
    )
    return [
        _build_legacy_cross_section_panel(
            adapter=monan_adapter,
            label="MONAN",
            request=request,
            main_variable_name=main_variable_name,
            field_vmin=field_vmin,
            field_vmax=field_vmax,
        ),
        _build_legacy_cross_section_panel(
            adapter=e3sm_adapter,
            label="E3SM",
            request=request,
            main_variable_name=main_variable_name,
            field_vmin=field_vmin,
            field_vmax=field_vmax,
        ),
    ]


def _build_legacy_monan_e3sm_cross_section_figure_specification(
    *,
    time: np.datetime64 = LEGACY_CROSS_SECTION_START_DATE,
    start_lat: float = LEGACY_CROSS_SECTION_START_LAT,
    start_lon: float = LEGACY_CROSS_SECTION_START_LON,
    end_lat: float = LEGACY_CROSS_SECTION_END_LAT,
    end_lon: float = LEGACY_CROSS_SECTION_END_LON,
    main_variable_name: str = LEGACY_CROSS_SECTION_MAIN_VARIABLE_NAME,
    main_field_label: str = LEGACY_CROSS_SECTION_MAIN_FIELD_LABEL,
    colorbar_label: str = LEGACY_CROSS_SECTION_MAIN_COLORBAR_LABEL,
) -> FigureSpecification:
    """Build the figure specification for the legacy transect recipe."""
    time_label = np.datetime_as_string(time, unit="m")
    suptitle = (
        f"Transect {main_field_label} ({main_variable_name}) | "
        f"{time_label} | "
        f"({_format_latlon_label(start_lat, start_lon)}) -> "
        f"({_format_latlon_label(end_lat, end_lon)})"
    )
    return FigureSpecification(
        nrows=1,
        ncols=2,
        suptitle=suptitle,
        figure_kwargs={"figsize": (14, 6), "constrained_layout": True},
        shared_colorbar_specifications=[
            SharedColorbarSpecification(
                source_panel_index=0,
                source_layer_index=0,
                target_panel_indices=[0, 1],
                label=colorbar_label,
                colorbar_kwargs={"orientation": "horizontal", "pad": 0.14},
            )
        ],
    )


def _build_legacy_cross_section_panel(
    *,
    adapter: DataAdapter,
    label: str,
    request: VerticalCrossSectionRequest,
    main_variable_name: str,
    field_vmin: float | None,
    field_vmax: float | None,
) -> CrossSectionPanelInput:
    """Build one legacy cross-section panel for MONAN or E3SM."""
    field_artist_kwargs = {"cmap": "viridis", "shading": "auto"}
    if field_vmin is not None:
        field_artist_kwargs["vmin"] = field_vmin
    if field_vmax is not None:
        field_artist_kwargs["vmax"] = field_vmax

    return CrossSectionPanelInput(
        layers=[
            CrossSectionLayerInput(
                adapter=adapter,
                request=request,
                variable_name=main_variable_name,
                render_specification=RenderSpecification(
                    artist_method="pcolormesh",
                    artist_kwargs=field_artist_kwargs,
                ),
                convert_pressure_to_hpa=True,
            ),
            CrossSectionLayerInput(
                adapter=adapter,
                request=request,
                variable_name="qc",
                render_specification=RenderSpecification(
                    artist_method="contour",
                    artist_kwargs={
                        "colors": "white",
                        "linewidths": 0.8,
                        "alpha": 0.8,
                    },
                    artist_calls=[
                        {
                            "method": "clabel",
                            "kwargs": {
                                "inline": True,
                                "fontsize": 7,
                                "fmt": "%.1e",
                            },
                        }
                    ],
                ),
                minimum_contour_level=LEGACY_CROSS_SECTION_QC_CONTOUR_MIN,
                convert_pressure_to_hpa=True,
            ),
        ],
        axes_set_kwargs={
            "title": label,
            "xlabel": "Coordinates along transect",
            "ylabel": "Pressure [hPa]",
            "ylim": (1000.0, LEGACY_CROSS_SECTION_PRESSURE_TOP_HPA),
            "yticks": _build_pressure_yticks(
                1000.0,
                LEGACY_CROSS_SECTION_PRESSURE_TOP_HPA,
            ),
        },
        grid_kwargs={"visible": True, "alpha": 0.25},
        transect_axis_mode="distance_km",
        use_coordinate_tick_labels=True,
        transect_tick_count=4,
    )


def _format_latlon_label(lat: float, lon: float) -> str:
    """Format latitude/longitude with hemisphere suffixes."""
    normalized_lon = ((lon + 180.0) % 360.0) - 180.0
    lat_hemi = "N" if lat >= 0.0 else "S"
    lon_hemi = "E" if normalized_lon >= 0.0 else "W"
    return (
        f"{abs(lat):.2f}°{lat_hemi}, "
        f"{abs(normalized_lon):.2f}°{lon_hemi}"
    )


def _build_legacy_monan_e3sm_side_by_side_panels(
    *,
    time: np.datetime64 = LEGACY_SIDE_BY_SIDE_DATE,
    variable_name: str = LEGACY_SIDE_BY_SIDE_VARIABLE_NAME,
    cmap: str = LEGACY_SIDE_BY_SIDE_CMAP,
    field_vmin: float | None = LEGACY_SIDE_BY_SIDE_FIELD_VMIN,
    field_vmax: float | None = LEGACY_SIDE_BY_SIDE_FIELD_VMAX,
    monan_adapter: DataAdapter | None = None,
    e3sm_adapter: DataAdapter | None = None,
) -> list[MapPanelInput]:
    """Build the legacy MONAN/E3SM side-by-side map panels."""
    if monan_adapter is None:
        monan_adapter = build_legacy_monan_e3sm_adapter()
    if e3sm_adapter is None:
        e3sm_adapter = build_legacy_e3sm_adapter()

    request = _build_legacy_monan_e3sm_side_by_side_request(time=time)
    return [
        _build_legacy_side_by_side_panel(
            adapter=monan_adapter,
            label="MONAN",
            request=request,
            variable_name=variable_name,
            cmap=cmap,
            field_vmin=field_vmin,
            field_vmax=field_vmax,
            show_left_labels=True,
        ),
        _build_legacy_side_by_side_panel(
            adapter=e3sm_adapter,
            label="E3SM",
            request=request,
            variable_name=variable_name,
            cmap=cmap,
            field_vmin=field_vmin,
            field_vmax=field_vmax,
            show_left_labels=False,
        ),
    ]


def _build_legacy_monan_e3sm_side_by_side_figure_specification(
    *,
    time: np.datetime64 = LEGACY_SIDE_BY_SIDE_DATE,
    field_label: str = LEGACY_SIDE_BY_SIDE_FIELD_LABEL,
    colorbar_label: str = LEGACY_SIDE_BY_SIDE_COLORBAR_LABEL,
) -> FigureSpecification:
    """Build the figure specification for the legacy side-by-side map."""
    time_label = np.datetime_as_string(time, unit="m")
    suptitle = f"{field_label} side-by-side | {time_label}"
    return FigureSpecification(
        nrows=1,
        ncols=2,
        suptitle=suptitle,
        figure_kwargs={"figsize": (16, 6), "constrained_layout": True},
        shared_colorbar_specifications=[
            SharedColorbarSpecification(
                source_panel_index=0,
                source_layer_index=0,
                target_panel_indices=[0, 1],
                label=colorbar_label,
                colorbar_kwargs={
                    "orientation": "horizontal",
                    "fraction": 0.05,
                    "pad": 0.05,
                },
            )
        ],
    )


def _build_legacy_monan_e3sm_paper_grade_rows(
    *,
    time: np.datetime64 = LEGACY_PAPER_GRADE_DATE,
    variable_pairs: Sequence[tuple[str, str]] = (
        LEGACY_PAPER_GRADE_VARIABLE_PAIRS
    ),
    labels: Sequence[str] = LEGACY_PAPER_GRADE_LABELS,
    vmins: Sequence[float] = LEGACY_PAPER_GRADE_VMINS,
    vmaxs: Sequence[float] = LEGACY_PAPER_GRADE_VMAXS,
    cmaps_abs: Sequence[str] = LEGACY_PAPER_GRADE_CMAPS_ABS,
    cmap_diff: str = LEGACY_PAPER_GRADE_CMAP_DIFF,
    diff_limits: Sequence[float | None] = LEGACY_PAPER_GRADE_DIFF_LIMITS,
    absolute_colorbar_labels: Sequence[str] = (
        LEGACY_PAPER_GRADE_ABSOLUTE_COLORBAR_LABELS
    ),
    difference_colorbar_labels: Sequence[str] = (
        LEGACY_PAPER_GRADE_DIFFERENCE_COLORBAR_LABELS
    ),
    monan_adapter: DataAdapter | None = None,
    e3sm_adapter: DataAdapter | None = None,
) -> list[MapComparisonRowInput]:
    """Build the legacy MONAN/E3SM paper-grade comparison rows."""
    row_count = len(variable_pairs)
    parameter_lengths = [
        len(labels),
        len(vmins),
        len(vmaxs),
        len(cmaps_abs),
        len(diff_limits),
        len(absolute_colorbar_labels),
        len(difference_colorbar_labels),
    ]
    if any(length != row_count for length in parameter_lengths):
        raise ValueError(
            "Legacy paper-grade rows require consistent row-wise lengths."
        )

    if monan_adapter is None:
        monan_adapter = build_legacy_monan_e3sm_adapter()
    if e3sm_adapter is None:
        e3sm_adapter = build_legacy_e3sm_adapter()

    request = _build_legacy_monan_e3sm_side_by_side_request(time=time)
    rows: list[MapComparisonRowInput] = []
    for (
        variable_pair,
        label,
        vmin,
        vmax,
        cmap_abs,
        diff_limit,
        absolute_colorbar_label,
        difference_colorbar_label,
    ) in zip(
        variable_pairs,
        labels,
        vmins,
        vmaxs,
        cmaps_abs,
        diff_limits,
        absolute_colorbar_labels,
        difference_colorbar_labels,
    ):
        monan_variable, e3sm_variable = variable_pair
        difference_artist_kwargs = {"cmap": cmap_diff}
        if diff_limit is not None:
            difference_artist_kwargs["vmin"] = -float(diff_limit)
            difference_artist_kwargs["vmax"] = float(diff_limit)

        rows.append(
            MapComparisonRowInput(
                left_source=MapComparisonSourceInput(
                    adapter=monan_adapter,
                    request=request,
                    variable_name=monan_variable,
                    source_label="MONAN",
                ),
                right_source=MapComparisonSourceInput(
                    adapter=e3sm_adapter,
                    request=request,
                    variable_name=e3sm_variable,
                    source_label="E3SM",
                ),
                field_label=label,
                absolute_render_specification=RenderSpecification(
                    artist_method="pcolormesh",
                    artist_kwargs={
                        "cmap": cmap_abs,
                        "vmin": float(vmin),
                        "vmax": float(vmax),
                    },
                ),
                difference_render_specification=RenderSpecification(
                    artist_method="pcolormesh",
                    artist_kwargs=difference_artist_kwargs,
                ),
                absolute_colorbar_label=absolute_colorbar_label,
                difference_colorbar_label=difference_colorbar_label,
                absolute_colorbar_kwargs={
                    "orientation": "horizontal",
                    "fraction": 0.045,
                    "pad": 0.04,
                },
                difference_colorbar_kwargs={
                    "orientation": "horizontal",
                    "fraction": 0.045,
                    "pad": 0.04,
                },
                coastlines_kwargs={"linewidth": 0.8},
                borders_kwargs={"linewidth": 0.5},
                gridlines_kwargs={
                    "draw_labels": True,
                    "linewidth": 0.6,
                    "alpha": 0.3,
                    "x_inline": False,
                    "y_inline": False,
                },
            )
        )

    return rows


def _build_legacy_monan_e3sm_paper_grade_figure_specification(
    *,
    time: np.datetime64 = LEGACY_PAPER_GRADE_DATE,
    row_count: int = len(LEGACY_PAPER_GRADE_VARIABLE_PAIRS),
) -> FigureSpecification:
    """Build the figure specification for the legacy paper-grade panel."""
    time_label = np.datetime_as_string(time, unit="m")
    return FigureSpecification(
        nrows=row_count,
        ncols=3,
        suptitle=f"Initialized 2014-02-24T00:00 - Forecast {time_label}",
        figure_kwargs={
            "figsize": (22, max(5.0 * row_count, 9.0)),
            "constrained_layout": True,
        },
    )


def _build_legacy_monan_e3sm_diurnal_amplitude_rows(
    *,
    day_start: np.datetime64 = LEGACY_DIURNAL_AMPLITUDE_START_DATE,
    monan_var: str = LEGACY_DIURNAL_AMPLITUDE_MONAN_VAR,
    e3sm_var: str = LEGACY_DIURNAL_AMPLITUDE_E3SM_VAR,
    field_label: str = LEGACY_DIURNAL_AMPLITUDE_FIELD_LABEL,
    cmap_abs: str = LEGACY_DIURNAL_AMPLITUDE_CMAP_ABS,
    cmap_diff: str = LEGACY_DIURNAL_AMPLITUDE_CMAP_DIFF,
    vmin: float = LEGACY_DIURNAL_AMPLITUDE_VMIN,
    vmax: float | None = LEGACY_DIURNAL_AMPLITUDE_VMAX,
    diff_limit: float | None = LEGACY_DIURNAL_AMPLITUDE_DIFF_LIMIT,
    monan_adapter: DataAdapter | None = None,
    e3sm_adapter: DataAdapter | None = None,
) -> list[DiurnalAmplitudeRowInput]:
    """Build the legacy MONAN/E3SM diurnal-amplitude comparison rows."""
    if monan_adapter is None:
        monan_adapter = build_legacy_monan_e3sm_adapter()
    if e3sm_adapter is None:
        e3sm_adapter = build_legacy_e3sm_adapter()

    absolute_artist_kwargs = {"cmap": cmap_abs, "vmin": float(vmin)}
    if vmax is not None:
        absolute_artist_kwargs["vmax"] = float(vmax)

    difference_artist_kwargs = {"cmap": cmap_diff}
    if diff_limit is not None:
        difference_artist_kwargs["vmin"] = -float(diff_limit)
        difference_artist_kwargs["vmax"] = float(diff_limit)

    return [
        DiurnalAmplitudeRowInput(
            left_source=DiurnalAmplitudeSourceInput(
                adapter=monan_adapter,
                variable_name=monan_var,
                source_label="MONAN",
            ),
            right_source=DiurnalAmplitudeSourceInput(
                adapter=e3sm_adapter,
                variable_name=e3sm_var,
                source_label="E3SM",
            ),
            day_start=day_start,
            field_label=field_label,
            absolute_render_specification=RenderSpecification(
                artist_method="pcolormesh",
                artist_kwargs=absolute_artist_kwargs,
            ),
            difference_render_specification=RenderSpecification(
                artist_method="pcolormesh",
                artist_kwargs=difference_artist_kwargs,
            ),
            left_panel_title="MONAN - Diurnal Amplitude PBLH",
            right_panel_title="E3SM - Diurnal Amplitude PBLH",
            difference_panel_title="Δ Amplitude PBLH (MONAN - E3SM)",
            absolute_colorbar_label="Amplitude PBLH",
            difference_colorbar_label="Δ Amplitude PBLH [m]",
            absolute_colorbar_kwargs={
                "orientation": "horizontal",
                "fraction": 0.045,
                "pad": 0.04,
            },
            difference_colorbar_kwargs={
                "orientation": "horizontal",
                "fraction": 0.045,
                "pad": 0.04,
            },
            coastlines_kwargs={"linewidth": 0.8},
            borders_kwargs={"linewidth": 0.5},
            gridlines_kwargs={
                "draw_labels": True,
                "linewidth": 0.6,
                "alpha": 0.3,
                "x_inline": False,
                "y_inline": False,
            },
        )
    ]


def _build_legacy_monan_e3sm_diurnal_amplitude_figure_specification(
    *,
    day_start: np.datetime64 = LEGACY_DIURNAL_AMPLITUDE_START_DATE,
) -> FigureSpecification:
    """Build the figure specification for the legacy diurnal amplitude."""
    day_label = np.datetime_as_string(day_start, unit="D")
    return FigureSpecification(
        nrows=1,
        ncols=3,
        suptitle=f"Diurnal-Cycle Amplitude of PBLH - {day_label}",
        figure_kwargs={"figsize": (18, 4.8), "constrained_layout": True},
    )


def _build_legacy_monan_e3sm_diurnal_amplitude_panel_rows(
    *,
    day_start: np.datetime64 = LEGACY_DIURNAL_AMPLITUDE_START_DATE,
    variable_pairs: Sequence[tuple[str, str]] = (
        LEGACY_DIURNAL_AMPLITUDE_PANEL_VARIABLE_PAIRS
    ),
    row_labels: Sequence[str] = (
        LEGACY_DIURNAL_AMPLITUDE_PANEL_ROW_LABELS
    ),
    field_labels: Sequence[str] = (
        LEGACY_DIURNAL_AMPLITUDE_PANEL_FIELD_LABELS
    ),
    vmins: Sequence[float] = LEGACY_DIURNAL_AMPLITUDE_PANEL_VMINS,
    vmaxs: Sequence[float | None] = LEGACY_DIURNAL_AMPLITUDE_PANEL_VMAXS,
    cmaps_abs: Sequence[str] = (
        LEGACY_DIURNAL_AMPLITUDE_PANEL_CMAPS_ABS
    ),
    cmap_diff: str = LEGACY_DIURNAL_AMPLITUDE_PANEL_CMAP_DIFF,
    diff_limits: Sequence[float | None] = (
        LEGACY_DIURNAL_AMPLITUDE_PANEL_DIFF_LIMITS
    ),
    absolute_colorbar_labels: Sequence[str] = (
        LEGACY_DIURNAL_AMPLITUDE_PANEL_ABSOLUTE_COLORBAR_LABELS
    ),
    difference_colorbar_labels: Sequence[str] = (
        LEGACY_DIURNAL_AMPLITUDE_PANEL_DIFFERENCE_COLORBAR_LABELS
    ),
    monan_adapter: DataAdapter | None = None,
    e3sm_adapter: DataAdapter | None = None,
) -> list[DiurnalAmplitudeMatrixRowInput]:
    """Build the legacy MONAN/E3SM diurnal-amplitude matrix rows."""
    row_count = len(variable_pairs)
    parameter_lengths = [
        len(row_labels),
        len(field_labels),
        len(vmins),
        len(vmaxs),
        len(cmaps_abs),
        len(diff_limits),
        len(absolute_colorbar_labels),
        len(difference_colorbar_labels),
    ]
    if any(length != row_count for length in parameter_lengths):
        raise ValueError(
            "Legacy diurnal-amplitude panel rows require consistent "
            "row-wise lengths."
        )

    if monan_adapter is None:
        monan_adapter = build_legacy_monan_e3sm_adapter()
    if e3sm_adapter is None:
        e3sm_adapter = build_legacy_e3sm_adapter()

    rows: list[DiurnalAmplitudeMatrixRowInput] = []
    for (
        variable_pair,
        row_label,
        field_label,
        vmin,
        vmax,
        cmap_abs,
        diff_limit,
        absolute_colorbar_label,
        difference_colorbar_label,
    ) in zip(
        variable_pairs,
        row_labels,
        field_labels,
        vmins,
        vmaxs,
        cmaps_abs,
        diff_limits,
        absolute_colorbar_labels,
        difference_colorbar_labels,
    ):
        monan_variable, e3sm_variable = variable_pair
        absolute_artist_kwargs = {
            "cmap": cmap_abs,
            "vmin": float(vmin),
        }
        if vmax is not None:
            absolute_artist_kwargs["vmax"] = float(vmax)

        difference_artist_kwargs = {"cmap": cmap_diff}
        if diff_limit is not None:
            difference_artist_kwargs["vmin"] = -float(diff_limit)
            difference_artist_kwargs["vmax"] = float(diff_limit)

        rows.append(
            DiurnalAmplitudeMatrixRowInput(
                left_source=DiurnalAmplitudeMatrixSourceInput(
                    adapter=monan_adapter,
                    variable_name=monan_variable,
                    source_label="MONAN",
                ),
                right_source=DiurnalAmplitudeMatrixSourceInput(
                    adapter=e3sm_adapter,
                    variable_name=e3sm_variable,
                    source_label="E3SM",
                ),
                day_start=day_start,
                row_label=row_label,
                field_label=field_label,
                absolute_render_specification=RenderSpecification(
                    artist_method="pcolormesh",
                    artist_kwargs=absolute_artist_kwargs,
                ),
                difference_render_specification=RenderSpecification(
                    artist_method="pcolormesh",
                    artist_kwargs=difference_artist_kwargs,
                ),
                left_panel_title=f"MONAN - {field_label}",
                right_panel_title=f"E3SM - {field_label}",
                difference_panel_title=(
                    f"Delta {field_label} (MONAN - E3SM)"
                ),
                absolute_colorbar_label=absolute_colorbar_label,
                difference_colorbar_label=difference_colorbar_label,
                absolute_colorbar_kwargs={
                    "orientation": "horizontal",
                    "fraction": 0.045,
                    "pad": 0.04,
                },
                difference_colorbar_kwargs={
                    "orientation": "horizontal",
                    "fraction": 0.045,
                    "pad": 0.04,
                },
                coastlines_kwargs={"linewidth": 0.8},
                borders_kwargs={"linewidth": 0.5},
                gridlines_kwargs={
                    "draw_labels": True,
                    "linewidth": 0.6,
                    "alpha": 0.3,
                    "x_inline": False,
                    "y_inline": False,
                },
            )
        )

    return rows


def _build_legacy_monan_e3sm_diurnal_amplitude_panel_figure_specification(
    *,
    day_start: np.datetime64 = LEGACY_DIURNAL_AMPLITUDE_START_DATE,
    row_count: int = len(LEGACY_DIURNAL_AMPLITUDE_PANEL_VARIABLE_PAIRS),
) -> FigureSpecification:
    """Build the figure specification for the amplitude matrix panel."""
    day_label = np.datetime_as_string(day_start, unit="D")
    return FigureSpecification(
        nrows=row_count,
        ncols=3,
        suptitle=f"Diurnal-Cycle Amplitude Panel - {day_label}",
        figure_kwargs={
            "figsize": (22, max(5.0 * row_count, 9.0)),
            "constrained_layout": True,
        },
    )


def _build_diurnal_extrema_defaults(
    time_reduce: str,
) -> tuple[
    Sequence[str],
    Sequence[str],
    Sequence[str],
    Sequence[float],
    Sequence[float | None],
]:
    """Return the default labels and limits for one extrema panel."""
    if time_reduce == "min":
        return (
            ("Minimum PBLH", "Minimum SHF"),
            ("Minimum PBLH", "Minimum SHF"),
            ("Δ Minimum PBLH", "Δ Minimum SHF"),
            (
                LEGACY_DIURNAL_EXTREMA_PBLH_MIN_VMIN,
                LEGACY_DIURNAL_EXTREMA_SHF_MIN_VMIN,
            ),
            (
                LEGACY_DIURNAL_EXTREMA_PBLH_MIN_VMAX,
                LEGACY_DIURNAL_EXTREMA_SHF_MIN_VMAX,
            ),
        )

    if time_reduce == "max":
        return (
            ("Maximum PBLH", "Maximum SHF"),
            ("Maximum PBLH", "Maximum SHF"),
            ("Δ Maximum PBLH", "Δ Maximum SHF"),
            (
                LEGACY_DIURNAL_EXTREMA_PBLH_MAX_VMIN,
                LEGACY_DIURNAL_EXTREMA_SHF_MAX_VMIN,
            ),
            (
                LEGACY_DIURNAL_EXTREMA_PBLH_MAX_VMAX,
                LEGACY_DIURNAL_EXTREMA_SHF_MAX_VMAX,
            ),
        )

    raise ValueError(
        "Diurnal extrema panel expects time_reduce to be "
        "'min' or 'max'."
    )


def _build_monan_e3sm_diurnal_extrema_panel_rows(
    *,
    day_start: np.datetime64 = LEGACY_DIURNAL_AMPLITUDE_START_DATE,
    time_reduce: str = "min",
    variable_pairs: Sequence[tuple[str, str]] = (
        LEGACY_DIURNAL_EXTREMA_VARIABLE_PAIRS
    ),
    row_labels: Sequence[str] = LEGACY_DIURNAL_EXTREMA_ROW_LABELS,
    field_labels: Sequence[str] = ("Minimum PBLH", "Minimum SHF"),
    vmins: Sequence[float] = (
        LEGACY_DIURNAL_EXTREMA_PBLH_MIN_VMIN,
        LEGACY_DIURNAL_EXTREMA_SHF_MIN_VMIN,
    ),
    vmaxs: Sequence[float | None] = (
        LEGACY_DIURNAL_EXTREMA_PBLH_MIN_VMAX,
        LEGACY_DIURNAL_EXTREMA_SHF_MIN_VMAX,
    ),
    cmaps_abs: Sequence[str] = LEGACY_DIURNAL_EXTREMA_CMAPS_ABS,
    cmap_diff: str = LEGACY_DIURNAL_EXTREMA_CMAP_DIFF,
    diff_limits: Sequence[float | None] = (
        LEGACY_DIURNAL_EXTREMA_DIFF_MIN_LIMITS
    ),
    absolute_colorbar_labels: Sequence[str] = (
        "Minimum PBLH",
        "Minimum SHF",
    ),
    difference_colorbar_labels: Sequence[str] = (
        "Δ Minimum PBLH",
        "Δ Minimum SHF",
    ),
    monan_adapter: DataAdapter | None = None,
    e3sm_adapter: DataAdapter | None = None,
) -> list[DiurnalExtremaMatrixRowInput]:
    """Build the MONAN/E3SM diurnal-extrema matrix rows."""
    row_count = len(variable_pairs)
    parameter_lengths = [
        len(row_labels),
        len(field_labels),
        len(vmins),
        len(vmaxs),
        len(cmaps_abs),
        len(diff_limits),
        len(absolute_colorbar_labels),
        len(difference_colorbar_labels),
    ]
    if any(length != row_count for length in parameter_lengths):
        raise ValueError(
            "Diurnal-extrema panel rows require consistent "
            "row-wise lengths."
        )

    if monan_adapter is None:
        monan_adapter = build_legacy_monan_e3sm_adapter()
    if e3sm_adapter is None:
        e3sm_adapter = build_legacy_e3sm_adapter()

    rows: list[DiurnalExtremaMatrixRowInput] = []
    for (
        variable_pair,
        row_label,
        field_label,
        vmin,
        vmax,
        cmap_abs,
        diff_limit,
        absolute_colorbar_label,
        difference_colorbar_label,
    ) in zip(
        variable_pairs,
        row_labels,
        field_labels,
        vmins,
        vmaxs,
        cmaps_abs,
        diff_limits,
        absolute_colorbar_labels,
        difference_colorbar_labels,
    ):
        monan_variable, e3sm_variable = variable_pair
        absolute_artist_kwargs = {
            "cmap": cmap_abs,
            "vmin": float(vmin),
        }
        if vmax is not None:
            absolute_artist_kwargs["vmax"] = float(vmax)

        difference_artist_kwargs = {"cmap": cmap_diff}
        if diff_limit is not None:
            difference_artist_kwargs["vmin"] = -float(diff_limit)
            difference_artist_kwargs["vmax"] = float(diff_limit)

        rows.append(
            DiurnalExtremaMatrixRowInput(
                left_source=DiurnalExtremaMatrixSourceInput(
                    adapter=monan_adapter,
                    variable_name=monan_variable,
                    source_label="MONAN",
                ),
                right_source=DiurnalExtremaMatrixSourceInput(
                    adapter=e3sm_adapter,
                    variable_name=e3sm_variable,
                    source_label="E3SM",
                ),
                day_start=day_start,
                time_reduce=time_reduce,  # type: ignore[arg-type]
                row_label=row_label,
                field_label=field_label,
                absolute_render_specification=RenderSpecification(
                    artist_method="pcolormesh",
                    artist_kwargs=absolute_artist_kwargs,
                ),
                difference_render_specification=RenderSpecification(
                    artist_method="pcolormesh",
                    artist_kwargs=difference_artist_kwargs,
                ),
                left_panel_title=f"MONAN - {field_label}",
                right_panel_title=f"E3SM - {field_label}",
                difference_panel_title=(
                    f"Δ {field_label} (MONAN - E3SM)"
                ),
                absolute_colorbar_label=absolute_colorbar_label,
                difference_colorbar_label=difference_colorbar_label,
                absolute_colorbar_kwargs={
                    "orientation": "horizontal",
                    "fraction": 0.045,
                    "pad": 0.04,
                },
                difference_colorbar_kwargs={
                    "orientation": "horizontal",
                    "fraction": 0.045,
                    "pad": 0.04,
                },
                coastlines_kwargs={"linewidth": 0.8},
                borders_kwargs={"linewidth": 0.5},
                gridlines_kwargs={
                    "draw_labels": True,
                    "linewidth": 0.6,
                    "alpha": 0.3,
                    "x_inline": False,
                    "y_inline": False,
                },
            )
        )

    return rows


def _build_monan_e3sm_diurnal_extrema_panel_figure_specification(
    *,
    day_start: np.datetime64 = LEGACY_DIURNAL_AMPLITUDE_START_DATE,
    time_reduce: str = "min",
    row_count: int = len(LEGACY_DIURNAL_EXTREMA_VARIABLE_PAIRS),
) -> FigureSpecification:
    """Build the figure specification for the extrema matrix panel."""
    day_label = np.datetime_as_string(day_start, unit="D")
    if time_reduce == "min":
        title_prefix = "Diurnal-Cycle Minimum Panel"
    elif time_reduce == "max":
        title_prefix = "Diurnal-Cycle Maximum Panel"
    else:
        raise ValueError(
            "Diurnal extrema panel expects time_reduce to be "
            "'min' or 'max'."
        )

    return FigureSpecification(
        nrows=row_count,
        ncols=3,
        suptitle=f"{title_prefix} - {day_label}",
        figure_kwargs={
            "figsize": (22, max(5.0 * row_count, 9.0)),
            "constrained_layout": True,
        },
    )


def _build_legacy_monan_e3sm_diurnal_peak_phase_rows(
    *,
    day_start: np.datetime64 = LEGACY_DIURNAL_PHASE_START_DATE,
    monan_var: str = LEGACY_DIURNAL_PHASE_MONAN_VAR,
    e3sm_var: str = LEGACY_DIURNAL_PHASE_E3SM_VAR,
    field_label: str = LEGACY_DIURNAL_PHASE_FIELD_LABEL,
    cmap_phase: str = LEGACY_DIURNAL_PHASE_CMAP_ABS,
    cmap_diff: str = LEGACY_DIURNAL_PHASE_CMAP_DIFF,
    phase_vmin: float = LEGACY_DIURNAL_PHASE_VMIN,
    phase_vmax: float = LEGACY_DIURNAL_PHASE_VMAX,
    diff_limit: float = LEGACY_DIURNAL_PHASE_DIFF_LIMIT,
    minimum_amplitude_for_peak_phase: float | None = (
        LEGACY_DIURNAL_PHASE_MINIMUM_AMPLITUDE_FOR_PEAK_PHASE
    ),
    monan_adapter: DataAdapter | None = None,
    e3sm_adapter: DataAdapter | None = None,
) -> list[DiurnalPeakPhaseRowInput]:
    """Build the legacy MONAN/E3SM diurnal peak-phase comparison rows."""
    if monan_adapter is None:
        monan_adapter = build_legacy_monan_e3sm_adapter()
    if e3sm_adapter is None:
        e3sm_adapter = build_legacy_e3sm_adapter()

    return [
        DiurnalPeakPhaseRowInput(
            left_source=DiurnalPeakPhaseSourceInput(
                adapter=monan_adapter,
                variable_name=monan_var,
                source_label="MONAN",
            ),
            right_source=DiurnalPeakPhaseSourceInput(
                adapter=e3sm_adapter,
                variable_name=e3sm_var,
                source_label="E3SM",
            ),
            day_start=day_start,
            field_label=field_label,
            minimum_amplitude_for_peak_phase=(
                minimum_amplitude_for_peak_phase
            ),
            absolute_render_specification=RenderSpecification(
                artist_method="pcolormesh",
                artist_kwargs={
                    "cmap": cmap_phase,
                    "vmin": float(phase_vmin),
                    "vmax": float(phase_vmax),
                },
            ),
            difference_render_specification=RenderSpecification(
                artist_method="pcolormesh",
                artist_kwargs={
                    "cmap": cmap_diff,
                    "vmin": -float(diff_limit),
                    "vmax": float(diff_limit),
                },
            ),
            left_panel_title="Peak Hour MONAN",
            right_panel_title="Peak Hour E3SM",
            difference_panel_title="Δ Phase (MONAN - E3SM)",
            absolute_colorbar_label="Peak hour (UTC)",
            difference_colorbar_label="Δ Phase",
            absolute_colorbar_kwargs={
                "orientation": "horizontal",
                "fraction": 0.045,
                "pad": 0.04,
                "ticks": np.arange(0, 24, 3),
            },
            difference_colorbar_kwargs={
                "orientation": "horizontal",
                "fraction": 0.045,
                "pad": 0.04,
                "ticks": np.arange(-12, 13, 3),
            },
            coastlines_kwargs={"linewidth": 0.8},
            borders_kwargs={"linewidth": 0.5},
            gridlines_kwargs={
                "draw_labels": True,
                "linewidth": 0.6,
                "alpha": 0.3,
                "x_inline": False,
                "y_inline": False,
            },
        )
    ]


def _build_legacy_monan_e3sm_diurnal_peak_phase_figure_specification(
    *,
    day_start: np.datetime64 = LEGACY_DIURNAL_PHASE_START_DATE,
) -> FigureSpecification:
    """Build the figure specification for the legacy diurnal peak phase."""
    day_label = np.datetime_as_string(day_start, unit="D")
    return FigureSpecification(
        nrows=1,
        ncols=3,
        suptitle=f"Diurnal Peak Phase of PBLH - {day_label}",
        figure_kwargs={"figsize": (18, 4.8), "constrained_layout": True},
    )


def _build_legacy_side_by_side_panel(
    *,
    adapter: DataAdapter,
    label: str,
    request: HorizontalFieldRequest,
    variable_name: str,
    cmap: str,
    field_vmin: float | None,
    field_vmax: float | None,
    show_left_labels: bool,
) -> MapPanelInput:
    """Build one legacy side-by-side map panel for MONAN or E3SM."""
    artist_kwargs = {"cmap": cmap}
    if field_vmin is not None:
        artist_kwargs["vmin"] = field_vmin
    if field_vmax is not None:
        artist_kwargs["vmax"] = field_vmax

    return MapPanelInput(
        layers=[
            MapLayerInput(
                adapter=adapter,
                request=request,
                variable_name=variable_name,
                render_specification=RenderSpecification(
                    artist_method="pcolormesh",
                    artist_kwargs=artist_kwargs,
                ),
            )
        ],
        axes_set_kwargs={
            "title": (
                f"{label} - {variable_name.upper()} "
                f"{np.datetime_as_string(request.times[0], unit='m')}"
            )
        },
        coastlines_kwargs={"linewidth": 0.8},
        borders_kwargs={"linewidth": 0.5},
        gridlines_kwargs={
            "draw_labels": True,
            "linewidth": 0.6,
            "alpha": 0.3,
            "linestyle": "--",
            "x_inline": False,
            "y_inline": False,
        },
        gridliner_attrs={
            "top_labels": False,
            "right_labels": False,
            "left_labels": show_left_labels,
        },
    )


def build_time_series_comparison_adapters(
    *,
    init_date: object = TIME_SERIES_COMPARISON_INIT_DATE,
) -> list[DataAdapter]:
    """Build adapters for the SHOC, MYNN, ERA5 and station comparison."""
    return [
        build_time_series_shoc_adapter(init_date=init_date),
        build_time_series_mynn_adapter(init_date=init_date),
        build_time_series_era5_adapter(init_date=init_date),
        build_time_series_goamazon_surface_station_adapter(
            init_date=init_date
        ),
    ]


def build_surface_nwp_reanalysis_time_series_comparison_inputs(
    *,
    adapters: Sequence[DataAdapter] | None = None,
    init_date: object = TIME_SERIES_COMPARISON_INIT_DATE,
    series_mode: TimeSeriesComparisonMode = "full",
    local_utc_offset_hours: int = TIME_SERIES_COMPARISON_UTC_OFFSET_HOURS,
    tick_step_hours: int = TIME_SERIES_COMPARISON_TICK_STEP_HOURS,
    hourly_mean_tick_step_hours: int = (
        TIME_SERIES_COMPARISON_HOURLY_MEAN_TICK_STEP_HOURS
    ),
) -> tuple[list[TimeSeriesPanelInput], FigureSpecification]:
    """Build panel inputs and figure layout for the 3-panel comparison."""
    _validate_time_series_comparison_mode(series_mode)
    start_time = np.datetime64(
        build_time_series_init_datetime_string(init_date),
        "ns",
    )
    if adapters is None:
        source_adapters = build_time_series_comparison_adapters(
            init_date=start_time
        )
    else:
        source_adapters = list(adapters)

    expected_source_count = len(TIME_SERIES_COMPARISON_SOURCE_STYLES)
    if len(source_adapters) != expected_source_count:
        raise ValueError(
            "Expected "
            f"{expected_source_count} adapters in SHOC/MYNN/ERA5/"
            "Observation order."
        )

    end_time_exclusive = start_time + np.timedelta64(
        TIME_SERIES_COMPARISON_DURATION_DAYS,
        "D",
    )
    gridded_request = build_time_series_comparison_gridded_request(
        init_date=start_time
    )
    gridded_cross_5_request = _build_cross_5_time_series_request(
        gridded_request
    )
    station_request = build_time_series_comparison_station_request(
        init_date=start_time
    )
    if series_mode == "hourly_mean":
        axes_calls = _build_hourly_mean_local_time_axes_calls(
            tick_step_hours=hourly_mean_tick_step_hours,
        )
    else:
        axes_calls = _build_local_time_axes_calls(
            start_time=start_time,
            end_time_exclusive=end_time_exclusive,
            utc_offset_hours=local_utc_offset_hours,
            tick_step_hours=tick_step_hours,
        )

    panels: list[TimeSeriesPanelInput] = []
    station_source_index = expected_source_count - 1
    panel_count = len(TIME_SERIES_COMPARISON_PANELS)
    for panel_index, (
        variable_name,
        y_axis_label,
    ) in enumerate(TIME_SERIES_COMPARISON_PANELS):
        layers: list[TimeSeriesLayerInput | PreparedTimeSeriesLayerInput] = []
        for source_index, (
            source_label,
            source_color,
        ) in enumerate(TIME_SERIES_COMPARISON_SOURCE_STYLES):
            adapter = source_adapters[source_index]
            render_specification = RenderSpecification(
                artist_method="plot",
                artist_kwargs={
                    "color": source_color,
                    "linewidth": 1.6,
                },
            )
            if source_index == station_source_index:
                raw_station_plot_data = adapter.to_time_series_plot_data(
                    variable_name=variable_name,
                    request=station_request,
                )
                prepared_plot_data = (
                    _build_hourly_nearest_station_plot_data(
                        raw_station_plot_data,
                        start_time=start_time,
                        end_time_exclusive=end_time_exclusive,
                    )
                )
                if series_mode == "hourly_mean":
                    prepared_plot_data = (
                        _build_hourly_mean_time_series_plot_data(
                            prepared_plot_data,
                            start_time=start_time,
                            end_time_exclusive=end_time_exclusive,
                            utc_offset_hours=local_utc_offset_hours,
                        )
                    )
                layers.append(
                    PreparedTimeSeriesLayerInput(
                        plot_data=prepared_plot_data,
                        render_specification=render_specification,
                        legend_label=source_label,
                    )
                )
            elif _is_monan_time_series_source(source_label):
                if series_mode == "hourly_mean":
                    raw_plot_data = adapter.to_time_series_plot_data(
                        variable_name=variable_name,
                        request=gridded_request,
                    )
                    (
                        prepared_plot_data,
                        std_band_plot_data,
                    ) = _build_hourly_mean_time_series_mean_std_plot_data(
                        raw_plot_data,
                        start_time=start_time,
                        end_time_exclusive=end_time_exclusive,
                        utc_offset_hours=local_utc_offset_hours,
                    )
                else:
                    (
                        prepared_plot_data,
                        std_band_plot_data,
                    ) = adapter.to_time_series_mean_std_plot_data(
                        variable_name=variable_name,
                        request=gridded_cross_5_request,
                    )
                _append_time_series_mean_std_layers(
                    layers,
                    mean_plot_data=prepared_plot_data,
                    std_band_plot_data=std_band_plot_data,
                    line_render_specification=render_specification,
                    source_color=source_color,
                    source_label=source_label,
                )
            elif series_mode == "hourly_mean":
                raw_plot_data = adapter.to_time_series_plot_data(
                    variable_name=variable_name,
                    request=gridded_request,
                )
                prepared_plot_data = _build_hourly_mean_time_series_plot_data(
                    raw_plot_data,
                    start_time=start_time,
                    end_time_exclusive=end_time_exclusive,
                    utc_offset_hours=local_utc_offset_hours,
                )
                layers.append(
                    PreparedTimeSeriesLayerInput(
                        plot_data=prepared_plot_data,
                        render_specification=render_specification,
                        legend_label=source_label,
                    )
                )
            else:
                layers.append(
                    TimeSeriesLayerInput(
                        adapter=adapter,
                        request=gridded_request,
                        variable_name=variable_name,
                        render_specification=render_specification,
                        legend_label=source_label,
                    )
                )

        panel_axes_set_kwargs = {
            "ylabel": y_axis_label,
            "ylim": TIME_SERIES_COMPARISON_Y_LIMITS[variable_name],
        }
        if panel_index == panel_count - 1:
            panel_axes_set_kwargs["xlabel"] = (
                "Local hour (GMT-4)"
                if series_mode == "hourly_mean"
                else "Local time (GMT-4)"
            )

        panels.append(
            TimeSeriesPanelInput(
                layers=layers,
                axes_set_kwargs=panel_axes_set_kwargs,
                grid_kwargs={"visible": True, "alpha": 0.3},
                legend_kwargs=(
                    {
                        "loc": "upper right",
                        "ncol": 4,
                    }
                    if panel_index == 0
                    else None
                ),
                axes_calls=[dict(axis_call) for axis_call in axes_calls],
            )
        )

    figsize = (13,8) if series_mode == "full" else (10, 8)
    figure_specification = FigureSpecification(
        nrows=3,
        ncols=1,
        suptitle=_build_time_series_comparison_title(init_date),
        suptitle_kwargs={"fontsize": 13},
        figure_kwargs={
            "figsize": figsize,
            "constrained_layout": True,
            "sharex": True,
        },
    )
    return panels, figure_specification


def _build_time_series_comparison_title(init_date: object) -> str:
    """Return the figure title for one time-series comparison case."""
    compact_date = normalize_time_series_init_date(init_date)
    init_date_label = (
        f"{compact_date[:4]}-{compact_date[4:6]}-{compact_date[6:]}"
    )
    return (
        "SHOC, MYNN, ERA5 and Observation Time-Series Comparison - "
        f"{build_time_series_season_label(init_date)} "
        f"(init {init_date_label})"
    )


def build_surface_nwp_reanalysis_time_series_comparison_figure(
    *,
    adapters: Sequence[DataAdapter] | None = None,
    init_date: object = TIME_SERIES_COMPARISON_INIT_DATE,
    series_mode: TimeSeriesComparisonMode = "full",
) -> Figure:
    """Build the 3-panel SHOC/MYNN/ERA5/station comparison figure."""
    panels, figure_specification = (
        build_surface_nwp_reanalysis_time_series_comparison_inputs(
            adapters=adapters,
            init_date=init_date,
            series_mode=series_mode,
        )
    )
    return plot_time_series_panels(
        panels=panels,
        figure_specification=figure_specification,
    )


def build_surface_flux_time_series_comparison_adapters(
    *,
    init_date: object = TIME_SERIES_COMPARISON_INIT_DATE,
) -> list[DataAdapter]:
    """Build adapters for the SHOC, MYNN, ERA5 and flux-tower comparison."""
    adapters = [
        build_surface_flux_time_series_shoc_adapter(init_date=init_date),
        build_surface_flux_time_series_mynn_adapter(init_date=init_date),
        build_surface_flux_time_series_era5_adapter(init_date=init_date),
    ]
    if _surface_flux_time_series_has_observation(init_date):
        adapters.append(
            build_surface_flux_goamazon_eddy_correlation_adapter(
                init_date=init_date
            )
        )
    return adapters


def build_surface_flux_time_series_comparison_inputs(
    *,
    adapters: Sequence[DataAdapter] | None = None,
    init_date: object = TIME_SERIES_COMPARISON_INIT_DATE,
    series_mode: TimeSeriesComparisonMode = "full",
    local_utc_offset_hours: int = TIME_SERIES_COMPARISON_UTC_OFFSET_HOURS,
    tick_step_hours: int = TIME_SERIES_COMPARISON_TICK_STEP_HOURS,
    hourly_mean_tick_step_hours: int = (
        TIME_SERIES_COMPARISON_HOURLY_MEAN_TICK_STEP_HOURS
    ),
) -> tuple[list[TimeSeriesPanelInput], FigureSpecification]:
    """Build panel inputs and figure layout for the surface-flux comparison."""
    _validate_time_series_comparison_mode(series_mode)
    start_time = np.datetime64(
        build_time_series_init_datetime_string(init_date),
        "ns",
    )
    source_styles = _build_surface_flux_time_series_source_styles(init_date)
    if adapters is None:
        source_adapters = build_surface_flux_time_series_comparison_adapters(
            init_date=start_time
        )
    else:
        source_adapters = list(adapters)

    expected_source_count = len(source_styles)
    if len(source_adapters) != expected_source_count:
        raise ValueError(
            "Expected "
            f"{expected_source_count} adapters in "
            f"{_format_source_labels_for_error(source_styles)} order."
        )

    end_time_exclusive = start_time + np.timedelta64(
        TIME_SERIES_COMPARISON_DURATION_DAYS,
        "D",
    )
    gridded_request = build_time_series_comparison_gridded_request(
        init_date=start_time
    )
    gridded_cross_5_request = _build_cross_5_time_series_request(
        gridded_request
    )
    station_request = build_time_series_comparison_station_request(
        init_date=start_time
    )
    if series_mode == "hourly_mean":
        axes_calls = _build_hourly_mean_local_time_axes_calls(
            tick_step_hours=hourly_mean_tick_step_hours,
        )
    else:
        axes_calls = _build_local_time_axes_calls(
            start_time=start_time,
            end_time_exclusive=end_time_exclusive,
            utc_offset_hours=local_utc_offset_hours,
            tick_step_hours=tick_step_hours,
        )

    panels: list[TimeSeriesPanelInput] = []
    observation_source_index = (
        expected_source_count - 1
        if _surface_flux_time_series_has_observation(init_date)
        else None
    )
    panel_count = len(SURFACE_FLUX_TIME_SERIES_COMPARISON_PANELS)
    for panel_index, (
        variable_name,
        y_axis_label,
    ) in enumerate(SURFACE_FLUX_TIME_SERIES_COMPARISON_PANELS):
        layers: list[TimeSeriesLayerInput | PreparedTimeSeriesLayerInput] = []
        for source_index, (
            source_label,
            source_color,
        ) in enumerate(source_styles):
            adapter = source_adapters[source_index]
            render_specification = RenderSpecification(
                artist_method="plot",
                artist_kwargs={
                    "color": source_color,
                    "linewidth": 1.6,
                },
            )
            if source_index == observation_source_index:
                raw_station_plot_data = adapter.to_time_series_plot_data(
                    variable_name=variable_name,
                    request=station_request,
                )
                prepared_plot_data = (
                    _build_hourly_nearest_station_plot_data(
                        raw_station_plot_data,
                        start_time=start_time,
                        end_time_exclusive=end_time_exclusive,
                    )
                )
                if series_mode == "hourly_mean":
                    prepared_plot_data = (
                        _build_hourly_mean_time_series_plot_data(
                            prepared_plot_data,
                            start_time=start_time,
                            end_time_exclusive=end_time_exclusive,
                            utc_offset_hours=local_utc_offset_hours,
                        )
                    )
                layers.append(
                    PreparedTimeSeriesLayerInput(
                        plot_data=prepared_plot_data,
                        render_specification=render_specification,
                        legend_label=source_label,
                    )
                )
            elif _is_monan_time_series_source(source_label):
                if series_mode == "hourly_mean":
                    raw_plot_data = adapter.to_time_series_plot_data(
                        variable_name=variable_name,
                        request=gridded_request,
                    )
                    (
                        prepared_plot_data,
                        std_band_plot_data,
                    ) = _build_hourly_mean_time_series_mean_std_plot_data(
                        raw_plot_data,
                        start_time=start_time,
                        end_time_exclusive=end_time_exclusive,
                        utc_offset_hours=local_utc_offset_hours,
                    )
                else:
                    (
                        prepared_plot_data,
                        std_band_plot_data,
                    ) = adapter.to_time_series_mean_std_plot_data(
                        variable_name=variable_name,
                        request=gridded_cross_5_request,
                    )
                _append_time_series_mean_std_layers(
                    layers,
                    mean_plot_data=prepared_plot_data,
                    std_band_plot_data=std_band_plot_data,
                    line_render_specification=render_specification,
                    source_color=source_color,
                    source_label=source_label,
                )
            elif series_mode == "hourly_mean":
                raw_plot_data = adapter.to_time_series_plot_data(
                    variable_name=variable_name,
                    request=gridded_request,
                )
                prepared_plot_data = _build_hourly_mean_time_series_plot_data(
                    raw_plot_data,
                    start_time=start_time,
                    end_time_exclusive=end_time_exclusive,
                    utc_offset_hours=local_utc_offset_hours,
                )
                layers.append(
                    PreparedTimeSeriesLayerInput(
                        plot_data=prepared_plot_data,
                        render_specification=render_specification,
                        legend_label=source_label,
                    )
                )
            else:
                layers.append(
                    TimeSeriesLayerInput(
                        adapter=adapter,
                        request=gridded_request,
                        variable_name=variable_name,
                        render_specification=render_specification,
                        legend_label=source_label,
                    )
                )

        panel_axes_set_kwargs = {"ylabel": y_axis_label}
        if panel_index == panel_count - 1:
            panel_axes_set_kwargs["xlabel"] = (
                "Local hour (GMT-4)"
                if series_mode == "hourly_mean"
                else "Local time (GMT-4)"
            )

        panels.append(
            TimeSeriesPanelInput(
                layers=layers,
                axes_set_kwargs=panel_axes_set_kwargs,
                grid_kwargs={"visible": True, "alpha": 0.3},
                legend_kwargs=(
                    {
                        "loc": "upper right",
                        "ncol": 4,
                    }
                    if panel_index == 0
                    else None
                ),
                axes_calls=[dict(axis_call) for axis_call in axes_calls],
            )
        )

    figsize = (13,8) if series_mode == "full" else (10, 8)
    figure_specification = FigureSpecification(
        nrows=2,
        ncols=1,
        suptitle=_build_surface_flux_time_series_comparison_title(init_date),
        suptitle_kwargs={"fontsize": 13},
        figure_kwargs={
            "figsize": figsize,
            "constrained_layout": True,
            "sharex": True,
        },
    )
    return panels, figure_specification


def _build_surface_flux_time_series_comparison_title(
    init_date: object,
) -> str:
    """Return the figure title for one surface-flux comparison case."""
    compact_date = normalize_time_series_init_date(init_date)
    source_styles = _build_surface_flux_time_series_source_styles(init_date)
    init_date_label = (
        f"{compact_date[:4]}-{compact_date[4:6]}-{compact_date[6:]}"
    )
    return (
        f"{_format_source_labels_for_title(source_styles)} Surface-Flux "
        "Time-Series Comparison - "
        f"{build_time_series_season_label(init_date)} "
        f"(init {init_date_label})"
    )


def build_surface_flux_time_series_comparison_figure(
    *,
    adapters: Sequence[DataAdapter] | None = None,
    init_date: object = TIME_SERIES_COMPARISON_INIT_DATE,
    series_mode: TimeSeriesComparisonMode = "full",
) -> Figure:
    """Build the 2-panel SHOC/MYNN/ERA5/flux-tower comparison figure."""
    panels, figure_specification = (
        build_surface_flux_time_series_comparison_inputs(
            adapters=adapters,
            init_date=init_date,
            series_mode=series_mode,
        )
    )
    return plot_time_series_panels(
        panels=panels,
        figure_specification=figure_specification,
    )


def build_vertical_profile_comparison_adapters(
    *,
    init_date: object = TIME_SERIES_COMPARISON_INIT_DATE,
) -> list[DataAdapter]:
    """Build SHOC, MYNN and ERA5 adapters for profile comparison."""
    return [
        build_vertical_profile_shoc_adapter(init_date=init_date),
        build_vertical_profile_mynn_adapter(init_date=init_date),
        build_vertical_profile_era5_adapter(init_date=init_date),
    ]


def build_vertical_profile_comparison_full_inputs(
    *,
    adapters: Sequence[DataAdapter] | None = None,
    init_date: object = TIME_SERIES_COMPARISON_INIT_DATE,
    forecast_day_index: int = 0,
) -> tuple[list[PanelInput], FigureSpecification]:
    """Build panel inputs and layout for one full-mode profile figure."""
    start_time = np.datetime64(
        build_time_series_init_datetime_string(init_date),
        "ns",
    )
    if adapters is None:
        source_adapters = build_vertical_profile_comparison_adapters(
            init_date=start_time
        )
    else:
        source_adapters = list(adapters)

    expected_source_count = 3
    if len(source_adapters) != expected_source_count:
        raise ValueError(
            "Expected 3 adapters in SHOC/MYNN/ERA5 order."
        )

    target_times = _build_vertical_profile_comparison_target_times(
        start_time=start_time,
        forecast_day_index=forecast_day_index,
    )
    radiosonde_adapters: list[DataAdapter] = []
    try:
        radiosonde_adapters = [
            build_goamazon_radiosonde_profile_adapter(
                target_time=target_time,
                init_date=init_date,
            )
            for target_time in target_times
        ]
        panels: list[PanelInput] = []
        display_target_times = target_times[
            list(VERTICAL_PROFILE_COMPARISON_DISPLAY_ROW_ORDER)
        ]
        for row_index, target_time in enumerate(display_target_times):
            nearest_request = build_vertical_profile_comparison_gridded_request(
                time_value=target_time,
            )
            cross_5_request = build_vertical_profile_comparison_gridded_request(
                time_value=target_time,
                point_sample_pattern="cross_5",
            )
            radiosonde_request = (
                build_vertical_profile_comparison_radiosonde_request(
                    time_value=target_time
                )
            )
            for column_index, (
                variable_name,
                panel_label,
                x_units,
            ) in enumerate(VERTICAL_PROFILE_COMPARISON_PANELS):
                layers = _build_vertical_profile_comparison_layers(
                    variable_name=variable_name,
                    source_adapters=source_adapters,
                    radiosonde_adapter=radiosonde_adapters[row_index],
                    nearest_request=nearest_request,
                    cross_5_request=cross_5_request,
                    radiosonde_request=radiosonde_request,
                )
                panels.append(
                    PanelInput(
                        layers=layers,
                        axes_set_kwargs=(
                            _build_vertical_profile_panel_axes_set_kwargs(
                                row_index=row_index,
                                column_index=column_index,
                                variable_name=variable_name,
                                target_time=target_time,
                                panel_label=panel_label,
                                x_units=x_units,
                            )
                        ),
                        grid_kwargs={"visible": True, "alpha": 0.3},
                        legend_kwargs=(
                            {"loc": "best", "fontsize": 8}
                            if row_index == 0 and column_index == 0
                            else None
                        ),
                        axes_calls=(
                            _build_vertical_profile_pressure_axes_calls()
                        ),
                    )
                )
    finally:
        for adapter in radiosonde_adapters:
            adapter.close()

    figure_specification = FigureSpecification(
        nrows=len(VERTICAL_PROFILE_COMPARISON_SYNOPTIC_HOURS),
        ncols=len(VERTICAL_PROFILE_COMPARISON_PANELS),
        suptitle=_build_vertical_profile_comparison_title(
            init_date=init_date,
            forecast_day_index=forecast_day_index,
        ),
        suptitle_kwargs={"fontsize": 13},
        figure_kwargs={
            "figsize": (13, 13),
            "constrained_layout": True,
            "sharey": True,
        },
    )
    return panels, figure_specification


def build_vertical_profile_comparison_full_figure(
    *,
    adapters: Sequence[DataAdapter] | None = None,
    init_date: object = TIME_SERIES_COMPARISON_INIT_DATE,
    forecast_day_index: int = 0,
) -> Figure:
    """Build one 4x3 full-mode vertical-profile comparison figure."""
    panels, figure_specification = build_vertical_profile_comparison_full_inputs(
        adapters=adapters,
        init_date=init_date,
        forecast_day_index=forecast_day_index,
    )
    return plot_vertical_profiles_panel(
        panels=panels,
        figure_specification=figure_specification,
    )


def _build_vertical_profile_comparison_layers(
    *,
    variable_name: str,
    source_adapters: Sequence[DataAdapter],
    radiosonde_adapter: DataAdapter,
    nearest_request: VerticalProfileRequest,
    cross_5_request: VerticalProfileRequest,
    radiosonde_request: VerticalProfileRequest,
) -> list[PreparedVerticalProfileLayerInput]:
    """Build prepared layers for one profile subplot."""
    layers: list[PreparedVerticalProfileLayerInput] = []
    for source_index, (
        source_label,
        source_color,
    ) in enumerate(VERTICAL_PROFILE_COMPARISON_SOURCE_STYLES):
        line_render_specification = _build_vertical_profile_line_render_spec(
            source_color
        )
        if _is_monan_time_series_source(source_label):
            mean_plot_data, std_band_plot_data = (
                source_adapters[source_index]
                .to_vertical_profile_mean_std_plot_data(
                    variable_name=variable_name,
                    request=cross_5_request,
                )
            )
            _append_vertical_profile_mean_std_layers(
                layers,
                mean_plot_data=mean_plot_data,
                std_band_plot_data=std_band_plot_data,
                line_render_specification=line_render_specification,
                source_color=source_color,
                source_label=source_label,
            )
        elif source_label == "ERA5":
            plot_data = source_adapters[source_index].to_vertical_profile_plot_data(
                variable_name=variable_name,
                request=nearest_request,
            )
            layers.append(
                PreparedVerticalProfileLayerInput(
                    plot_data=plot_data,
                    render_specification=line_render_specification,
                    legend_label=source_label,
                )
            )
        else:
            plot_data = radiosonde_adapter.to_vertical_profile_plot_data(
                variable_name=variable_name,
                request=radiosonde_request,
            )
            layers.append(
                PreparedVerticalProfileLayerInput(
                    plot_data=plot_data,
                    render_specification=line_render_specification,
                    legend_label=source_label,
                )
            )

    return layers


def _append_vertical_profile_mean_std_layers(
    layers: list[PreparedVerticalProfileLayerInput],
    *,
    mean_plot_data: VerticalProfilePlotData,
    std_band_plot_data: VerticalProfileBandPlotData,
    line_render_specification: RenderSpecification,
    source_color: str,
    source_label: str,
) -> None:
    """Append std band and mean line profile layers in render order."""
    layers.append(
        PreparedVerticalProfileLayerInput(
            plot_data=std_band_plot_data,
            render_specification=_build_vertical_profile_std_band_render_spec(
                source_color
            ),
        )
    )
    layers.append(
        PreparedVerticalProfileLayerInput(
            plot_data=mean_plot_data,
            render_specification=line_render_specification,
            legend_label=source_label,
        )
    )


def _build_vertical_profile_line_render_spec(
    source_color: str,
) -> RenderSpecification:
    """Build a standard vertical-profile line render spec."""
    return RenderSpecification(
        artist_method="plot",
        artist_kwargs={
            "color": source_color,
            "linewidth": 1.4,
        },
    )


def _build_vertical_profile_std_band_render_spec(
    source_color: str,
) -> RenderSpecification:
    """Build the unlabeled render spec for a profile std band."""
    return RenderSpecification(
        artist_method="fill_betweenx",
        artist_kwargs={
            "color": source_color,
            "alpha": VERTICAL_PROFILE_STD_BAND_ALPHA,
            "linewidth": 0.0,
        },
    )


def _build_vertical_profile_panel_axes_set_kwargs(
    *,
    row_index: int,
    column_index: int,
    variable_name: str,
    target_time: np.datetime64,
    panel_label: str,
    x_units: str,
) -> dict[str, object]:
    """Build axis labels for one profile subplot."""
    axes_set_kwargs: dict[str, object] = {
        "xlim": VERTICAL_PROFILE_COMPARISON_X_LIMITS[variable_name],
    }
    if row_index == 0:
        axes_set_kwargs["title"] = panel_label
    if column_index == 0:
        axes_set_kwargs["ylabel"] = (
            f"{_format_synoptic_local_hour_label(target_time)} LT\n"
            "Pressure [hPa]"
        )
    if row_index == len(VERTICAL_PROFILE_COMPARISON_SYNOPTIC_HOURS) - 1:
        axes_set_kwargs["xlabel"] = f"{panel_label} [{x_units}]"

    return axes_set_kwargs


def _build_vertical_profile_pressure_axes_calls() -> list[dict[str, object]]:
    """Return pressure-axis calls for the 1000-700 hPa profile layer."""
    return [
        {"method": "invert_yaxis"},
        {
            "method": "set_ylim",
            "args": [
                VERTICAL_PROFILE_COMPARISON_PRESSURE_BOTTOM_HPA,
                VERTICAL_PROFILE_COMPARISON_PRESSURE_TOP_HPA,
            ],
        },
        {
            "method": "set_yticks",
            "args": [VERTICAL_PROFILE_COMPARISON_PRESSURE_TICKS_HPA],
        },
    ]


def _build_vertical_profile_comparison_target_times(
    *,
    start_time: np.datetime64,
    forecast_day_index: int,
) -> np.ndarray:
    """Return the four target synoptic times for one forecast day."""
    if forecast_day_index < 0 or forecast_day_index >= (
        TIME_SERIES_COMPARISON_DURATION_DAYS
    ):
        raise ValueError(
            "forecast_day_index must be between 0 and "
            f"{TIME_SERIES_COMPARISON_DURATION_DAYS - 1}."
        )

    day_start = start_time + np.timedelta64(forecast_day_index, "D")
    return np.asarray(
        [
            day_start + np.timedelta64(hour, "h")
            for hour in VERTICAL_PROFILE_COMPARISON_SYNOPTIC_HOURS
        ],
        dtype="datetime64[ns]",
    )


def _build_vertical_profile_comparison_title(
    *,
    init_date: object,
    forecast_day_index: int,
) -> str:
    """Return the figure title for one full-mode profile comparison."""
    compact_date = normalize_time_series_init_date(init_date)
    init_date_label = (
        f"{compact_date[:4]}-{compact_date[4:6]}-{compact_date[6:]}"
    )
    start_time = np.datetime64(
        build_time_series_init_datetime_string(init_date),
        "ns",
    )
    forecast_day = start_time + np.timedelta64(forecast_day_index, "D")
    forecast_day_label = np.datetime_as_string(forecast_day, unit="D")
    return (
        "SHOC, MYNN, ERA5 and Radiosonde Vertical-Profile Comparison - "
        f"{build_time_series_season_label(init_date)} "
        f"(init {init_date_label}, {forecast_day_label}, "
        f"{VERTICAL_PROFILE_COMPARISON_POINT_LAT:.2f}°, "
        f"{VERTICAL_PROFILE_COMPARISON_POINT_LON:.1f}°)"
    )


def _format_synoptic_local_hour_label(time_value: np.datetime64) -> str:
    """Return a two-digit local hour for one UTC target datetime."""
    utc_hour_value = (
        np.datetime64(time_value, "h").astype("datetime64[h]").astype(int) % 24
    )
    local_hour_value = (
        utc_hour_value + VERTICAL_PROFILE_COMPARISON_UTC_OFFSET_HOURS
    ) % 24
    return f"{int(local_hour_value):02d}"


def _surface_flux_time_series_has_observation(init_date: object) -> bool:
    """Return whether the surface-flux case has observation files."""
    compact_date = normalize_time_series_init_date(init_date)
    return compact_date not in SURFACE_FLUX_TIME_SERIES_NO_OBSERVATION_INIT_DATES


def _build_surface_flux_time_series_source_styles(
    init_date: object,
) -> tuple[tuple[str, str], ...]:
    """Return source styles for one surface-flux comparison case."""
    if _surface_flux_time_series_has_observation(init_date):
        return TIME_SERIES_COMPARISON_SOURCE_STYLES
    return TIME_SERIES_COMPARISON_SOURCE_STYLES[:-1]


def _format_source_labels_for_title(
    source_styles: Sequence[tuple[str, str]],
) -> str:
    """Return source labels formatted for a figure title."""
    labels = [source_label for source_label, _ in source_styles]
    if len(labels) == 1:
        return labels[0]
    if len(labels) == 2:
        return " and ".join(labels)
    return f"{', '.join(labels[:-1])} and {labels[-1]}"


def _format_source_labels_for_error(
    source_styles: Sequence[tuple[str, str]],
) -> str:
    """Return source labels formatted for adapter-order errors."""
    return "/".join(source_label for source_label, _ in source_styles)


def _validate_time_series_comparison_mode(
    series_mode: str,
) -> None:
    """Validate the time-series comparison mode."""
    if series_mode not in {"full", "hourly_mean"}:
        raise ValueError(
            "series_mode must be either 'full' or 'hourly_mean'."
        )


def _build_local_time_axes_calls(
    *,
    start_time: np.datetime64,
    end_time_exclusive: np.datetime64,
    utc_offset_hours: int,
    tick_step_hours: int,
) -> list[dict[str, object]]:
    """Build x-axis calls that display GMT-offset labels over UTC values."""
    tick_times = np.arange(
        start_time,
        end_time_exclusive,
        np.timedelta64(tick_step_hours, "h"),
    ).astype("datetime64[ns]")
    final_tick_time = (
        end_time_exclusive - np.timedelta64(1, "h")
    ).astype("datetime64[ns]")
    if final_tick_time > tick_times[-1]:
        tick_times = np.append(tick_times, final_tick_time)

    local_times = tick_times + np.timedelta64(utc_offset_hours, "h")
    tick_labels = [
        np.datetime_as_string(local_time, unit="h").replace("T", " ")
        for local_time in local_times
    ]
    return [
        {"method": "set_xticks", "args": [tick_times]},
        {"method": "set_xticklabels", "args": [tick_labels]},
        {
            "method": "set_xlim",
            "args": [
                start_time,
                end_time_exclusive - np.timedelta64(1, "ns"),
            ],
        },
    ]


def _build_hourly_mean_local_time_axes_calls(
    *,
    tick_step_hours: int,
) -> list[dict[str, object]]:
    """Build x-axis calls for hourly means indexed by local hour."""
    tick_hours = np.arange(0, 24, tick_step_hours)
    tick_labels = [f"{int(hour):02d}" for hour in tick_hours]
    return [
        {"method": "set_xticks", "args": [tick_hours]},
        {"method": "set_xticklabels", "args": [tick_labels]},
        {"method": "set_xlim", "args": [0, 23]},
    ]


def _build_cross_5_time_series_request(
    request: TimeSeriesRequest,
) -> TimeSeriesRequest:
    """Return a copy of a point request that samples the 5-point cross."""
    return replace(request, point_sample_pattern="cross_5")


def _is_monan_time_series_source(source_label: str) -> bool:
    """Return whether a source should receive MONAN std-band treatment."""
    return source_label in TIME_SERIES_COMPARISON_MONAN_SOURCE_LABELS


def _append_time_series_mean_std_layers(
    layers: list[TimeSeriesLayerInput | PreparedTimeSeriesLayerInput],
    *,
    mean_plot_data: TimeSeriesPlotData,
    std_band_plot_data: TimeSeriesBandPlotData,
    line_render_specification: RenderSpecification,
    source_color: str,
    source_label: str,
) -> None:
    """Append std band and mean line layers in render order."""
    layers.append(
        PreparedTimeSeriesLayerInput(
            plot_data=std_band_plot_data,
            render_specification=_build_time_series_std_band_render_spec(
                source_color
            ),
        )
    )
    layers.append(
        PreparedTimeSeriesLayerInput(
            plot_data=mean_plot_data,
            render_specification=line_render_specification,
            legend_label=source_label,
        )
    )


def _build_time_series_std_band_render_spec(
    source_color: str,
) -> RenderSpecification:
    """Build the unlabeled render spec for a standard-deviation band."""
    return RenderSpecification(
        artist_method="fill_between",
        artist_kwargs={
            "color": source_color,
            "alpha": TIME_SERIES_COMPARISON_STD_BAND_ALPHA,
            "linewidth": 0.0,
        },
    )


def _build_hourly_nearest_station_plot_data(
    plot_data: TimeSeriesPlotData,
    *,
    start_time: np.datetime64,
    end_time_exclusive: np.datetime64,
) -> TimeSeriesPlotData:
    """Return station data reduced to hourly nearest samples."""
    source_times = np.asarray(plot_data.times, dtype="datetime64[ns]")
    source_values = np.asarray(plot_data.values)
    if source_times.size == 0:
        raise ValueError("Station time series is empty for this request.")

    in_window = (
        (source_times >= start_time)
        & (source_times < end_time_exclusive)
    )
    if not np.any(in_window):
        raise ValueError(
            "Station time series has no samples within the requested "
            "comparison interval."
        )

    window_times = source_times[in_window]
    window_values = source_values[in_window]
    sort_indices = np.argsort(window_times)
    window_times = window_times[sort_indices]
    window_values = window_values[sort_indices]

    hourly_times = np.arange(
        start_time,
        end_time_exclusive,
        np.timedelta64(1, "h"),
    ).astype("datetime64[ns]")
    nearest_indices = _select_nearest_time_indices(
        source_times=window_times,
        target_times=hourly_times,
    )
    hourly_values = window_values[nearest_indices]

    hourly_draw_mask = None
    if plot_data.draw_mask is not None:
        source_draw_mask = np.asarray(plot_data.draw_mask)[in_window]
        source_draw_mask = source_draw_mask[sort_indices]
        hourly_draw_mask = source_draw_mask[nearest_indices]

    return TimeSeriesPlotData(
        label=plot_data.label,
        times=hourly_times,
        values=np.asarray(hourly_values),
        units=plot_data.units,
        site_label=plot_data.site_label,
        vertical_label=plot_data.vertical_label,
        value_axis=plot_data.value_axis,
        draw_mask=hourly_draw_mask,
    )


def _build_hourly_mean_time_series_plot_data(
    plot_data: TimeSeriesPlotData,
    *,
    start_time: np.datetime64,
    end_time_exclusive: np.datetime64,
    utc_offset_hours: int,
) -> TimeSeriesPlotData:
    """Return 24 hourly means indexed by local hour.

    The source timestamps stay in UTC for grouping. Each UTC-hour mean is
    placed on the corresponding local-hour axis position.
    """
    source_times = np.asarray(plot_data.times, dtype="datetime64[ns]")
    source_values = np.asarray(plot_data.values, dtype=float)
    if source_times.size != source_values.size:
        raise ValueError(
            "Time-series hourly means require matching time and value sizes."
        )

    in_window = (
        (source_times >= start_time)
        & (source_times < end_time_exclusive)
    )
    if not np.any(in_window):
        raise ValueError(
            "Time series has no samples within the requested comparison "
            "interval."
        )

    window_times = source_times[in_window]
    window_values = source_values[in_window]
    local_hours = _compute_local_hours(window_times, utc_offset_hours)
    hourly_values = np.full(24, np.nan, dtype=float)
    for hour in range(24):
        hour_values = window_values[local_hours == hour]
        valid_values = hour_values[~np.isnan(hour_values)]
        if valid_values.size > 0:
            hourly_values[hour] = float(np.mean(valid_values))

    hourly_draw_mask = None
    if plot_data.draw_mask is not None:
        source_draw_mask = np.asarray(plot_data.draw_mask)[in_window]
        hourly_draw_mask = np.zeros(24, dtype=bool)
        for hour in range(24):
            hour_mask = local_hours == hour
            if np.any(hour_mask):
                hourly_draw_mask[hour] = bool(
                    np.any(source_draw_mask[hour_mask])
                )

    return TimeSeriesPlotData(
        label=plot_data.label,
        times=np.arange(24),
        values=hourly_values,
        units=plot_data.units,
        site_label=plot_data.site_label,
        vertical_label=plot_data.vertical_label,
        value_axis=plot_data.value_axis,
        draw_mask=hourly_draw_mask,
    )


def _build_hourly_mean_time_series_mean_std_plot_data(
    plot_data: TimeSeriesPlotData,
    *,
    start_time: np.datetime64,
    end_time_exclusive: np.datetime64,
    utc_offset_hours: int,
) -> tuple[TimeSeriesPlotData, TimeSeriesBandPlotData]:
    """Return hourly means plus temporal std bands by local hour."""
    source_times = np.asarray(plot_data.times, dtype="datetime64[ns]")
    source_values = np.asarray(plot_data.values, dtype=float)
    if source_times.size != source_values.size:
        raise ValueError(
            "Time-series hourly statistics require matching time and "
            "value sizes."
        )

    in_window = (
        (source_times >= start_time)
        & (source_times < end_time_exclusive)
    )
    if not np.any(in_window):
        raise ValueError(
            "Time series has no samples within the requested comparison "
            "interval."
        )

    window_times = source_times[in_window]
    window_values = source_values[in_window]
    local_hours = _compute_local_hours(window_times, utc_offset_hours)
    hourly_values = np.full(24, np.nan, dtype=float)
    hourly_std_values = np.full(24, np.nan, dtype=float)
    for hour in range(24):
        hour_values = window_values[local_hours == hour]
        valid_values = hour_values[~np.isnan(hour_values)]
        if valid_values.size > 0:
            hourly_values[hour] = float(np.mean(valid_values))
            hourly_std_values[hour] = float(np.std(valid_values, ddof=0))

    hourly_draw_mask = None
    if plot_data.draw_mask is not None:
        source_draw_mask = np.asarray(plot_data.draw_mask)[in_window]
        hourly_draw_mask = np.zeros(24, dtype=bool)
        for hour in range(24):
            hour_mask = local_hours == hour
            if np.any(hour_mask):
                hourly_draw_mask[hour] = bool(
                    np.any(source_draw_mask[hour_mask])
                )

    mean_plot_data = TimeSeriesPlotData(
        label=plot_data.label,
        times=np.arange(24),
        values=hourly_values,
        units=plot_data.units,
        site_label=plot_data.site_label,
        vertical_label=plot_data.vertical_label,
        value_axis=plot_data.value_axis,
        draw_mask=hourly_draw_mask,
    )
    band_plot_data = TimeSeriesBandPlotData(
        label=plot_data.label,
        times=np.arange(24),
        lower_values=hourly_values - hourly_std_values,
        upper_values=hourly_values + hourly_std_values,
        units=plot_data.units,
        site_label=plot_data.site_label,
        vertical_label=plot_data.vertical_label,
        value_axis=plot_data.value_axis,
        draw_mask=hourly_draw_mask,
    )
    return mean_plot_data, band_plot_data


def _compute_local_hours(
    times: np.ndarray,
    utc_offset_hours: int,
) -> np.ndarray:
    """Return local hour-of-day values for UTC datetime64 timestamps."""
    utc_hours = (times.astype("datetime64[h]").astype(np.int64) % 24)
    return ((utc_hours + utc_offset_hours) % 24).astype(int)


def _select_nearest_time_indices(
    *,
    source_times: np.ndarray,
    target_times: np.ndarray,
) -> np.ndarray:
    """Return source indices that are nearest to each target timestamp."""
    source_int = source_times.astype("datetime64[ns]").astype(np.int64)
    target_int = target_times.astype("datetime64[ns]").astype(np.int64)
    insertion_points = np.searchsorted(source_int, target_int, side="left")
    right_indices = np.clip(
        insertion_points,
        0,
        source_int.size - 1,
    )
    left_indices = np.clip(right_indices - 1, 0, source_int.size - 1)
    left_distance = np.abs(target_int - source_int[left_indices])
    right_distance = np.abs(source_int[right_indices] - target_int)
    choose_left = left_distance <= right_distance
    return np.where(choose_left, left_indices, right_indices)
