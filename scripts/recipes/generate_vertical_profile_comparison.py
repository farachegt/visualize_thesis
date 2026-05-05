from __future__ import annotations

import argparse
from datetime import datetime, timedelta
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

SUPPORTED_INIT_DATES = ("20141002", "20140802", "20140216")
DEFAULT_INIT_DATE = "20141002"
FORECAST_DAYS = 5


def generate_vertical_profile_comparison_figures(
    output_dir: Path | None = None,
    init_date: str = DEFAULT_INIT_DATE,
) -> list[Path]:
    """Generate and save full-mode synoptic vertical-profile comparisons."""
    import matplotlib.pyplot as plt

    from plot_core.scenarios import (
        OUTPUT_DIR,
        build_time_series_season_label,
        build_vertical_profile_comparison_adapters,
        build_vertical_profile_comparison_full_figure,
    )

    season_label = build_time_series_season_label(init_date)
    season_slug = _slugify(season_label)
    final_output_dir = output_dir or OUTPUT_DIR
    final_output_dir.mkdir(parents=True, exist_ok=True)

    adapters = build_vertical_profile_comparison_adapters(init_date=init_date)
    saved_paths: list[Path] = []
    try:
        for forecast_day_index in range(FORECAST_DAYS):
            forecast_date = _forecast_day_compact_date(
                init_date,
                forecast_day_index,
            )
            output_path = (
                final_output_dir
                / (
                    "vertical_profiles_comparison_"
                    f"{season_slug}_full_{forecast_date}.png"
                )
            )
            figure = build_vertical_profile_comparison_full_figure(
                adapters=adapters,
                init_date=init_date,
                forecast_day_index=forecast_day_index,
            )
            figure.savefig(output_path, dpi=150, bbox_inches="tight")
            plt.close(figure)
            saved_paths.append(output_path)
    finally:
        for adapter in adapters:
            adapter.close()

    return saved_paths


def _slugify(label: str) -> str:
    """Return a stable filename slug for a human-readable label."""
    return label.lower().replace(" ", "_")


def _forecast_day_compact_date(
    init_date: str,
    forecast_day_index: int,
) -> str:
    """Return `YYYYMMDD` for one forecast-day offset."""
    init_day = datetime.strptime(init_date, "%Y%m%d").date()
    forecast_day = init_day + timedelta(days=forecast_day_index)
    return forecast_day.strftime("%Y%m%d")


def main() -> None:
    """Generate vertical-profile comparison figures and print their paths."""
    parser = argparse.ArgumentParser(
        description=(
            "Generate full-mode SHOC/MYNN/ERA5/Radiosonde vertical-profile "
            "comparison figures."
        )
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help=(
            "Output directory. Default writes season/date-named files under "
            "tests/output/."
        ),
    )
    parser.add_argument(
        "--init-date",
        choices=SUPPORTED_INIT_DATES,
        default=DEFAULT_INIT_DATE,
        help="Forecast initialization date selector.",
    )
    args = parser.parse_args()

    saved_paths = generate_vertical_profile_comparison_figures(
        output_dir=args.output_dir,
        init_date=args.init_date,
    )
    for saved_path in saved_paths:
        print(f"saved: {saved_path}")


if __name__ == "__main__":
    main()
