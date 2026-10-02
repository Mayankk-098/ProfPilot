from __future__ import annotations

import re
from datetime import date, datetime, time, timedelta


WEEKDAYS = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}


def normalize_date(
    value: str | None,
    reference_date: date | None = None,
) -> date | None:
    """
    Convert natural-language dates into a concrete date.

    Supported examples:
    - today
    - tomorrow
    - yesterday
    - kal
    - aaj
    - Monday
    - Friday
    - YYYY-MM-DD
    """
    if not value:
        return None

    if reference_date is None:
        reference_date = datetime.now().date()

    text = value.lower().strip()

    # Remove possessive suffixes accidentally attached
    # by natural language.
    text = re.sub(
        r"'s$",
        "",
        text,
    )

    # English / Hinglish relative dates.
    if text in {"today", "aaj"}:
        return reference_date

    if text in {"tomorrow", "kal"}:
        return reference_date + timedelta(days=1)

    if text in {"yesterday", "kal"}:
        return reference_date - timedelta(days=1)

    # ISO date.
    try:
        return datetime.strptime(
            text,
            "%Y-%m-%d",
        ).date()
    except ValueError:
        pass

    # Day of week: choose the next occurrence.
    if text in WEEKDAYS:
        target = WEEKDAYS[text]
        current = reference_date.weekday()

        days_ahead = (
            target - current
        ) % 7

        # If today is the requested weekday,
        # interpret it as today's occurrence.
        return reference_date + timedelta(
            days=days_ahead
        )

    return None


def normalize_time(
    value: str | None,
) -> time | None:
    """
    Convert natural-language clock times to datetime.time.
    """
    if not value:
        return None

    text = value.lower().strip()

    text = text.replace(".", "")
    text = text.replace(" ", " ")

    # 10:30 AM / 10 AM / 2 PM
    match = re.fullmatch(
        r"(\d{1,2})(?::(\d{2}))?\s*([ap]m)?",
        text,
    )

    if match:
        hour = int(match.group(1))
        minute = int(
            match.group(2)
            or 0
        )
        meridiem = match.group(3)

        if meridiem:
            if not 1 <= hour <= 12:
                return None

            if meridiem == "pm" and hour != 12:
                hour += 12

            if meridiem == "am" and hour == 12:
                hour = 0
        else:
            if not 0 <= hour <= 23:
                return None

        if not 0 <= minute <= 59:
            return None

        return time(
            hour=hour,
            minute=minute,
        )

    # Simple Hindi/Hinglish forms:
    # "2 baje", "2:30 baje"
    match = re.fullmatch(
        r"(\d{1,2})(?::(\d{2}))?\s*baje",
        text,
    )

    if match:
        hour = int(match.group(1))
        minute = int(
            match.group(2)
            or 0
        )

        if not 0 <= hour <= 23:
            return None

        if not 0 <= minute <= 59:
            return None

        return time(
            hour=hour,
            minute=minute,
        )

    return None


def format_date(value: date | None) -> str | None:
    if value is None:
        return None

    return value.strftime(
        "%Y-%m-%d"
    )


def format_time(value: time | None) -> str | None:
    if value is None:
        return None

    return value.strftime(
        "%H:%M"
    )


def resolve_temporal_entities(
    nlp_analysis: dict | None,
    reference_date: date | None = None,
) -> dict:
    """
    Resolve DATE/TIME/NEW_DATE/NEW_TIME entities
    extracted by the NLP layer.
    """
    if not nlp_analysis:
        return {
            "date": None,
            "new_date": None,
            "time": None,
            "new_time": None,
        }

    entities = nlp_analysis.get(
        "entities",
        [],
    )

    raw_date = None
    raw_new_date = None
    raw_time = None
    raw_new_time = None

    for entity in entities:
        label = entity.get("label")
        text = entity.get("text")

        if label == "DATE":
            raw_date = text

        elif label == "NEW_DATE":
            raw_new_date = text

        elif label == "TIME":
            raw_time = text

        elif label == "NEW_TIME":
            raw_new_time = text

    resolved_date = normalize_date(
        raw_date,
        reference_date,
    )

    resolved_new_date = normalize_date(
        raw_new_date,
        reference_date,
    )

    resolved_time = normalize_time(
        raw_time,
    )

    resolved_new_time = normalize_time(
        raw_new_time,
    )

    return {
        "date": format_date(
            resolved_date
        ),
        "new_date": format_date(
            resolved_new_date
        ),
        "time": format_time(
            resolved_time
        ),
        "new_time": format_time(
            resolved_new_time
        ),
        "raw": {
            "date": raw_date,
            "new_date": raw_new_date,
            "time": raw_time,
            "new_time": raw_new_time,
        },
    }