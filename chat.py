from __future__ import annotations

import chainlit as cl

from tree_map import (
    create_hierarchy1_chart,
    load_hierarchy1_data,
    process_hierarchy1_data,
)

EXAMPLE_QUESTIONS = [
    "Show the relative total revenue of hierarchy 1",
    "Which product had the highest sales in 2019?",
    "Compare stock levels between stores A and B",
]


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

    if user_query == EXAMPLE_QUESTIONS[0]:
        await cl.Message(
            content="**Step 1/3:** Obtaining the data by executing the SQL store."
        ).send()
        raw_df = load_hierarchy1_data()

        await cl.Message(
            content="**Step 2/3:** Processing the data for the treemap layout."
        ).send()
        processed_df = process_hierarchy1_data(raw_df)

        await cl.Message(
            content="**Step 3/3:** Creating the interactive Plotly treemap visualization."
        ).send()
        chart = create_hierarchy1_chart(processed_df)

        chart_element = cl.Plotly(
            name="hierarchy1_treemap",
            figure=chart,
            display="inline",
        )

        await cl.Message(
            content="Here is the Plotly treemap showing the relative total revenue for hierarchy 1:",
            elements=[chart_element],
        ).send()
    else:
        await cl.Message(content=f"🔎 Answering: {user_query} ...").send()
