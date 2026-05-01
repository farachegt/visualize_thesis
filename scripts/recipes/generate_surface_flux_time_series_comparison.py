from __future__ import annotations

import argparse
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

SUPPORTED_INIT_DATES = ("20141002", "20140802", "20140216")
DEFAULT_INIT_DATE = "20141002"


def generate_surface_flux_time_series_comparison_figure(
    output_path: Path | None = None,
    mode: str = "full",
    init_date: str = DEFAULT_INIT_DATE,
) -> Path:
    """Generate and save the SHOC/MYNN/ERA5/flux-tower comparison."""
    import matplotlib.pyplot as plt

    from plot_core.scenarios import (
        OUTPUT_DIR,
        build_surface_flux_time_series_comparison_adapters,
        build_surface_flux_time_series_comparison_figure,
        build_time_series_season_label,
    )

    series_mode = _normalize_mode(mode)
    final_output_path = output_path or _default_output_path(
        OUTPUT_DIR,
        series_mode,
        build_time_series_season_label(init_date),
    )
    final_output_path.parent.mkdir(parents=True, exist_ok=True)

    adapters = build_surface_flux_time_series_comparison_adapters(
        init_date=init_date
    )
    try:
        figure = build_surface_flux_time_series_comparison_figure(
            adapters=adapters,
            init_date=init_date,
            series_mode=series_mode,
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


def _default_output_path(
    output_dir: Path,
    mode: str,
    season_label: str,
) -> Path:
    """Return the default output path for one season and plot mode."""
    season_slug = season_label.lower().replace(" ", "_")
    return output_dir / f"time_series_comparison_sf_{season_slug}_{mode}.png"


def main() -> None:
    """Generate the surface-flux time-series comparison and print its path."""
    parser = argparse.ArgumentParser(
        description=(
            "Generate the SHOC/MYNN/ERA5/Observation surface-flux "
            "time-series comparison figure."
        )
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help=(
            "Output file path. Default uses the selected season and mode "
            "under tests/output/."
        ),
    )
    parser.add_argument(
        "--mode",
        choices=("full", "hourly-mean"),
        default="full",
        help=(
            "Plot mode. Use 'full' for the 5-day series or "
            "'hourly-mean' for local-hour means over the 5-day window."
        ),
    )
    parser.add_argument(
        "--init-date",
        choices=SUPPORTED_INIT_DATES,
        default=DEFAULT_INIT_DATE,
        help="Forecast initialization date selector.",
    )
    args = parser.parse_args()

    saved_path = generate_surface_flux_time_series_comparison_figure(
        output_path=args.output,
        mode=args.mode,
        init_date=args.init_date,
    )
    print(f"saved: {saved_path}")


if __name__ == "__main__":
    main()
