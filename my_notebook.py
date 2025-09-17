import marimo

__generated_with = "0.15.5"
app = marimo.App(width="medium")


@app.cell
def _():
    import altair as alt
    import duckdb

    con = duckdb.connect()
    SQL = """ SELECT * FROM read_parquet('data/sales_stores_hierarchy_merged.parquet'); """
    con.sql(SQL).to_view("SALES")
    con.sql("describe SALES ").show()
    return alt, con


@app.cell
def _():
    query = """
    SELECT
        DATE_TRUNC('day', date) AS day,
        SUM(revenue) AS total_revenue
    FROM read_parquet('data/sales_stores_hierarchy_merged.parquet')
    GROUP BY day
    ORDER BY day
    """
    return (query,)


@app.cell
def _(alt, con, query):
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
    return


if __name__ == "__main__":
    app.run()
