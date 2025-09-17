from __future__ import annotations

from pathlib import Path
from typing import Final, Tuple

import duckdb
import pandas as pd
import plotly.graph_objects as go

DATA_DIR: Final[Path] = Path(__file__).resolve().parent / "data"
DATA_PATH: Final[Path] = DATA_DIR / "sales_stores_hierarchy_merged.parquet"

HIERARCHY_COLUMNS: Final[dict[int, str]] = {
    1: "hierarchy1_id",
    2: "hierarchy2_id",
    3: "hierarchy3_id",
    4: "hierarchy4_id",
    5: "hierarchy5_id",
}
HIERARCHY_COLUMN_TO_LEVEL: Final[dict[str, int]] = {
    column: level for level, column in HIERARCHY_COLUMNS.items()
}

METRIC_COLUMNS: Final[dict[str, str]] = {
    "revenue": "revenue",
    "sales": "sales",
    "stock": "stock",
}


def _ensure_data_path() -> Path:
    if not DATA_PATH.exists():
        msg = f"Expected parquet file at {DATA_PATH}, but it was not found."
        raise FileNotFoundError(msg)
    return DATA_PATH


def _normalize_hierarchy_column(column: str) -> Tuple[str, int]:
    """Validate the hierarchy column name and return the normalized column with its level."""
    normalized = column.strip()

    try:
        level = HIERARCHY_COLUMN_TO_LEVEL[normalized]
    except KeyError as exc:  # pragma: no cover - defensive branch
        expected = ", ".join(sorted(HIERARCHY_COLUMN_TO_LEVEL))
        msg = f"Unsupported hierarchy column '{column}'. Expected one of: {expected}."
        raise ValueError(msg) from exc

    return normalized, level


def _normalize_metric(metric: str) -> Tuple[str, str]:
    """Validate the metric name and return the data column with a friendly label."""
    key = metric.strip().lower()

    try:
        column_name = METRIC_COLUMNS[key]
    except KeyError as exc:  # pragma: no cover - defensive branch
        expected = ", ".join(sorted(METRIC_COLUMNS))
        msg = f"Unsupported metric '{metric}'. Expected one of: {expected}."
        raise ValueError(msg) from exc

    label = key.capitalize()
    return column_name, label


def load_hierarchy_data(column: str, metric: str = "revenue") -> pd.DataFrame:
    """Load hierarchy metric data for the requested column using DuckDB."""
    parquet_path = _ensure_data_path()
    hierarchy_column, _ = _normalize_hierarchy_column(column)
    metric_column, _ = _normalize_metric(metric)

    query = f"""
        SELECT
            {hierarchy_column} AS hierarchy_id,
            SUM({metric_column}) AS total_value
        FROM read_parquet(?)
        GROUP BY {hierarchy_column}
        ORDER BY total_value DESC
    """

    with duckdb.connect() as con:
        df = con.execute(query, [str(parquet_path)]).fetchdf()

    return df


def process_hierarchy_data(
    df: pd.DataFrame, column: str, metric: str = "revenue"
) -> pd.DataFrame:
    """Prepare hierarchy metric data for treemap visualization."""
    _normalize_hierarchy_column(column)
    _, metric_label = _normalize_metric(metric)

    if df.empty:
        msg = "No data available to build the treemap."
        raise ValueError(msg)

    working = df.copy()
    working.sort_values(
        "total_value", ascending=False, inplace=True, ignore_index=True
    )

    total = working["total_value"].sum()
    if total == 0:
        msg = f"{metric_label} totals are zero; unable to build treemap."
        raise ValueError(msg)

    working["share"] = working["total_value"].div(total).map(lambda v: f"{v:.0%}")
    working["label"] = working["hierarchy_id"].astype(str)

    return working


def create_hierarchy_chart(
    df: pd.DataFrame, column: str, metric: str = "revenue"
) -> go.Figure:
    """Create a Plotly treemap figure from processed hierarchy data."""
    _, level = _normalize_hierarchy_column(column)
    _, metric_label = _normalize_metric(metric)

    hover_template = (
        f"Hierarchy {level}: %{{label}}<br>Total {metric_label}: %{{value:,.0f}}<br>"
        "Share: %{customdata}<extra></extra>"
    )

    figure = go.Figure(
        go.Treemap(
            labels=df["label"],
            parents=["" for _ in df.index],
            values=df["total_value"],
            customdata=df["share"],
            marker=dict(colors=df["total_value"], colorscale="Blues"),
            texttemplate=(
                f"<b>%{{label}}</b><br>%{{value:,.0f}} {metric_label}<br>"
                "Share: %{customdata}"
            ),
            hovertemplate=hover_template,
        )
    )

    figure.update_layout(
        title=f"Relative Total {metric_label} by Hierarchy {level}",
        margin=dict(t=80, l=0, r=0, b=0),
    )

    return figure


def build_hierarchy_treemap_chart(column: str, metric: str = "revenue") -> go.Figure:
    """Convenience helper that loads, processes, and plots the treemap chart."""
    raw_df = load_hierarchy_data(column, metric)
    processed_df = process_hierarchy_data(raw_df, column, metric)
    return create_hierarchy_chart(processed_df, column, metric)


def load_hierarchy1_data() -> pd.DataFrame:
    return load_hierarchy_data("hierarchy1_id")


def process_hierarchy1_data(df: pd.DataFrame) -> pd.DataFrame:
    return process_hierarchy_data(df, "hierarchy1_id")


def create_hierarchy1_chart(df: pd.DataFrame) -> go.Figure:
    return create_hierarchy_chart(df, "hierarchy1_id")


def build_hierarchy1_treemap_chart() -> go.Figure:
    return build_hierarchy_treemap_chart("hierarchy1_id")


__all__ = [
    "HIERARCHY_COLUMNS",
    "METRIC_COLUMNS",
    "build_hierarchy_treemap_chart",
    "build_hierarchy1_treemap_chart",
    "create_hierarchy_chart",
    "create_hierarchy1_chart",
    "load_hierarchy_data",
    "load_hierarchy1_data",
    "process_hierarchy_data",
    "process_hierarchy1_data",
]
