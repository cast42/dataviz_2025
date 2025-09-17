from __future__ import annotations

import calendar
from datetime import date, datetime
import re

import chainlit as cl

from tree_map import (
    HIERARCHY_COLUMNS,
    create_hierarchy_chart,
    load_hierarchy_data,
    process_hierarchy_data,
)

EXAMPLE_QUESTIONS = [
    "Show the relative total revenue of hierarchy 1 in 2019",
    "Which product had the highest sales in 2019?",
    "Compare stock levels between stores A and B",
]

RELATIVE_TOTAL_PATTERN = re.compile(
    r"show the relative total\s+(revenue|sales|stock)\s+of hierarchy\s*([1-5])(?:\s+(.*))?$",
    re.IGNORECASE,
)

BETWEEN_PATTERN = re.compile(
    r"between\s+(.+?)\s+and\s+(.+?)(?:$|[?.!])",
    re.IGNORECASE,
)

MONTH_YEAR_PATTERN = re.compile(
    r"in\s+([a-zA-Z]+)\s+(\d{4})(?:$|[?.!])",
    re.IGNORECASE,
)

QUARTER_PATTERN = re.compile(
    r"in\s+q([1-4])(?:\s+of)?\s+(\d{4})(?:$|[?.!])",
    re.IGNORECASE,
)

YEAR_PATTERN = re.compile(
    r"in\s+(\d{4})(?:$|[?.!])",
    re.IGNORECASE,
)

DATE_INPUT_FORMATS = ("%d-%m-%Y", "%d/%m/%Y", "%Y-%m-%d", "%Y/%m/%d")

MONTH_ALIASES = {
    name: index
    for index, name in enumerate(
        [
            "january",
            "february",
            "march",
            "april",
            "may",
            "june",
            "july",
            "august",
            "september",
            "october",
            "november",
            "december",
        ],
        start=1,
    )
}

MONTH_ALIASES.update({name[:3]: value for name, value in MONTH_ALIASES.items()})
MONTH_ALIASES["sept"] = 9


def _format_display_date(value: date) -> str:
    return value.strftime("%d-%m-%Y")


def _parse_date_literal(value: str) -> date | None:
    cleaned = value.strip().rstrip(".,")
    normalized = cleaned.replace(".", "-")

    for fmt in DATE_INPUT_FORMATS:
        try:
            return datetime.strptime(normalized, fmt).date()
        except ValueError:
            continue
    return None


def _month_from_name(name: str) -> int | None:
    return MONTH_ALIASES.get(name.strip().lower())


def _parse_between_range(text: str) -> tuple[date, date, str] | None:
    match = BETWEEN_PATTERN.search(text)
    if not match:
        return None

    start_raw, end_raw = match.group(1), match.group(2)
    start = _parse_date_literal(start_raw)
    end = _parse_date_literal(end_raw)
    if not start or not end:
        return None

    if start > end:
        start, end = end, start

    phrase = f"between {_format_display_date(start)} and {_format_display_date(end)}"
    return start, end, phrase


def _parse_quarter_range(text: str) -> tuple[date, date, str] | None:
    match = QUARTER_PATTERN.search(text)
    if not match:
        return None

    quarter = int(match.group(1))
    year = int(match.group(2))
    start_month = 3 * (quarter - 1) + 1
    end_month = start_month + 2

    start = date(year, start_month, 1)
    end_day = calendar.monthrange(year, end_month)[1]
    end = date(year, end_month, end_day)

    phrase = f"in Q{quarter} {year}"
    return start, end, phrase


def _parse_month_year_range(text: str) -> tuple[date, date, str] | None:
    match = MONTH_YEAR_PATTERN.search(text)
    if not match:
        return None

    month_name = match.group(1)
    month = _month_from_name(month_name)
    if not month:
        return None

    year = int(match.group(2))
    start = date(year, month, 1)
    end_day = calendar.monthrange(year, month)[1]
    end = date(year, month, end_day)

    phrase = f"in {calendar.month_name[month]} {year}"
    return start, end, phrase


def _parse_year_range(text: str) -> tuple[date, date, str] | None:
    match = YEAR_PATTERN.search(text)
    if not match:
        return None

    year = int(match.group(1))
    start = date(year, 1, 1)
    end = date(year, 12, 31)
    phrase = f"in {year}"
    return start, end, phrase


def _parse_time_range(segment: str) -> tuple[date, date, str] | None:
    if not segment:
        return None

    text = segment.strip()

    for parser in (
        _parse_between_range,
        _parse_quarter_range,
        _parse_month_year_range,
        _parse_year_range,
    ):
        parsed = parser(text)
        if parsed:
            return parsed

    return None


def _extract_metric_level_and_dates(
    query: str,
) -> tuple[str, int, date, date, str] | None:
    match = RELATIVE_TOTAL_PATTERN.fullmatch(query.strip())
    if not match:
        return None

    metric = match.group(1).lower()
    level = int(match.group(2))
    remainder = (match.group(3) or "").strip()

    time_range = _parse_time_range(remainder)
    if not time_range:
        return None

    start_date, end_date, phrase = time_range
    return metric, level, start_date, end_date, phrase


async def _send_alternative_prompt(
    level: int,
    metric: str,
    start_date: date,
    end_date: date,
    range_phrase: str,
) -> None:
    alt_metric = "sales" if metric != "sales" else "stock"
    fallback_phrase = (
        range_phrase
        if range_phrase
        else f"between {_format_display_date(start_date)} and {_format_display_date(end_date)}"
    )
    example_query = (
        f"Show the relative total {alt_metric} of hierarchy {level} {fallback_phrase}"
    )

    await cl.Message(
        content=(
            f"Instead of {metric}, I can also generate a treemap for {alt_metric}. "
            f"For example, asking '{example_query}' also works."
        )
    ).send()


async def _send_hierarchy_treemap(
    level: int,
    metric: str,
    start_date: date,
    end_date: date,
    range_phrase: str,
) -> None:
    column = HIERARCHY_COLUMNS[level]
    metric_label = metric.capitalize()

    await cl.Message(
        content="**Step 1/3:** Obtaining the data by executing the SQL store."
    ).send()
    raw_df = load_hierarchy_data(column, metric, start_date, end_date)

    if raw_df.empty:
        await cl.Message(
            content=(
                f"No data between {_format_display_date(start_date)} and "
                f"{_format_display_date(end_date)}"
            )
        ).send()
        return

    await cl.Message(
        content="**Step 2/3:** Processing the data for the treemap layout."
    ).send()
    processed_df = process_hierarchy_data(raw_df, column, metric)

    await cl.Message(
        content="**Step 3/3:** Creating the interactive Plotly treemap visualization."
    ).send()
    chart = create_hierarchy_chart(processed_df, column, metric)

    range_suffix = f" {range_phrase.strip()}" if range_phrase else ""
    chart_element = cl.Plotly(
        name=f"hierarchy{level}_{metric}_treemap",
        figure=chart,
        display="inline",
    )

    await cl.Message(
        content=(
            f"Here is the Plotly treemap showing the relative total {metric_label} "
            f"for hierarchy {level}{range_suffix}:"
        ),
        elements=[chart_element],
    ).send()

    await _send_alternative_prompt(level, metric, start_date, end_date, range_phrase)


async def _handle_user_query(user_query: str) -> None:
    parsed = _extract_metric_level_and_dates(user_query)
    if not parsed:
        await cl.Message(content="This is not yet supported").send()
        return

    metric, level, start_date, end_date, range_phrase = parsed
    await _send_hierarchy_treemap(level, metric, start_date, end_date, range_phrase)


@cl.on_chat_start
async def main():
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
    user_query = action.payload.get("query", action.label)
    await cl.Message(content=f"✅ You selected: **{user_query}**").send()

    await _handle_user_query(user_query)


@cl.on_message
async def on_message(message: cl.Message):
    await _handle_user_query(message.content)
