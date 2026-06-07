from __future__ import annotations

import csv
import math
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

VERTICAL_PROFILE_LONG_FIELDNAMES = (
    "case_init_date",
    "season",
    "metric_family",
    "variable",
    "variable_label",
    "source",
    "reference_source",
    "local_hour_lt",
    "synoptic_hour_utc",
    "metric",
    "value",
    "units",
    "n_samples",
    "n_profiles",
)

VERTICAL_PROFILE_WIDE_FIELDNAMES = (
    "case_init_date",
    "season",
    "metric_family",
    "variable",
    "variable_label",
    "source",
    "reference_source",
    "local_hour_lt",
    "synoptic_hour_utc",
    "units",
    "n_samples",
    "n_profiles",
    "bias",
    "mae",
    "rmse",
    "corr",
)

LATEX_TABLE_SOURCES = ("SHOC", "MYNN")
LATEX_TABLE_EXCLUDED_VARIABLES = ("precipitation",)
LATEX_UNIT_LABELS = {
    "degC": r"$^\circ$C",
    "g kg^-1": r"g kg$^{-1}$",
    "m s^-1": r"m s$^{-1}$",
    "mm h^-1": r"mm h$^{-1}$",
    "m": "m",
    "W m^-2": r"W m$^{-2}$",
}
VERTICAL_PROFILE_LATEX_UNIT_LABELS = {
    **LATEX_UNIT_LABELS,
    "K": "K",
}


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


def build_latex_metrics_table(
    *,
    wide_rows: list[dict[str, object]],
    season_slug: str,
) -> str:
    """Return the publication table LaTeX from wide metric rows."""
    season_label = season_slug.replace("_", " ")
    label_suffix = season_slug.replace("_", "-")
    source_rows = _group_latex_rows_by_source(wide_rows)

    lines = [
        r"% Requires \usepackage{multirow}",
        r"\begin{table}[htbp]",
        r"\centering",
        r"\scriptsize",
        (
            r"\caption{Surface and PBL-height error metrics for "
            f"{season_label}."
            r"}"
        ),
        rf"\label{{tab:error-metrics-sfc-{label_suffix}}}",
        r"\begin{tabular}{lllrrrr}",
        r"\hline",
        r"Source & Variable & Unit & Bias & MAE & RMSE & $r$ \\",
        r"\hline",
    ]

    for source_index, source_label in enumerate(LATEX_TABLE_SOURCES):
        rows = source_rows.get(source_label, [])
        if not rows:
            continue
        if source_index > 0:
            lines.append(r"\hline")

        row_count = len(rows)
        for row_index, row in enumerate(rows):
            source_cell = (
                rf"\multirow{{{row_count}}}{{*}}{{{source_label}}}"
                if row_index == 0
                else ""
            )
            lines.append(
                " & ".join(
                    (
                        source_cell,
                        _latex_escape(row["variable_label"]),
                        _latex_unit_label(row["units"]),
                        _format_latex_metric_value(row["bias"]),
                        _format_latex_metric_value(row["mae"]),
                        _format_latex_metric_value(row["rmse"]),
                        _format_latex_metric_value(row["corr"]),
                    )
                )
                + r" \\"
            )

    lines.extend(
        [
            r"\hline",
            r"\end{tabular}",
            r"\end{table}",
            "",
        ]
    )
    return "\n".join(lines)


def build_vertical_profile_long_rows_from_wide_rows(
    wide_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    """Return vertical-profile long table rows from wide metric rows."""
    long_rows: list[dict[str, object]] = []
    for wide_row in wide_rows:
        variable_name = str(wide_row["variable"])
        for metric_name in BASE_METRIC_NAMES:
            long_rows.append(
                {
                    "case_init_date": wide_row["case_init_date"],
                    "season": wide_row["season"],
                    "metric_family": wide_row["metric_family"],
                    "variable": variable_name,
                    "variable_label": wide_row["variable_label"],
                    "source": wide_row["source"],
                    "reference_source": wide_row["reference_source"],
                    "local_hour_lt": wide_row["local_hour_lt"],
                    "synoptic_hour_utc": wide_row["synoptic_hour_utc"],
                    "metric": metric_name,
                    "value": wide_row.get(metric_name),
                    "units": metric_units(
                        variable_name=variable_name,
                        metric_name=metric_name,
                    ),
                    "n_samples": wide_row["n_samples"],
                    "n_profiles": wide_row["n_profiles"],
                }
            )
    return long_rows


def build_vertical_profile_latex_metrics_table(
    *,
    wide_rows: list[dict[str, object]],
    season_slug: str,
) -> str:
    """Return the vertical-profile publication table LaTeX."""
    season_label = season_slug.replace("_", " ")
    label_suffix = season_slug.replace("_", "-")
    selected_rows = [
        row
        for row in wide_rows
        if row.get("source") in LATEX_TABLE_SOURCES
        and int(row.get("n_samples", 0)) > 0
    ]
    selected_rows.sort(
        key=lambda row: (
            int(row["local_hour_lt"]),
            LATEX_TABLE_SOURCES.index(str(row["source"])),
            str(row["variable"]),
        )
    )

    lines = [
        r"% Requires \usepackage{multirow}",
        r"\begin{table}[htbp]",
        r"\centering",
        r"\scriptsize",
        (
            r"\caption{Vertical-profile error metrics for "
            f"{season_label}."
            r"}"
        ),
        rf"\label{{tab:error-metrics-vp-{label_suffix}}}",
        r"\begin{tabular}{lllllrrrr}",
        r"\hline",
        (
            r"Local hour (LT) & UTC hour & Source & Variable & Unit & "
            r"Bias & MAE & RMSE & $r$ \\"
        ),
        r"\hline",
    ]

    grouped_rows: dict[tuple[int, str], list[dict[str, object]]] = {}
    for row in selected_rows:
        key = (int(row["local_hour_lt"]), str(row["source"]))
        grouped_rows.setdefault(key, []).append(row)

    previous_hour: int | None = None
    for hour in (2, 8, 14, 20):
        hour_has_rows = False
        for source_label in LATEX_TABLE_SOURCES:
            rows = grouped_rows.get((hour, source_label), [])
            if not rows:
                continue
            if previous_hour is not None and previous_hour != hour:
                lines.append(r"\hline")
            previous_hour = hour
            hour_has_rows = True
            row_count = len(rows)
            utc_hour = str(rows[0]["synoptic_hour_utc"])
            for row_index, row in enumerate(rows):
                hour_cell = (
                    rf"\multirow{{{row_count}}}{{*}}{{{hour:02d}}}"
                    if row_index == 0
                    else ""
                )
                utc_hour_cell = (
                    rf"\multirow{{{row_count}}}{{*}}{{{utc_hour}}}"
                    if row_index == 0
                    else ""
                )
                source_cell = (
                    rf"\multirow{{{row_count}}}{{*}}{{{source_label}}}"
                    if row_index == 0
                    else ""
                )
                lines.append(
                    " & ".join(
                        (
                            hour_cell,
                            utc_hour_cell,
                            source_cell,
                            _latex_escape(row["variable_label"]),
                            _vertical_profile_latex_unit_label(row["units"]),
                            _format_latex_metric_value(row["bias"]),
                            _format_latex_metric_value(row["mae"]),
                            _format_latex_metric_value(row["rmse"]),
                            _format_latex_metric_value(row["corr"]),
                        )
                    )
                    + r" \\"
                )
        if hour_has_rows:
            previous_hour = hour

    lines.extend(
        [
            r"\hline",
            r"\end{tabular}",
            r"\end{table}",
            "",
        ]
    )
    return "\n".join(lines)


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


def write_text(
    *,
    path: Path,
    text: str,
) -> None:
    """Write text output with a trailing newline."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def default_output_paths(
    *,
    output_root: Path,
    season_slug: str,
) -> tuple[Path, Path, Path]:
    """Return default long/wide/table output paths for one season."""
    return (
        output_root / f"error_metrics_sfc_{season_slug}_long.csv",
        output_root / f"error_metrics_sfc_{season_slug}_wide.csv",
        output_root / f"error_metrics_sfc_{season_slug}_table.tex",
    )


def default_vertical_profile_output_paths(
    *,
    output_root: Path,
    season_slug: str,
) -> tuple[Path, Path, Path]:
    """Return default vertical-profile long/wide/table output paths."""
    return (
        output_root / f"error_metrics_vp_{season_slug}_long.csv",
        output_root / f"error_metrics_vp_{season_slug}_wide.csv",
        output_root / f"error_metrics_vp_{season_slug}_table.tex",
    )


def _group_latex_rows_by_source(
    wide_rows: list[dict[str, object]],
) -> dict[str, list[dict[str, object]]]:
    selected_rows = [
        row
        for row in wide_rows
        if row.get("source") in LATEX_TABLE_SOURCES
        and row.get("variable") not in LATEX_TABLE_EXCLUDED_VARIABLES
    ]

    variable_order: dict[str, int] = {}
    for row in selected_rows:
        variable_name = str(row["variable"])
        if variable_name not in variable_order:
            variable_order[variable_name] = len(variable_order)

    grouped_rows: dict[str, list[dict[str, object]]] = {
        source_label: [] for source_label in LATEX_TABLE_SOURCES
    }
    for row in selected_rows:
        grouped_rows[str(row["source"])].append(row)

    for rows in grouped_rows.values():
        rows.sort(key=lambda row: variable_order[str(row["variable"])])

    return grouped_rows


def _format_latex_metric_value(value: object) -> str:
    if value is None or value == "":
        return r"--"
    try:
        numeric_value = float(value)
    except (TypeError, ValueError):
        return _latex_escape(value)
    if not math.isfinite(numeric_value):
        return r"--"
    return f"{numeric_value:.2f}"


def _latex_unit_label(unit: object) -> str:
    unit_text = str(unit)
    return LATEX_UNIT_LABELS.get(unit_text, _latex_escape(unit_text))


def _vertical_profile_latex_unit_label(unit: object) -> str:
    unit_text = str(unit)
    return VERTICAL_PROFILE_LATEX_UNIT_LABELS.get(
        unit_text,
        _latex_escape(unit_text),
    )


def _latex_escape(value: object) -> str:
    text = str(value)
    return (
        text.replace("\\", r"\textbackslash{}")
        .replace("&", r"\&")
        .replace("%", r"\%")
        .replace("_", r"\_")
        .replace("#", r"\#")
    )


__all__ = [
    "LONG_FIELDNAMES",
    "VERTICAL_PROFILE_LONG_FIELDNAMES",
    "VERTICAL_PROFILE_WIDE_FIELDNAMES",
    "WIDE_FIELDNAMES",
    "build_latex_metrics_table",
    "build_long_rows_from_wide_rows",
    "build_vertical_profile_latex_metrics_table",
    "build_vertical_profile_long_rows_from_wide_rows",
    "default_output_paths",
    "default_vertical_profile_output_paths",
    "write_csv",
    "write_text",
]
