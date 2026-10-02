from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.academic import Course


def normalize_text(value: str | None) -> str:
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

    for entity in nlp_analysis.get("entities", []):
        if entity.get("label") == label:
            return entity.get("text")

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

    query = normalize_text(course_text)

    courses = (
        db.query(Course)
        .all()
    )

    for course in courses:
        candidates = {
            normalize_text(course.id),
            normalize_text(course.code),
            normalize_text(course.short_name),
            normalize_text(course.name),
        }

        if query in candidates:
            return course.id

    # Fallback: substring matching for natural names.
    for course in courses:
        fields = [
            normalize_text(course.code),
            normalize_text(course.short_name),
            normalize_text(course.name),
        ]

        if any(
            query in field or field in query
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

    topic_text = extract_entity(
        nlp_analysis,
        "TOPIC",
    )

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
        "batch_text": batch_text,
        "topic_text": topic_text,
        "room_text": room_text,
        "threshold_text": threshold_text,
        "duration_text": duration_text,
    }