from __future__ import annotations

import argparse
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from metrics.alignment import align_time_series, build_paired_dataarrays
from metrics.extraction import extract_hourly_series_by_source
from metrics.registry import (
    RECIPE_FAMILY_VARIABLES,
    TIME_SERIES_DEFAULT_INIT_DATE,
    TIME_SERIES_SUPPORTED_INIT_DATES,
    VARIABLE_LABELS,
    VARIABLE_UNITS,
    build_case_metadata,
    build_reference_summary_lines,
    iter_recipe_variable_pairs,
    select_candidate_sources,
    select_reference_source,
)
from metrics.scores import (
    compute_bias,
    compute_corr,
    compute_mae,
    compute_precipitation_totals,
    compute_rmse,
    paired_finite_sample_count,
)
from metrics.tables import (
    LONG_FIELDNAMES,
    WIDE_FIELDNAMES,
    build_latex_metrics_table,
    build_long_rows_from_wide_rows,
    default_output_paths,
    write_csv,
    write_text,
)

DEFAULT_OUTPUT_ROOT = PROJECT_ROOT / "tests" / "output" / "metrics"


def compute_error_metrics(
    *,
    init_date: str = TIME_SERIES_DEFAULT_INIT_DATE,
) -> tuple[list[dict[str, object]], list[dict[str, object]], dict[str, str]]:
    """Compute all v1 error-metric outputs for one supported case."""
    case = build_case_metadata(init_date)
    wide_rows: list[dict[str, object]] = []

    for recipe_family, variable_name in iter_recipe_variable_pairs():
        if variable_name not in RECIPE_FAMILY_VARIABLES[recipe_family]:
            raise ValueError(
                "Internal variable registry mismatch for "
                f"{recipe_family}/{variable_name}."
            )

        series_by_source = extract_hourly_series_by_source(
            recipe_family=recipe_family,
            variable_name=variable_name,
            init_date=case.init_date,
        )
        available_sources = tuple(series_by_source.keys())

        reference_source = select_reference_source(
            recipe_family=recipe_family,
            variable_name=variable_name,
            case=case,
        )
        if reference_source not in series_by_source:
            raise ValueError(
                f"Reference source {reference_source!r} is unavailable for "
                f"{recipe_family}/{variable_name} in {case.init_date}."
            )

        reference_plot_data = series_by_source[reference_source]
        candidate_sources = select_candidate_sources(
            variable_name=variable_name,
            reference_source=reference_source,
            available_sources=available_sources,
        )

        for candidate_source in candidate_sources:
            candidate_plot_data = series_by_source[candidate_source]
            aligned = align_time_series(
                candidate_times=candidate_plot_data.times,
                candidate_values=candidate_plot_data.values,
                reference_times=reference_plot_data.times,
                reference_values=reference_plot_data.values,
            )
            candidate_da, reference_da = build_paired_dataarrays(aligned)
            n_samples = paired_finite_sample_count(candidate_da, reference_da)

            wide_row: dict[str, object] = {
                "case_init_date": case.init_date,
                "season": case.season_slug,
                "recipe_family": recipe_family,
                "variable": variable_name,
                "variable_label": VARIABLE_LABELS[variable_name],
                "source": candidate_source,
                "reference_source": reference_source,
                "units": VARIABLE_UNITS[variable_name],
                "n_samples": n_samples,
                "bias": compute_bias(candidate_da, reference_da),
                "mae": compute_mae(candidate_da, reference_da),
                "rmse": compute_rmse(candidate_da, reference_da),
                "corr": compute_corr(candidate_da, reference_da),
                "total_candidate": None,
                "total_reference": None,
                "total_bias": None,
                "relative_total_bias_percent": None,
            }

            if variable_name == "precipitation":
                totals = compute_precipitation_totals(
                    candidate_da,
                    reference_da,
                )
                wide_row["total_candidate"] = totals.total_candidate
                wide_row["total_reference"] = totals.total_reference
                wide_row["total_bias"] = totals.total_bias
                wide_row["relative_total_bias_percent"] = (
                    totals.relative_total_bias_percent
                )

            wide_rows.append(wide_row)

    long_rows = build_long_rows_from_wide_rows(wide_rows)
    return long_rows, wide_rows, {
        "case_init_date": case.init_date,
        "season_slug": case.season_slug,
    }


def resolve_output_paths(
    *,
    output_dir: Path | None,
    season_slug: str,
) -> tuple[Path, Path, Path]:
    """Resolve long/wide CSV and LaTeX output paths."""
    output_root = DEFAULT_OUTPUT_ROOT if output_dir is None else output_dir
    return default_output_paths(
        output_root=output_root,
        season_slug=season_slug,
    )


def main() -> None:
    """Compute and write CSV and LaTeX error metrics for one case."""
    parser = argparse.ArgumentParser(
        description=(
            "Compute SHOC/MYNN/ERA5 error metrics against Observation or "
            "ERA5 references over the 5-day hourly comparison window."
        )
    )
    parser.add_argument(
        "--init-date",
        choices=TIME_SERIES_SUPPORTED_INIT_DATES,
        default=TIME_SERIES_DEFAULT_INIT_DATE,
        help="Forecast initialization date selector.",
    )
    parser.add_argument(
        "--output-dir",
        dest="output_dir",
        type=Path,
        default=None,
        help=(
            "Output directory for default long/wide/table filenames. Default: "
            "tests/output/metrics/."
        ),
    )
    args = parser.parse_args()

    case = build_case_metadata(args.init_date)
    for summary_line in build_reference_summary_lines(case):
        print(summary_line)

    long_rows, wide_rows, metadata = compute_error_metrics(
        init_date=args.init_date
    )
    long_path, wide_path, latex_path = resolve_output_paths(
        output_dir=args.output_dir,
        season_slug=metadata["season_slug"],
    )
    latex_table = build_latex_metrics_table(
        wide_rows=wide_rows,
        season_slug=metadata["season_slug"],
    )

    write_csv(
        path=long_path,
        fieldnames=LONG_FIELDNAMES,
        rows=long_rows,
    )
    write_csv(
        path=wide_path,
        fieldnames=WIDE_FIELDNAMES,
        rows=wide_rows,
    )
    write_text(path=latex_path, text=latex_table)

    print(f"wrote long: {long_path}")
    print(f"wrote wide: {wide_path}")
    print(f"wrote table: {latex_path}")


if __name__ == "__main__":
    main()
