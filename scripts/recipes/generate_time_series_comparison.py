from __future__ import annotations

import argparse
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def generate_time_series_comparison_figure(
    output_path: Path | None = None,
    mode: str = "full",
) -> Path:
    """Generate and save the 3-panel SHOC/MYNN/ERA5/station comparison."""
    import matplotlib.pyplot as plt

    from plot_core.scenarios import (
        OUTPUT_DIR,
        build_surface_nwp_reanalysis_time_series_comparison_figure,
        build_time_series_comparison_adapters,
    )

    series_mode = _normalize_mode(mode)
    final_output_path = output_path or _default_output_path(
        OUTPUT_DIR,
        series_mode,
    )
    final_output_path.parent.mkdir(parents=True, exist_ok=True)

    adapters = build_time_series_comparison_adapters()
    try:
        figure = (
            build_surface_nwp_reanalysis_time_series_comparison_figure(
                adapters=adapters,
                series_mode=series_mode,
            )
        )
        figure.savefig(final_output_path, dpi=150, bbox_inches="tight")
        plt.close(figure)
    finally:
        for adapter in adapters:
            adapter.close()

    return final_output_path


def _normalize_mode(mode: str) -> str:
    """Return the scenario mode name used by the builder."""
    if mode == "hourly-mean":
        return "hourly_mean"
    if mode in {"full", "hourly_mean"}:
        return mode
    raise ValueError("mode must be 'full' or 'hourly-mean'.")


def _default_output_path(output_dir: Path, mode: str) -> Path:
    """Return the default output path for one plot mode."""
    if mode == "hourly_mean":
        return output_dir / "time_series_comparison_hourly_mean.png"
    return output_dir / "time_series_comparison.png"


def main() -> None:
    """Generate the time-series comparison figure and print its path."""
    parser = argparse.ArgumentParser(
        description=(
            "Generate the SHOC/MYNN/ERA5/Observation time-series "
            "comparison figure."
        )
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help=(
            "Output file path. Default depends on --mode and writes under "
            "tests/output/."
        ),
    )
    parser.add_argument(
        "--mode",
        choices=("full", "hourly-mean"),
        default="full",
        help=(
            "Plot mode. Use 'full' for the 5-day series or "
            "'hourly-mean' for UTC-hour means over the 5-day window."
        ),
    )
    args = parser.parse_args()

    saved_path = generate_time_series_comparison_figure(
        output_path=args.output,
        mode=args.mode,
    )
    print(f"saved: {saved_path}")


if __name__ == "__main__":
    main()
