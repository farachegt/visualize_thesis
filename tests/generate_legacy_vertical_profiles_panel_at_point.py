from __future__ import annotations

from pathlib import Path
import sys

import matplotlib.pyplot as plt

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tests.fixtures import (
    OUTPUT_DIR,
    build_legacy_mynn_monan_adapter,
    build_legacy_shoc_monan_adapter,
    build_legacy_vertical_profiles_panel_at_point_figure,
)

OUTPUT_SUBDIR = "legacy_vertical_profiles_panel_at_point"
OUTPUT_FILENAME = "vertical_profiles_panel_at_point.png"


def generate_legacy_vertical_profiles_panel_at_point(
    output_dir: Path | None = None,
) -> Path:
    """Generate the legacy SHOC vs MYNN vertical-profile comparison.

    Parameters
    ----------
    output_dir:
        Directory where the figure will be saved. When omitted, the figure is
        written into `tests/output/legacy_vertical_profiles_panel_at_point`.

    Returns
    -------
    Path
        Path of the saved figure.
    """
    final_output_dir = output_dir or (OUTPUT_DIR / OUTPUT_SUBDIR)
    final_output_dir.mkdir(parents=True, exist_ok=True)

    shoc_adapter = build_legacy_shoc_monan_adapter()
    mynn_adapter = build_legacy_mynn_monan_adapter()
    try:
        figure = build_legacy_vertical_profiles_panel_at_point_figure(
            primary_adapter=shoc_adapter,
            secondary_adapter=mynn_adapter,
        )
        output_path = final_output_dir / OUTPUT_FILENAME
        figure.savefig(output_path, dpi=150, bbox_inches="tight")
        plt.close(figure)
    finally:
        shoc_adapter.close()
        mynn_adapter.close()

    return output_path


def main() -> None:
    """Generate the legacy SHOC vs MYNN vertical-profile figure."""
    output_path = generate_legacy_vertical_profiles_panel_at_point()
    print(f"saved: {output_path}")


if __name__ == "__main__":
    main()
