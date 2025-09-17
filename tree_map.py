import marimo

__generated_with = "0.15.5"
app = marimo.App(width="medium")


@app.cell
def _():
    import duckdb
    import altair as alt

    con = duckdb.connect()
    SQL = ''' SELECT * FROM read_parquet('data/sales_stores_hierarchy_merged.parquet'); '''
    con.sql(SQL).to_view("SALES")
    con.sql('describe SALES ').show()
    return alt, con


@app.cell
def _():
    query = """
    SELECT
        hierarchy1_id,
        SUM(revenue) AS total_revenue
    FROM read_parquet('data/sales_stores_hierarchy_merged.parquet')
    GROUP BY hierarchy1_id
    """
    return (query,)


@app.cell
def _(con, query):
    df = con.execute(query).fetchdf()
    df
    return (df,)


@app.cell
def _(df):
    print(df.to_markdown(index=False))
    return


@app.cell
def _(alt, df):
    import squarify

    values = df["total_revenue"].tolist()
    normed = squarify.normalize_sizes(values, 100, 100)
    rects = squarify.squarify(normed, 0, 0, 100, 100)

    # Add rectangle info to dataframe
    for i, r in enumerate(rects):
        df.loc[i, "x"] = r['x']
        df.loc[i, "y"] = r['y']
        df.loc[i, "dx"] = r['dx']
        df.loc[i, "dy"] = r['dy']

    df["x2"] = df["x"] + df["dx"]
    df["y2"] = df["y"] + df["dy"]

    # Now plot with Altair
    chart = (
        alt.Chart(df)
        # Get the grand total once and attach it to every row
        .transform_joinaggregate(
            total_sum='sum(total_revenue)'
        )
        # Compute a formatted percent string like "27%"
        .transform_calculate(
            share="format(datum.total_revenue / datum.total_sum, '.0%')"
        )
        .mark_rect()
        .encode(
            x=alt.X("x:Q", scale=alt.Scale(domain=[0, 100]), axis=None),
            y=alt.Y("y:Q", scale=alt.Scale(domain=[0, 100]), axis=None),
            x2="x2:Q",
            y2="y2:Q",
            color="total_revenue:Q",
            tooltip=[
                alt.Tooltip("hierarchy1_id:N", title="Category"),
                alt.Tooltip("total_revenue:Q", title="Revenue (€)", format=",.0f"),
                alt.Tooltip("share:N", title="Share"),  # e.g. "27%"
            ],
        )
        # .properties(width=500, height=500)
    )

    chart
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
