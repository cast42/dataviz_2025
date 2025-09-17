from __future__ import annotations

from pathlib import Path
from typing import Final

import altair as alt
import duckdb
import pandas as pd
import squarify


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
    """Prepare treemap layout coordinates for the hierarchy 1 revenue data."""
    if df.empty:
        msg = "No data available to build the treemap."
        raise ValueError(msg)

    working = df.copy()

    values = working["total_revenue"].tolist()
    normed_sizes = squarify.normalize_sizes(values, 100, 100)
    rectangles = squarify.squarify(normed_sizes, 0, 0, 100, 100)

    working["x"] = [rect["x"] for rect in rectangles]
    working["y"] = [rect["y"] for rect in rectangles]
    working["dx"] = [rect["dx"] for rect in rectangles]
    working["dy"] = [rect["dy"] for rect in rectangles]
    working["x2"] = working["x"] + working["dx"]
    working["y2"] = working["y"] + working["dy"]

    return working


def create_hierarchy1_chart(df: pd.DataFrame) -> alt.Chart:
    """Create an Altair treemap chart from processed hierarchy 1 data."""
    chart = (
        alt.Chart(df)
        .transform_joinaggregate(total_sum="sum(total_revenue)")
        .transform_calculate(share="format(datum.total_revenue / datum.total_sum, '.0%')")
        .mark_rect()
        .encode(
            x=alt.X("x:Q", scale=alt.Scale(domain=[0, 100]), axis=None),
            y=alt.Y("y:Q", scale=alt.Scale(domain=[0, 100]), axis=None),
            x2="x2:Q",
            y2="y2:Q",
            color=alt.Color("total_revenue:Q", title="Revenue"),
            tooltip=[
                alt.Tooltip("hierarchy1_id:N", title="Hierarchy 1"),
                alt.Tooltip("total_revenue:Q", title="Revenue", format=",.0f"),
                alt.Tooltip("share:N", title="Share"),
            ],
        )
        .properties(title="Relative Total Revenue by Hierarchy 1", width=600, height=500)
        .configure_title(fontSize=24, anchor="start", fontWeight="bold")
    )

    return chart


def build_hierarchy1_treemap_chart() -> alt.Chart:
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
