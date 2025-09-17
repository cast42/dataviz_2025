from __future__ import annotations

import re

import chainlit as cl

from tree_map import (
    HIERARCHY_COLUMNS,
    create_hierarchy_chart,
    load_hierarchy_data,
    process_hierarchy_data,
)

EXAMPLE_QUESTIONS = [
    "Show the relative total revenue of hierarchy 1",
    "Which product had the highest sales in 2019?",
    "Compare stock levels between stores A and B",
]

RELATIVE_TOTAL_PATTERN = re.compile(
    r"show the relative total\s+(revenue|sales|stock)\s+of hierarchy\s*([1-5])(?:\s*[?.!])?",
    re.IGNORECASE,
)


def _extract_metric_and_level(query: str) -> tuple[str, int] | None:
    match = RELATIVE_TOTAL_PATTERN.fullmatch(query.strip())
    if not match:
        return None
    metric = match.group(1).lower()
    level = int(match.group(2))
    return metric, level


async def _send_hierarchy_treemap(level: int, metric: str) -> None:
    column = HIERARCHY_COLUMNS[level]
    metric_label = metric.capitalize()

    await cl.Message(
        content="**Step 1/3:** Obtaining the data by executing the SQL store."
    ).send()
    raw_df = load_hierarchy_data(column, metric)

    await cl.Message(
        content="**Step 2/3:** Processing the data for the treemap layout."
    ).send()
    processed_df = process_hierarchy_data(raw_df, column, metric)

    await cl.Message(
        content="**Step 3/3:** Creating the interactive Plotly treemap visualization."
    ).send()
    chart = create_hierarchy_chart(processed_df, column, metric)

    chart_element = cl.Plotly(
        name=f"hierarchy{level}_{metric}_treemap",
        figure=chart,
        display="inline",
    )

    await cl.Message(
        content=(
            f"Here is the Plotly treemap showing the relative total {metric_label} "
            f"for hierarchy {level}:"
        ),
        elements=[chart_element],
    ).send()


async def _handle_user_query(user_query: str) -> None:
    parsed = _extract_metric_and_level(user_query)
    if parsed is None:
        await cl.Message(content="This is not yet supported").send()
        return

    metric, level = parsed
    await _send_hierarchy_treemap(level, metric)


@cl.on_chat_start
async def main():
    # Send a welcome message with example question buttons
    actions = [
        cl.Action(
            name="suggested_question",
            label=q,
            payload={"query": q},
        )
        for q in EXAMPLE_QUESTIONS
    ]

    await cl.Message(
        content="Welcome! Here are some example questions you can ask:",
        actions=actions,
    ).send()


@cl.action_callback("suggested_question")
async def on_action(action: cl.Action):
    # Action triggered when a button is clicked
    user_query = action.payload.get("query", action.label)
    await cl.Message(content=f"✅ You selected: **{user_query}**").send()

    await _handle_user_query(user_query)


@cl.on_message
async def on_message(message: cl.Message):
    await _handle_user_query(message.content)
