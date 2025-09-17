import tempfile
from pathlib import Path

import altair as alt
import chainlit as cl
import pandas as pd


@cl.on_chat_start
async def start():
    df = pd.DataFrame({"x": ["A", "B", "C"], "y": [2, 1, 3]})

    chart = (
        alt.Chart(df)
        .mark_bar()
        .encode(x="x", y="y")
        .properties(title="Altair chart (PNG)")
    )

    # Save chart to a temporary PNG using the vl-convert backend
    # Requires: uv add altair_saver vl-convert-python
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    tmp_path = Path(tmp.name)
    tmp.close()

    # Either of these works once the saver backend is available:
    # 1) Native Altair save:
    chart.save(str(tmp_path), format="png")

    # 2) Or altair_saver (uncomment if you prefer):
    # from altair_saver import save
    # save(chart, str(tmp_path), fmt="png")

    await cl.Message(
        content="Here is the Altair chart as a PNG:",
        elements=[cl.Image(name="altair_chart", path=str(tmp_path), display="inline")],
    ).send()
