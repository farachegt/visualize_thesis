from __future__ import annotations

from pathlib import Path
import sys

import matplotlib.pyplot as plt

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from plot_core.scenarios import (
    OUTPUT_DIR,
    build_surface_nwp_reanalysis_time_series_comparison_figure,
    build_time_series_comparison_adapters,
)


def generate_time_series_comparison_figure(
    output_path: Path | None = None,
) -> Path:
    """Generate and save the 3-panel SHOC/MYNN/ERA5/station comparison."""
    final_output_path = output_path or (
        OUTPUT_DIR / "time_series_comparison.png"
    )
    final_output_path.parent.mkdir(parents=True, exist_ok=True)

    adapters = build_time_series_comparison_adapters()
    try:
        figure = (
            build_surface_nwp_reanalysis_time_series_comparison_figure(
                adapters=adapters
            )
        )
        figure.savefig(final_output_path, dpi=150, bbox_inches="tight")
        plt.close(figure)
    finally:
        for adapter in adapters:
            adapter.close()

    return final_output_path


def main() -> None:
    """Generate the time-series comparison figure and print its path."""
    saved_path = generate_time_series_comparison_figure()
    print(f"saved: {saved_path}")


if __name__ == "__main__":
    main()
