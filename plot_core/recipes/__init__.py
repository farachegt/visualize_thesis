"""High-level plotting recipes built on top of the reusable core."""

from .cross_sections import (
    CrossSectionLayerInput,
    CrossSectionPanelInput,
    plot_cross_section_panels,
)
from .maps import (
    MapComparisonRowInput,
    MapComparisonSourceInput,
    MapLayerInput,
    MapPanelInput,
    PreparedMapLayerInput,
    plot_map_comparison_rows,
    plot_map_panels,
    plot_paper_grade_panel,
)
from .profiles import (
    PanelInput,
    VerticalProfileLayerInput,
    plot_vertical_profiles_panel,
)
from .time_vertical import (
    HourlyMeanLayerInput,
    HourlyMeanPanelInput,
    HourlyMeanTkeColumnInput,
    plot_hourly_mean_panels,
    plot_vertical_profile_tke_hourly_mean,
)

__all__ = [
    "CrossSectionLayerInput",
    "CrossSectionPanelInput",
    "HourlyMeanLayerInput",
    "HourlyMeanPanelInput",
    "HourlyMeanTkeColumnInput",
    "MapComparisonRowInput",
    "MapComparisonSourceInput",
    "MapLayerInput",
    "MapPanelInput",
    "PreparedMapLayerInput",
    "PanelInput",
    "plot_cross_section_panels",
    "plot_hourly_mean_panels",
    "plot_map_comparison_rows",
    "plot_map_panels",
    "plot_paper_grade_panel",
    "VerticalProfileLayerInput",
    "plot_vertical_profile_tke_hourly_mean",
    "plot_vertical_profiles_panel",
]
