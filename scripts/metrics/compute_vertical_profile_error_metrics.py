from __future__ import annotations

import argparse
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from metrics.registry import (  # noqa: E402
    TIME_SERIES_DEFAULT_INIT_DATE,
    TIME_SERIES_SUPPORTED_INIT_DATES,
    build_case_metadata,
)
from metrics.tables import (  # noqa: E402
    VERTICAL_PROFILE_LONG_FIELDNAMES,
    VERTICAL_PROFILE_WIDE_FIELDNAMES,
    build_vertical_profile_latex_metrics_table,
    build_vertical_profile_long_rows_from_wide_rows,
    default_vertical_profile_output_paths,
    write_csv,
    write_text,
)
from metrics.vertical_profiles import (  # noqa: E402
    compute_vertical_profile_metric_rows,
)

DEFAULT_OUTPUT_ROOT = PROJECT_ROOT / "tests" / "output" / "metrics"


def compute_vertical_profile_error_metrics(
    *,
    init_date: str = TIME_SERIES_DEFAULT_INIT_DATE,
    print_alignment: bool = True,
) -> tuple[list[dict[str, object]], list[dict[str, object]], dict[str, str]]:
    """Compute vertical-profile long and wide metrics for one case."""
    wide_rows, metadata = compute_vertical_profile_metric_rows(
        init_date=init_date,
        alignment_logger=print if print_alignment else None,
    )
    long_rows = build_vertical_profile_long_rows_from_wide_rows(wide_rows)
    return long_rows, wide_rows, metadata


def resolve_output_paths(
    *,
    output: Path | None,
    season_slug: str,
) -> tuple[Path, Path, Path]:
    """Resolve vertical-profile long/wide/table output paths."""
    if output is None:
        return default_vertical_profile_output_paths(
            output_root=DEFAULT_OUTPUT_ROOT,
            season_slug=season_slug,
        )

    if output.suffix:
        base = output.with_suffix("")
        return (
            base.with_name(f"{base.name}_long.csv"),
            base.with_name(f"{base.name}_wide.csv"),
            base.with_name(f"{base.name}_table.tex"),
        )

    return default_vertical_profile_output_paths(
        output_root=output,
        season_slug=season_slug,
    )


def main() -> None:
    """Compute and write vertical-profile error metrics for one case."""
    parser = argparse.ArgumentParser(
        description=(
            "Compute SHOC/MYNN vertical-profile metrics against GoAmazon "
            "radiosonde observations over full-mode synoptic profiles."
        )
    )
    parser.add_argument(
        "--init-date",
        choices=TIME_SERIES_SUPPORTED_INIT_DATES,
        default=TIME_SERIES_DEFAULT_INIT_DATE,
        help="Forecast initialization date selector.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help=(
            "Output directory for default long/wide/table filenames, or a "
            "base file path where suffixes are appended. Default: "
            "tests/output/metrics/."
        ),
    )
    args = parser.parse_args()

    case = build_case_metadata(args.init_date)
    print("vertical-profile reference: Observation")
    print("vertical-profile candidate sources: SHOC, MYNN")

    long_rows, wide_rows, metadata = compute_vertical_profile_error_metrics(
        init_date=case.init_date,
        print_alignment=True,
    )
    long_path, wide_path, latex_path = resolve_output_paths(
        output=args.output,
        season_slug=metadata["season_slug"],
    )
    latex_table = build_vertical_profile_latex_metrics_table(
        wide_rows=wide_rows,
        season_slug=metadata["season_slug"],
    )

    write_csv(
        path=long_path,
        fieldnames=VERTICAL_PROFILE_LONG_FIELDNAMES,
        rows=long_rows,
    )
    write_csv(
        path=wide_path,
        fieldnames=VERTICAL_PROFILE_WIDE_FIELDNAMES,
        rows=wide_rows,
    )
    write_text(path=latex_path, text=latex_table)

    print(f"wrote long: {long_path}")
    print(f"wrote wide: {wide_path}")
    print(f"wrote table: {latex_path}")


if __name__ == "__main__":
    main()
