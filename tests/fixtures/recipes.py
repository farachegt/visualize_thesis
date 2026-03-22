from __future__ import annotations

from typing import Sequence

import numpy as np
from matplotlib.figure import Figure

from plot_core.adapter import DataAdapter
from plot_core.recipes.cross_sections import (
    CrossSectionLayerInput,
    CrossSectionPanelInput,
    plot_cross_section_panels,
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
    VerticalProfileLayerInput,
    plot_vertical_profiles_panel,
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
    build_legacy_e3sm_adapter,
    build_legacy_monan_e3sm_adapter,
    build_legacy_mynn_monan_adapter,
    build_legacy_shoc_monan_adapter,
    build_model_u_adapter,
    build_radiosonde_u_adapter,
)
from .requests import (
    build_legacy_chile_coast_vertical_profile_request,
    build_model_vertical_profile_request,
    build_radiosonde_vertical_profile_request,
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
LEGACY_HOURLY_MEAN_REGION_NAME = "African Desert"
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
LEGACY_PAPER_GRADE_LABELS = ("PBLH", "SHF/HFX")
LEGACY_PAPER_GRADE_VMINS = (0.0, -200.0)
LEGACY_PAPER_GRADE_VMAXS = (3000.0, 500.0)
LEGACY_PAPER_GRADE_CMAPS_ABS = ("turbo", "Spectral_r")
LEGACY_PAPER_GRADE_CMAP_DIFF = "RdBu_r"
LEGACY_PAPER_GRADE_DIFF_LIMITS = (1500.0, 200.0)


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
                    "ylabel": "Pressure (Pa)",
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
        f"{abs(point_lon):.2f}°{longitude_hemisphere}, UTC+0)"
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
    ) in zip(
        variable_pairs,
        labels,
        vmins,
        vmaxs,
        cmaps_abs,
        diff_limits,
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
                difference_panel_title=(
                    f"Delta {label} = MONAN - E3SM"
                ),
                absolute_colorbar_label=label,
                difference_colorbar_label=f"Delta {label}",
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
        suptitle=f"MONAN vs E3SM - {time_label}",
        figure_kwargs={
            "figsize": (18, max(4 * row_count, 6)),
            "constrained_layout": True,
        },
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
