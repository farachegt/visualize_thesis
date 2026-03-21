from __future__ import annotations

from typing import Sequence

from matplotlib.figure import Figure

from plot_core.adapter import DataAdapter
from plot_core.recipes.profiles import (
    PanelInput,
    VerticalProfileLayerInput,
    plot_vertical_profiles_panel,
)
from plot_core.rendering import FigureSpecification, RenderSpecification
from plot_core.requests import VerticalProfileRequest

from .adapters import (
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
