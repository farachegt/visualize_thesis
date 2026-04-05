from __future__ import annotations

from pathlib import Path
import sys

import matplotlib.pyplot as plt

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from plot_core.scenarios import (
    OUTPUT_DIR,
    build_legacy_e3sm_adapter,
    build_legacy_monan_e3sm_adapter,
    build_legacy_monan_e3sm_hourly_mean_figure,
    build_legacy_monan_e3sm_hourly_mean_region_map_figure,
)

REGION_COORDINATES = {
    "Atlantic Ocean": (-14.0, -24.0),
    "Amazon Rainforest": (-3.0, -60.0),
    "Sahara Desert": (20.0, 0.0),
    "Greenland": (76.4, -41.0),
}

REGION_TKE_VMAX = {
    "Atlantic Ocean": 0.2,
    "Amazon Rainforest": 1.0,
    "Sahara Desert": 2.0,
    "Greenland": 1.0,
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
        Paths of the saved figures, starting with the global reference map
        followed by the regional hourly-mean figures in the same order as
        `REGION_COORDINATES`.
    """
    final_output_dir = output_dir or (
        OUTPUT_DIR / "legacy_monan_e3sm_hourly_mean"
    )
    final_output_dir.mkdir(parents=True, exist_ok=True)

    saved_paths: list[Path] = []
    monan_adapter = build_legacy_monan_e3sm_adapter()
    e3sm_adapter = build_legacy_e3sm_adapter()
    try:
        reference_map_figure = (
            build_legacy_monan_e3sm_hourly_mean_region_map_figure(
                region_coordinates=REGION_COORDINATES,
            )
        )
        reference_map_path = (
            final_output_dir / "hourly_mean_regions_reference_map.png"
        )
        reference_map_figure.savefig(
            reference_map_path,
            dpi=150,
            bbox_inches="tight",
        )
        plt.close(reference_map_figure)
        saved_paths.append(reference_map_path)

        for region_name, (latitude, longitude) in REGION_COORDINATES.items():
            figure = build_legacy_monan_e3sm_hourly_mean_figure(
                region_name=region_name,
                point_lat=latitude,
                point_lon=longitude,
                tke_vmin=0.0,
                tke_vmax=REGION_TKE_VMAX[region_name],
                monan_adapter=monan_adapter,
                e3sm_adapter=e3sm_adapter,
            )
            output_path = final_output_dir / (
                f"{_slugify_region_name(region_name)}.png"
            )
            figure.savefig(output_path, dpi=150, bbox_inches="tight")
            plt.close(figure)
            saved_paths.append(output_path)
    finally:
        monan_adapter.close()
        e3sm_adapter.close()

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
