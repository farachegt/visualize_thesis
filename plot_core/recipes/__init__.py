"""High-level plotting recipes built on top of the reusable core."""

from .cross_sections import (
    CrossSectionLayerInput,
    CrossSectionPanelInput,
    plot_cross_section_panels,
)
from .diurnal import (
    DiurnalAmplitudeRowInput,
    DiurnalAmplitudeSourceInput,
    DiurnalPeakPhaseRowInput,
    DiurnalPeakPhaseSourceInput,
    plot_diurnal_amplitude_rows,
    plot_diurnal_cycle_amplitude_pblh,
    plot_diurnal_peak_phase_pblh,
    plot_diurnal_peak_phase_rows,
)
from .diurnal_extrema_matrix import (
    DiurnalExtremaMatrixRowInput,
    DiurnalExtremaMatrixSourceInput,
    plot_diurnal_extrema_matrix_rows,
)
from .diurnal_matrix import (
    DiurnalAmplitudeMatrixRowInput,
    DiurnalAmplitudeMatrixSourceInput,
    plot_diurnal_amplitude_matrix_rows,
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
    plot_precipitation_monan,
)
from .profiles import (
    PanelInput,
    PreparedVerticalProfileLayerInput,
    VerticalProfileCloudHatchInput,
    VerticalProfileSourceInput,
    VerticalProfileLayerInput,
    plot_vertical_profiles_panel_at_point,
    plot_vertical_profiles_panel,
)
from .time_series import (
    PreparedTimeSeriesLayerInput,
    TimeSeriesLayerInput,
    TimeSeriesPanelInput,
    plot_time_series_panels,
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
    "DiurnalAmplitudeRowInput",
    "DiurnalAmplitudeSourceInput",
    "DiurnalAmplitudeMatrixRowInput",
    "DiurnalAmplitudeMatrixSourceInput",
    "DiurnalPeakPhaseRowInput",
    "DiurnalPeakPhaseSourceInput",
    "DiurnalExtremaMatrixRowInput",
    "DiurnalExtremaMatrixSourceInput",
    "HourlyMeanLayerInput",
    "HourlyMeanPanelInput",
    "HourlyMeanTkeColumnInput",
    "MapComparisonRowInput",
    "MapComparisonSourceInput",
    "MapLayerInput",
    "MapPanelInput",
    "PreparedMapLayerInput",
    "PreparedTimeSeriesLayerInput",
    "PanelInput",
    "PreparedVerticalProfileLayerInput",
    "TimeSeriesLayerInput",
    "TimeSeriesPanelInput",
    "VerticalProfileCloudHatchInput",
    "VerticalProfileSourceInput",
    "plot_cross_section_panels",
    "plot_diurnal_amplitude_rows",
    "plot_diurnal_amplitude_matrix_rows",
    "plot_diurnal_cycle_amplitude_pblh",
    "plot_diurnal_extrema_matrix_rows",
    "plot_diurnal_peak_phase_pblh",
    "plot_diurnal_peak_phase_rows",
    "plot_hourly_mean_panels",
    "plot_map_comparison_rows",
    "plot_map_panels",
    "plot_paper_grade_panel",
    "plot_precipitation_monan",
    "plot_time_series_panels",
    "VerticalProfileLayerInput",
    "plot_vertical_profiles_panel_at_point",
    "plot_vertical_profile_tke_hourly_mean",
    "plot_vertical_profiles_panel",
]
