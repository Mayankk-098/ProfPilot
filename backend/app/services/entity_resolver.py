from __future__ import annotations

import re

from sqlalchemy.orm import Session

from app.models.academic import Course
from app.services.temporal_resolver import (
    resolve_temporal_entities,
)


def normalize_text(
    value: str | None,
) -> str:
    if not value:
        return ""

    return " ".join(
        value.lower().strip().split()
    )


def extract_entity(
    nlp_analysis: dict | None,
    label: str,
) -> str | None:
    if not nlp_analysis:
        return None

    values = []

    for entity in nlp_analysis.get(
        "entities",
        [],
    ):
        if entity.get("label") == label:
            text = entity.get("text")

            if text:
                values.append(text)

    if not values:
        return None

    # Preserve multiple entities of the same type.
    return " ".join(values)


def extract_lecture_topic(
    nlp_analysis: dict | None,
) -> str | None:
    """
    Recover the full lecture topic phrase for log_lecture
    requests.

    The trained NER model may only tag one part of a
    multi-word/multi-concept lecture description.

    Example:
        "Log today's DBMS lecture on functional dependencies
         and normalization"

    NER might detect:
        TOPIC = normalization

    This fallback recovers:
        functional dependencies and normalization
    """

    if not nlp_analysis:
        return None

    text = nlp_analysis.get(
        "text",
        "",
    ).strip()

    if not text:
        return None

    intent = nlp_analysis.get(
        "intent"
    )

    if intent != "log_lecture":
        return None

    patterns = [
        r"(?:lecture|class)\s+(?:on|about|covering|regarding)\s+(.+)$",
        r"(?:lecture|class)\s*[:\-]\s*(.+)$",
    ]

    for pattern in patterns:
        match = re.search(
            pattern,
            text,
            flags=re.IGNORECASE,
        )

        if match:
            topic = match.group(1).strip()

            # Remove trailing punctuation.
            topic = topic.rstrip(
                " .,!?"
            )

            if topic:
                return topic

    return None


def resolve_course_id(
    db: Session,
    course_text: str | None,
) -> str | None:
    """
    Resolve a model-extracted course name/code
    to the actual database course ID.
    """

    if not course_text:
        return None

    query = normalize_text(
        course_text
    )

    courses = (
        db.query(Course)
        .all()
    )

    # Exact matching first.
    for course in courses:
        candidates = {
            normalize_text(course.id),
            normalize_text(course.code),
            normalize_text(course.short_name),
            normalize_text(course.name),
        }

        if query in candidates:
            return course.id

    # Natural-language substring fallback.
    for course in courses:
        fields = [
            normalize_text(course.code),
            normalize_text(course.short_name),
            normalize_text(course.name),
        ]

        if any(
            query in field
            or field in query
            for field in fields
            if field
        ):
            return course.id

    return None


def resolve_entities(
    db: Session,
    nlp_analysis: dict | None,
    fallback_course_id: str | None = None,
) -> dict:
    """
    Convert raw NLP entities into canonical academic values.
    """

    course_text = extract_entity(
        nlp_analysis,
        "COURSE",
    )

    date_text = extract_entity(
        nlp_analysis,
        "DATE",
    )

    new_date_text = extract_entity(
        nlp_analysis,
        "NEW_DATE",
    )

    time_text = extract_entity(
        nlp_analysis,
        "TIME",
    )

    new_time_text = extract_entity(
        nlp_analysis,
        "NEW_TIME",
    )

    batch_text = extract_entity(
        nlp_analysis,
        "BATCH",
    )

    # First use the learned TOPIC entity.
    topic_text = extract_entity(
        nlp_analysis,
        "TOPIC",
    )

    # For lecture logging, recover the complete
    # lecture subject phrase when the NER model
    # captured only part of it.
    full_lecture_topic = extract_lecture_topic(
        nlp_analysis
    )

    if full_lecture_topic:
        topic_text = full_lecture_topic

    room_text = extract_entity(
        nlp_analysis,
        "ROOM",
    )

    threshold_text = extract_entity(
        nlp_analysis,
        "THRESHOLD",
    )

    duration_text = extract_entity(
        nlp_analysis,
        "DURATION",
    )

    resolved_course_id = resolve_course_id(
        db=db,
        course_text=course_text,
    )

    temporal = resolve_temporal_entities(
        nlp_analysis=nlp_analysis,
    )

    return {
        "course_id": (
            resolved_course_id
            or fallback_course_id
        ),

        "course_text": course_text,

        "date_text": date_text,
        "new_date_text": new_date_text,

        "time_text": time_text,
        "new_time_text": new_time_text,

        "resolved_date": temporal["date"],
        "resolved_new_date": temporal["new_date"],

        "resolved_time": temporal["time"],
        "resolved_new_time": temporal["new_time"],

        "batch_text": batch_text,

        "topic_text": topic_text,

        "room_text": room_text,
        "threshold_text": threshold_text,
        "duration_text": duration_text,
    }