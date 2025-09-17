from __future__ import annotations

from pathlib import Path
from typing import Final

import duckdb
import pandas as pd
import plotly.graph_objects as go

DATA_DIR: Final[Path] = Path(__file__).resolve().parent / "data"
DATA_PATH: Final[Path] = DATA_DIR / "sales_stores_hierarchy_merged.parquet"


def _ensure_data_path() -> Path:
    if not DATA_PATH.exists():
        msg = f"Expected parquet file at {DATA_PATH}, but it was not found."
        raise FileNotFoundError(msg)
    return DATA_PATH


def load_hierarchy1_data() -> pd.DataFrame:
    """Load hierarchy 1 revenue data from the parquet source using DuckDB."""
    parquet_path = _ensure_data_path()

    query = """
        SELECT
            hierarchy1_id,
            SUM(revenue) AS total_revenue
        FROM read_parquet(?)
        GROUP BY hierarchy1_id
        ORDER BY total_revenue DESC
    """

    with duckdb.connect() as con:
        df = con.execute(query, [str(parquet_path)]).fetchdf()

    return df


def process_hierarchy1_data(df: pd.DataFrame) -> pd.DataFrame:
    """Prepare hierarchy 1 revenue data for treemap visualization."""
    if df.empty:
        msg = "No data available to build the treemap."
        raise ValueError(msg)

    working = df.copy()
    working.sort_values(
        "total_revenue", ascending=False, inplace=True, ignore_index=True
    )

    total = working["total_revenue"].sum()
    if total == 0:
        msg = "Revenue totals are zero; unable to build treemap."
        raise ValueError(msg)

    working["share"] = working["total_revenue"].div(total).map(lambda v: f"{v:.0%}")
    working["label"] = working["hierarchy1_id"].astype(str)

    return working


def create_hierarchy1_chart(df: pd.DataFrame) -> go.Figure:
    """Create a Plotly treemap figure from processed hierarchy 1 data."""
    figure = go.Figure(
        go.Treemap(
            labels=df["label"],
            parents=["" for _ in df.index],
            values=df["total_revenue"],
            customdata=df["share"],
            marker=dict(colors=df["total_revenue"], colorscale="Blues"),
            texttemplate="<b>%{label}</b><br>%{value:,.0f}<br>%{customdata}",
            hovertemplate=(
                "Hierarchy 1: %{label}<br>Revenue: %{value:,.0f}<br>"
                "Share: %{customdata}<extra></extra>"
            ),
        )
    )

    figure.update_layout(
        title="Relative Total Revenue by Hierarchy 1",
        margin=dict(t=80, l=0, r=0, b=0),
    )

    return figure


def build_hierarchy1_treemap_chart() -> go.Figure:
    """Convenience helper that loads, processes, and plots the treemap chart."""
    raw_df = load_hierarchy1_data()
    processed_df = process_hierarchy1_data(raw_df)
    return create_hierarchy1_chart(processed_df)


__all__ = [
    "build_hierarchy1_treemap_chart",
    "create_hierarchy1_chart",
    "load_hierarchy1_data",
    "process_hierarchy1_data",
]
