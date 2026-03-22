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
    build_legacy_e3sm_adapter,
    build_legacy_monan_e3sm_adapter,
    build_legacy_monan_e3sm_diurnal_peak_phase_figure,
)

START_DATE = np.datetime64("2014-02-24")
N_DAYS = 3
FIELD_FILE_STEM = "diurnal_peak_phase_pblh"


def generate_legacy_monan_e3sm_diurnal_peak_phase_pblh_figures(
    output_dir: Path | None = None,
) -> list[Path]:
    """Generate one legacy-style diurnal peak-phase figure per day.

    Parameters
    ----------
    output_dir:
        Directory where the figures will be saved. When omitted, the figures
        are written into
        `tests/output/legacy_monan_e3sm_diurnal_peak_phase_pblh`.

    Returns
    -------
    list[Path]
        Paths of the saved figures, in chronological order.
    """
    final_output_dir = output_dir or (
        OUTPUT_DIR / "legacy_monan_e3sm_diurnal_peak_phase_pblh"
    )
    final_output_dir.mkdir(parents=True, exist_ok=True)

    saved_paths: list[Path] = []
    monan_adapter = build_legacy_monan_e3sm_adapter()
    e3sm_adapter = build_legacy_e3sm_adapter()
    try:
        for day_start in _build_daily_starts(START_DATE, N_DAYS):
            figure = build_legacy_monan_e3sm_diurnal_peak_phase_figure(
                day_start=day_start,
                monan_adapter=monan_adapter,
                e3sm_adapter=e3sm_adapter,
            )
            output_path = final_output_dir / (
                f"{FIELD_FILE_STEM}_{_slugify_day(day_start)}.png"
            )
            figure.savefig(output_path, dpi=150, bbox_inches="tight")
            plt.close(figure)
            saved_paths.append(output_path)
    finally:
        monan_adapter.close()
        e3sm_adapter.close()

    return saved_paths


def main() -> None:
    """Generate all legacy-style MONAN/E3SM diurnal peak-phase figures."""
    for output_path in (
        generate_legacy_monan_e3sm_diurnal_peak_phase_pblh_figures()
    ):
        print(f"saved: {output_path}")


def _build_daily_starts(
    start_date: np.datetime64,
    n_days: int,
) -> list[np.datetime64]:
    """Return the sequence of day starts used by the batch script."""
    return [
        np.datetime64(start_date, "D") + np.timedelta64(day_idx, "D")
        for day_idx in range(n_days)
    ]


def _slugify_day(day_start: np.datetime64) -> str:
    """Convert one day instant into a stable file stem."""
    return np.datetime_as_string(day_start, unit="D")


if __name__ == "__main__":
    main()
