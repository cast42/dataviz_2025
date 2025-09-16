from pathlib import Path

import altair as alt
import duckdb


project_root = Path(__file__).resolve().parent
parquet_path = project_root / "data" / "sales_stores_hierarchy_merged.parquet"

parquet_literal = str(parquet_path).replace("'", "''")

if not parquet_path.exists():
    msg = f"Expected parquet file at {parquet_path}, but it was not found."
    raise FileNotFoundError(msg)

# connect to an in-memory DuckDB instance
con = duckdb.connect()

# SQL to get total revenue per day
query = f"""
SELECT
    DATE_TRUNC('day', date) AS day,
    SUM(revenue) AS total_revenue
FROM read_parquet('{parquet_literal}')
GROUP BY day
ORDER BY day
"""

# execute and fetch as dataframe
df = con.execute(query).fetchdf()

# plot with altair
chart = (
    alt.Chart(df)
    .mark_line(point=True)
    .encode(
        x=alt.X("day:T", title="Date"),
        y=alt.Y("total_revenue:Q", title="Total Revenue"),
        tooltip=["day:T", "total_revenue:Q"],
    )
    .properties(title="Total Revenue per Day", width=700, height=400)
)

chart.show()

output_path = project_root / "linegraph.html"
chart.save(str(output_path))
print(f"Saved chart to {output_path}")
