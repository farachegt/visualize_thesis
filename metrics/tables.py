from __future__ import annotations

import csv
from pathlib import Path

from .registry import (
    BASE_METRIC_NAMES,
    PRECIPITATION_TOTAL_METRIC_NAMES,
    metric_units,
)

LONG_FIELDNAMES = (
    "case_init_date",
    "season",
    "recipe_family",
    "variable",
    "variable_label",
    "source",
    "reference_source",
    "metric",
    "value",
    "units",
    "n_samples",
)

WIDE_FIELDNAMES = (
    "case_init_date",
    "season",
    "recipe_family",
    "variable",
    "variable_label",
    "source",
    "reference_source",
    "units",
    "n_samples",
    "bias",
    "mae",
    "rmse",
    "corr",
    "total_candidate",
    "total_reference",
    "total_bias",
    "relative_total_bias_percent",
)


def build_long_rows_from_wide_rows(
    wide_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    """Return one output row per metric from wide metric rows."""
    long_rows: list[dict[str, object]] = []
    for wide_row in wide_rows:
        variable_name = str(wide_row["variable"])
        metric_names: tuple[str, ...] = BASE_METRIC_NAMES
        if variable_name == "precipitation":
            metric_names = (
                *BASE_METRIC_NAMES,
                *PRECIPITATION_TOTAL_METRIC_NAMES,
            )

        for metric_name in metric_names:
            long_rows.append(
                {
                    "case_init_date": wide_row["case_init_date"],
                    "season": wide_row["season"],
                    "recipe_family": wide_row["recipe_family"],
                    "variable": variable_name,
                    "variable_label": wide_row["variable_label"],
                    "source": wide_row["source"],
                    "reference_source": wide_row["reference_source"],
                    "metric": metric_name,
                    "value": wide_row.get(metric_name),
                    "units": metric_units(
                        variable_name=variable_name,
                        metric_name=metric_name,
                    ),
                    "n_samples": wide_row["n_samples"],
                }
            )

    return long_rows


def write_csv(
    *,
    path: Path,
    fieldnames: tuple[str, ...],
    rows: list[dict[str, object]],
) -> None:
    """Write rows to CSV with deterministic column order."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(fieldnames),
            extrasaction="ignore",
        )
        writer.writeheader()
        writer.writerows(rows)


def default_output_paths(
    *,
    output_root: Path,
    season_slug: str,
) -> tuple[Path, Path]:
    """Return default long/wide output paths for one season."""
    return (
        output_root / f"error_metrics_sfc_{season_slug}_long.csv",
        output_root / f"error_metrics_sfc_{season_slug}_wide.csv",
    )


__all__ = [
    "LONG_FIELDNAMES",
    "WIDE_FIELDNAMES",
    "build_long_rows_from_wide_rows",
    "default_output_paths",
    "write_csv",
]
