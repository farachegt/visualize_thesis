from __future__ import annotations

from pathlib import Path
import sys

import matplotlib.pyplot as plt
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tests.fixtures import (
    OUTPUT_DIR,
    build_legacy_monan_e3sm_cross_section_figure,
)

START_TIME = np.datetime64("2014-02-24T00:00")
END_TIME = np.datetime64("2014-02-27T00:00")
FIELD_FILE_STEM = "theta"


def generate_legacy_monan_e3sm_cross_section_figures(
    output_dir: Path | None = None,
) -> list[Path]:
    """Generate one legacy-style transect figure per configured hour.

    Parameters
    ----------
    output_dir:
        Directory where the figures will be saved. When omitted, the figures
        are written into `tests/output/legacy_monan_e3sm_cross_sections`.

    Returns
    -------
    list[Path]
        Paths of the saved figures, in chronological order.
    """
    final_output_dir = output_dir or (
        OUTPUT_DIR / "legacy_monan_e3sm_cross_sections"
    )
    final_output_dir.mkdir(parents=True, exist_ok=True)

    saved_paths: list[Path] = []
    for time in _build_hourly_times(START_TIME, END_TIME):
        figure = build_legacy_monan_e3sm_cross_section_figure(time=time)
        output_path = final_output_dir / (
            f"transect_{FIELD_FILE_STEM}_{_slugify_time(time)}.png"
        )
        figure.savefig(output_path, dpi=150, bbox_inches="tight")
        plt.close(figure)
        saved_paths.append(output_path)

    return saved_paths


def main() -> None:
    """Generate all legacy-style MONAN/E3SM transect figures."""
    for output_path in generate_legacy_monan_e3sm_cross_section_figures():
        print(f"saved: {output_path}")


def _build_hourly_times(
    start_time: np.datetime64,
    end_time: np.datetime64,
) -> list[np.datetime64]:
    """Return an inclusive list of hourly instants."""
    hourly_times: list[np.datetime64] = []
    current_time = np.datetime64(start_time, "h")
    final_time = np.datetime64(end_time, "h")
    while current_time <= final_time:
        hourly_times.append(current_time)
        current_time += np.timedelta64(1, "h")

    return hourly_times


def _slugify_time(time: np.datetime64) -> str:
    """Convert a time instant into a stable file stem."""
    return np.datetime_as_string(time, unit="h").replace(":", "")


if __name__ == "__main__":
    main()
