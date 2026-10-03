from __future__ import annotations

import re
from datetime import datetime
from math import isfinite
from uuid import uuid4

from sqlalchemy.orm import Session

from ai.syllabus.mapper import map_and_format
from app.models.academic import (
    Course,
    LectureLog,
    SyllabusTopic,
    SyllabusUnit,
)


# Keep execution at least as conservative as the syllabus mapper.
MIN_EXECUTION_MATCH_SCORE = 0.15


def _normalize_text(value: str | None) -> str:
    if not value:
        return ""

    return " ".join(
        str(value)
        .lower()
        .strip()
        .split()
    )


def _parse_duration(
    duration_value,
) -> int:
    """
    Convert common duration formats into minutes.

    Missing/invalid duration is stored as 0.
    """

    if duration_value is None:
        return 0

    if isinstance(
        duration_value,
        (int, float),
    ):
        return max(
            0,
            int(duration_value),
        )

    text = str(
        duration_value
    ).strip().lower()

    if not text:
        return 0

    if text.isdigit():
        return int(text)

    minute_match = re.search(
        r"(\d+)\s*(?:m|min|mins|minute|minutes)\b",
        text,
    )

    if minute_match:
        return int(
            minute_match.group(1)
        )

    hour_match = re.search(
        r"(\d+(?:\.\d+)?)\s*(?:h|hr|hrs|hour|hours)\b",
        text,
    )

    if hour_match:
        return int(
            float(hour_match.group(1))
            * 60
        )

    return 0


def _normalize_date(
    date_value,
) -> str:
    if date_value:
        return str(date_value)

    return datetime.now().strftime(
        "%Y-%m-%d"
    )


def _find_duplicate_lecture(
    db: Session,
    course_id: str,
    date: str,
    description: str,
) -> LectureLog | None:
    """
    Detect an exact duplicate lecture submission.

    This protects against:
    - double-clicking confirm
    - mobile retry
    - repeated API requests
    """

    normalized_description = (
        _normalize_text(description)
    )

    lectures = (
        db.query(LectureLog)
        .filter(
            LectureLog.course_id
            == course_id,
            LectureLog.date == date,
        )
        .all()
    )

    for lecture in lectures:
        if (
            _normalize_text(
                lecture.description
            )
            == normalized_description
        ):
            return lecture

    return None


def _recalculate_course_progress(
    db: Session,
    course: Course,
) -> dict:
    """
    Recalculate syllabus progress and
    teaching pace from current DB state.
    """

    units = (
        db.query(SyllabusUnit)
        .filter(
            SyllabusUnit.course_id
            == course.id
        )
        .all()
    )

    total_topics = 0
    completed_topics = 0

    unit_results = []

    for unit in units:
        topics = (
            db.query(SyllabusTopic)
            .filter(
                SyllabusTopic.unit_id
                == unit.id
            )
            .all()
        )

        unit_total = len(topics)

        unit_completed = sum(
            1
            for topic in topics
            if topic.completed
        )

        if unit_total > 0:
            unit_progress = round(
                (
                    unit_completed
                    / unit_total
                )
                * 100,
                2,
            )
        else:
            unit_progress = 0.0

        unit.progress = unit_progress

        total_topics += unit_total
        completed_topics += (
            unit_completed
        )

        unit_results.append(
            {
                "unit_id": unit.id,
                "unit_name": unit.name,
                "progress": unit_progress,
                "completed_topics": (
                    unit_completed
                ),
                "total_topics": unit_total,
            }
        )

    if total_topics > 0:
        course_progress = round(
            (
                completed_topics
                / total_topics
            )
            * 100,
            2,
        )
    else:
        course_progress = 0.0

    # Keep the cached Course.progress field
    # synchronized for legacy compatibility.
    course.progress = course_progress

    # The lecture has already been flushed
    # before this function is called.
    lecture_count = (
        db.query(LectureLog)
        .filter(
            LectureLog.course_id
            == course.id
        )
        .count()
    )

    if lecture_count > 0:
        course.current_pace = round(
            completed_topics
            / lecture_count,
            2,
        )
    else:
        course.current_pace = 0.0

    return {
        "course_progress": course_progress,
        "completed_topics": (
            completed_topics
        ),
        "total_topics": total_topics,
        "lecture_count": lecture_count,
        "current_pace": (
            course.current_pace
        ),
        "units": unit_results,
    }


def _validate_mapping_matches(
    matches: list,
) -> list[dict]:
    """
    Validate and normalize mapper results before
    allowing them to mutate syllabus state.

    Rules:
    - result must be a dictionary
    - topic ID must exist
    - score must be numeric and finite
    - score must meet MIN_EXECUTION_MATCH_SCORE
    - duplicate topic IDs are removed
    - results are returned in descending score order
    """

    validated_matches = []
    seen_topic_ids = set()

    for match in matches or []:
        if not isinstance(match, dict):
            continue

        topic_id = (
            match.get("topic_id")
            or match.get("id")
        )

        if not topic_id:
            continue

        topic_id = str(topic_id)

        if topic_id in seen_topic_ids:
            continue

        raw_score = match.get(
            "score",
            0.0,
        )

        try:
            score = float(raw_score)
        except (
            TypeError,
            ValueError,
        ):
            continue

        if not isfinite(score):
            continue

        if score < MIN_EXECUTION_MATCH_SCORE:
            continue

        # Cosine-style mapper scores should normally
        # be within [0, 1]. Reject malformed values.
        if score > 1.0:
            continue

        normalized_match = dict(match)

        normalized_match["topic_id"] = (
            topic_id
        )
        normalized_match["score"] = round(
            score,
            4,
        )

        validated_matches.append(
            normalized_match
        )
        seen_topic_ids.add(topic_id)

    validated_matches.sort(
        key=lambda item: item["score"],
        reverse=True,
    )

    return validated_matches


def execute_log_lecture_action(
    action_plan: dict,
    db: Session,
    lecturer_id: str = "lecturer_001",
) -> dict:
    """
    Execute a confirmed log_lecture action.

    Steps:
    1. Validate proposal
    2. Prevent duplicate execution
    3. Re-run syllabus mapping
    4. Validate mapping confidence
    5. Validate matched topics belong to the course
    6. Create LectureLog
    7. Mark newly matched topics complete
    8. Flush the lecture into the DB
    9. Recalculate academic state
    10. Commit transaction
    """

    proposal = action_plan.get(
        "proposal"
    )

    if not proposal:
        return {
            "status": "error",
            "message": (
                "The lecture action does not "
                "contain a valid proposal."
            ),
        }

    course_id = proposal.get(
        "course_id"
    )

    topic = proposal.get(
        "topic"
    )

    date = _normalize_date(
        proposal.get("date")
    )

    duration = _parse_duration(
        proposal.get("duration")
    )

    if not course_id:
        return {
            "status": "error",
            "message": "Course is required.",
        }

    if not topic:
        return {
            "status": "error",
            "message": (
                "Lecture topic is required."
            ),
        }

    course = (
        db.query(Course)
        .filter(
            Course.id == course_id
        )
        .first()
    )

    if not course:
        return {
            "status": "error",
            "message": (
                f"Course '{course_id}' "
                "was not found."
            ),
        }

    # -------------------------------------------------
    # DUPLICATE PROTECTION
    # -------------------------------------------------

    duplicate = _find_duplicate_lecture(
        db=db,
        course_id=course_id,
        date=date,
        description=topic,
    )

    if duplicate:
        return {
            "status": "already_executed",
            "message": (
                "This lecture has already "
                "been recorded."
            ),
            "lecture": {
                "id": duplicate.id,
                "date": duplicate.date,
                "duration": duplicate.duration,
                "description": (
                    duplicate.description
                ),
                "course_id": (
                    duplicate.course_id
                ),
            },
        }

    # -------------------------------------------------
    # RE-RUN SYLLABUS MAPPING
    # -------------------------------------------------
    #
    # Important:
    # We intentionally re-run the mapper at execution
    # time instead of trusting stale proposal data.
    # -------------------------------------------------

    mapping_result = map_and_format(
        db=db,
        course_id=course_id,
        lecture_description=topic,
        top_k=5,
        min_score=MIN_EXECUTION_MATCH_SCORE,
    )

    raw_matches = mapping_result.get(
        "matches",
        [],
    )

    matches = _validate_mapping_matches(
        raw_matches
    )

    # -------------------------------------------------
    # MAPPING SAFETY GATE
    # -------------------------------------------------
    #
    # Never create a lecture record or mutate syllabus
    # state when the lecture cannot be confidently mapped.
    # -------------------------------------------------

    if not matches:
        return {
            "status": "mapping_failed",
            "message": (
                "The lecture could not be mapped "
                "confidently to a syllabus topic. "
                "No lecture record was created."
            ),
            "mapping": {
                "matches": [],
                "mapping_status": (
                    mapping_result.get(
                        "mapping_status"
                    )
                ),
                "mapping_error": (
                    mapping_result.get(
                        "mapping_error"
                    )
                ),
                "minimum_score": (
                    MIN_EXECUTION_MATCH_SCORE
                ),
            },
        }

    # -------------------------------------------------
    # VALIDATE TOPIC IDS
    # -------------------------------------------------

    matched_topic_ids = [
        match["topic_id"]
        for match in matches
    ]

    # SyllabusTopic is related to a course through
    # SyllabusUnit, so explicitly validate that every
    # matched topic belongs to this course.
    topics = (
        db.query(SyllabusTopic)
        .join(
            SyllabusUnit,
            SyllabusTopic.unit_id
            == SyllabusUnit.id,
        )
        .filter(
            SyllabusTopic.id.in_(
                matched_topic_ids
            ),
            SyllabusUnit.course_id
            == course_id,
        )
        .all()
    )

    topic_by_id = {
        str(syllabus_topic.id): syllabus_topic
        for syllabus_topic in topics
    }

    missing_topic_ids = [
        topic_id
        for topic_id in matched_topic_ids
        if topic_id not in topic_by_id
    ]

    # Never allow a mapper result pointing to a topic
    # outside the requested course to mutate the database.
    if missing_topic_ids:
        return {
            "status": "mapping_failed",
            "message": (
                "One or more mapped syllabus topics "
                "could not be verified for this course. "
                "No lecture record was created."
            ),
            "mapping": {
                "matches": matches,
                "invalid_topic_ids": (
                    missing_topic_ids
                ),
                "course_id": course_id,
            },
        }

    # Reorder according to mapper confidence.
    verified_topics = [
        topic_by_id[topic_id]
        for topic_id in matched_topic_ids
    ]

    # -------------------------------------------------
    # CREATE LECTURE
    # -------------------------------------------------

    lecture = LectureLog(
        id=uuid4().hex,
        date=date,
        duration=duration,
        description=topic,
        course_id=course_id,
    )

    db.add(lecture)

    # -------------------------------------------------
    # MARK SYLLABUS TOPICS
    # -------------------------------------------------

    completed_topic_names = []

    for syllabus_topic in verified_topics:
        if not syllabus_topic.completed:
            syllabus_topic.completed = True

            completed_topic_names.append(
                syllabus_topic.name
            )

    # -------------------------------------------------
    # IMPORTANT:
    # Flush before calculating lecture_count.
    # -------------------------------------------------

    db.flush()

    # -------------------------------------------------
    # RECALCULATE ACADEMIC STATE
    # -------------------------------------------------

    academic_state = (
        _recalculate_course_progress(
            db=db,
            course=course,
        )
    )

    db.commit()

    db.refresh(lecture)
    db.refresh(course)

    return {
        "status": "executed",
        "lecture": {
            "id": lecture.id,
            "date": lecture.date,
            "duration": lecture.duration,
            "description": (
                lecture.description
            ),
            "course_id": (
                lecture.course_id
            ),
        },
        "syllabus": {
            "matches": matches,
            "topics_marked_completed": (
                completed_topic_names
            ),
        },
        "academic_state": (
            academic_state
        ),
    }


def execute_action(
    action_plan: dict,
    db: Session,
    lecturer_id: str = "lecturer_001",
) -> dict:
    """
    Execute a confirmed action.

    Currently supported:
        log_lecture
    """

    action = action_plan.get(
        "action"
    )

    if action != "log_lecture":
        return {
            "status": "not_supported",
            "message": (
                f"Execution for '{action}' "
                "has not been implemented yet."
            ),
        }

    return execute_log_lecture_action(
        action_plan=action_plan,
        db=db,
        lecturer_id=lecturer_id,
    )