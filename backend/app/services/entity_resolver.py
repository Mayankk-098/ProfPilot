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

    return " ".join(values)


def extract_lecture_topic(
    nlp_analysis: dict | None,
) -> str | None:
    """
    Recover the full lecture topic phrase for log_lecture
    requests.
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
    Resolve an explicitly mentioned course against
    the courses present in the database.

    Returns None when the mentioned course cannot
    be resolved.
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

    # -----------------------------------------
    # EXACT MATCH
    # -----------------------------------------

    for course in courses:
        candidates = {
            normalize_text(course.id),
            normalize_text(course.code),
            normalize_text(course.short_name),
            normalize_text(course.name),
        }

        if query in candidates:
            return course.id

    # -----------------------------------------
    # SUBSTRING MATCH
    # -----------------------------------------

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

    Course resolution rules:

    1. If the user explicitly mentions a course,
       resolve ONLY that course.

    2. If the explicit course cannot be found,
       DO NOT fall back to the contextual course.

    3. If the user does not mention a course,
       fallback_course_id may be used as context.
    """

    # -----------------------------------------
    # RAW ENTITIES
    # -----------------------------------------

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

    topic_text = extract_entity(
        nlp_analysis,
        "TOPIC",
    )

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

    # -----------------------------------------
    # COURSE RESOLUTION
    # -----------------------------------------

    resolved_course_id = resolve_course_id(
        db=db,
        course_text=course_text,
    )

    if course_text:
        # User explicitly mentioned a course.
        #
        # NEVER silently replace it with
        # fallback_course_id.
        effective_course_id = (
            resolved_course_id
        )

        course_resolution_failed = (
            resolved_course_id is None
        )

    else:
        # No explicit course mentioned.
        # Contextual fallback is safe here.
        effective_course_id = (
            fallback_course_id
        )

        course_resolution_failed = False

    # -----------------------------------------
    # TEMPORAL ENTITIES
    # -----------------------------------------

    temporal = resolve_temporal_entities(
        nlp_analysis=nlp_analysis,
    )

    # -----------------------------------------
    # RETURN
    # -----------------------------------------

    return {
        "course_id": (
            effective_course_id
        ),

        "course_text": course_text,

        "course_resolution_failed": (
            course_resolution_failed
        ),

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