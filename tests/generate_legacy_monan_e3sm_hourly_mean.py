from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt

from tests.fixtures import (
    OUTPUT_DIR,
    build_legacy_monan_e3sm_hourly_mean_figure,
)

REGION_COORDINATES = {
    "Atlantic Ocean": (-14.0, -24.0),
    "Amazon Rainforest": (-3.0, -60.0),
    "African Desert": (20.0, 0.0),
    "Siberia": (60.0, 100.0),
    "Australia": (-25.0, 135.0),
}

REGION_TKE_VMAX = {
    "Atlantic Ocean": 0.2,
    "Amazon Rainforest": 1.0,
    "African Desert": 2.0,
    "Siberia": 2.0,
    "Australia": 2.0,
}


def generate_legacy_monan_e3sm_hourly_mean_figures(
    output_dir: Path | None = None,
) -> list[Path]:
    """Generate one legacy-style hourly-mean figure per configured region.

    Parameters
    ----------
    output_dir:
        Directory where the figures will be saved. When omitted, the figures
        are written into `tests/output/legacy_monan_e3sm_hourly_mean`.

    Returns
    -------
    list[Path]
        Paths of the saved figures, in the same order as
        `REGION_COORDINATES`.
    """
    final_output_dir = output_dir or (
        OUTPUT_DIR / "legacy_monan_e3sm_hourly_mean"
    )
    final_output_dir.mkdir(parents=True, exist_ok=True)

    saved_paths: list[Path] = []
    for region_name, (latitude, longitude) in REGION_COORDINATES.items():
        figure = build_legacy_monan_e3sm_hourly_mean_figure(
            region_name=region_name,
            point_lat=latitude,
            point_lon=longitude,
            tke_vmin=0.0,
            tke_vmax=REGION_TKE_VMAX[region_name],
        )
        output_path = final_output_dir / (
            f"{_slugify_region_name(region_name)}.png"
        )
        figure.savefig(output_path, dpi=150, bbox_inches="tight")
        plt.close(figure)
        saved_paths.append(output_path)

    return saved_paths


def main() -> None:
    """Generate all legacy-style MONAN/E3SM hourly-mean region figures."""
    for output_path in generate_legacy_monan_e3sm_hourly_mean_figures():
        print(f"saved: {output_path}")


def _slugify_region_name(region_name: str) -> str:
    """Convert a human-readable region name into a stable file stem."""
    return region_name.lower().replace(" ", "_")


if __name__ == "__main__":
    main()
