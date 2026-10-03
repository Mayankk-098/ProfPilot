from __future__ import annotations

from collections import Counter
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from ai.syllabus.mapper import map_and_format
from app.models.academic import (
    Course,
    LectureLog,
    SyllabusTopic,
    SyllabusUnit,
)


# Historical state should only use reasonably
# strong syllabus matches.
DEFAULT_MAPPING_THRESHOLD = 0.10


def _get_course(
    db: Session,
    course_id: str,
) -> Course | None:
    return (
        db.query(Course)
        .filter(
            Course.id == course_id
        )
        .first()
    )


def _get_topics(
    db: Session,
    course_id: str,
) -> list[SyllabusTopic]:
    return (
        db.query(SyllabusTopic)
        .join(
            SyllabusUnit,
            SyllabusTopic.unit_id
            == SyllabusUnit.id,
        )
        .filter(
            SyllabusUnit.course_id
            == course_id
        )
        .all()
    )


def _get_units(
    db: Session,
    course_id: str,
) -> list[SyllabusUnit]:
    return (
        db.query(SyllabusUnit)
        .filter(
            SyllabusUnit.course_id
            == course_id
        )
        .all()
    )


def _parse_lecture_date(
    value: str | None,
) -> datetime:
    """
    Parse the two date formats currently present
    in the database.

    Supported:
        2026-10-02
        18 September 2026

    Unknown formats are placed at the end.
    """

    if not value:
        return datetime.max

    text = str(value).strip()

    formats = (
        "%Y-%m-%d",
        "%d %B %Y",
        "%d %b %Y",
    )

    for fmt in formats:
        try:
            return datetime.strptime(
                text,
                fmt,
            )
        except ValueError:
            continue

    return datetime.max


def _get_lectures(
    db: Session,
    course_id: str,
) -> list[LectureLog]:
    """
    Return lectures in actual chronological order.
    """

    lectures = (
        db.query(LectureLog)
        .filter(
            LectureLog.course_id
            == course_id
        )
        .all()
    )

    return sorted(
        lectures,
        key=lambda lecture: (
            _parse_lecture_date(
                lecture.date
            ),
            lecture.id or "",
        ),
    )


def _build_topic_lookup(
    topics: list[SyllabusTopic],
) -> dict[str, SyllabusTopic]:
    return {
        topic.id: topic
        for topic in topics
    }


def _map_lecture(
    db: Session,
    course_id: str,
    lecture: LectureLog,
    topic_lookup: dict[str, SyllabusTopic],
    score_threshold: float,
) -> dict[str, Any]:
    """
    Map one lecture to syllabus topics and discard
    weak lexical matches.
    """

    try:
        mapping = map_and_format(
            db=db,
            course_id=course_id,
            lecture_description=(
                lecture.description
            ),
            top_k=5,
        )
    except Exception as exc:
        return {
            "lecture_id": lecture.id,
            "date": lecture.date,
            "description": lecture.description,
            "matches": [],
            "new_topic_ids": [],
            "mapping_status": "error",
            "mapping_error": str(exc),
        }

    matches = mapping.get(
        "matches",
        [],
    )

    valid_matches = []

    for match in matches:
        topic_id = (
            match.get("topic_id")
            or match.get("id")
        )

        if not topic_id:
            continue

        if topic_id not in topic_lookup:
            continue

        score = float(
            match.get(
                "score",
                0.0,
            )
        )

        if score < score_threshold:
            continue

        topic = topic_lookup[
            topic_id
        ]

        valid_matches.append(
            {
                "topic_id": topic_id,
                "topic": match.get(
                    "topic",
                    topic.name,
                ),
                "unit": match.get(
                    "unit"
                ),
                "score": score,
            }
        )

    return {
        "lecture_id": lecture.id,
        "date": lecture.date,
        "description": lecture.description,
        "matches": valid_matches,
        "new_topic_ids": [],
        "mapping_status": (
            "matched"
            if valid_matches
            else "no_match"
        ),
    }


def build_course_state(
    db: Session,
    course_id: str,
    mapping_threshold: float = (
        DEFAULT_MAPPING_THRESHOLD
    ),
    recent_lecture_window: int = 5,
) -> dict[str, Any]:
    """
    Build a read-only academic state for a course.

    Combines:
        - syllabus structure
        - completion state
        - lecture history
        - lecture -> syllabus mappings
        - actual progress
        - observed teaching pace
        - recent teaching pace
        - syllabus drift
        - evidence/provenance

    This function never mutates the database.
    """

    course = _get_course(
        db=db,
        course_id=course_id,
    )

    if not course:
        return {
            "status": "not_found",
            "course_id": course_id,
        }

    topics = _get_topics(
        db=db,
        course_id=course_id,
    )

    units = _get_units(
        db=db,
        course_id=course_id,
    )

    lectures = _get_lectures(
        db=db,
        course_id=course_id,
    )

    topic_lookup = _build_topic_lookup(
        topics
    )

    total_topics = len(topics)

    completed_topics = [
        topic
        for topic in topics
        if topic.completed
    ]

    remaining_topics = [
        topic
        for topic in topics
        if not topic.completed
    ]

    # -------------------------------------------------
    # HISTORICAL LECTURE MAPPING
    # -------------------------------------------------

    lecture_evidence = []

    observed_topic_ids: set[str] = set()

    topic_match_counts: Counter[str] = (
        Counter()
    )

    unmapped_lectures = []

    # Topics encountered before the current lecture.
    topics_seen_before: set[str] = set()

    for lecture in lectures:
        evidence = _map_lecture(
            db=db,
            course_id=course_id,
            lecture=lecture,
            topic_lookup=topic_lookup,
            score_threshold=mapping_threshold,
        )

        current_topic_ids = {
            match["topic_id"]
            for match in evidence["matches"]
        }

        # Only topics not seen in earlier lectures
        # count as newly introduced topics.
        new_topic_ids = (
            current_topic_ids
            - topics_seen_before
        )

        evidence["new_topic_ids"] = sorted(
            new_topic_ids
        )

        if not evidence["matches"]:
            unmapped_lectures.append(
                lecture.id
            )

        for topic_id in current_topic_ids:
            observed_topic_ids.add(
                topic_id
            )
            topic_match_counts[
                topic_id
            ] += 1

        topics_seen_before.update(
            current_topic_ids
        )

        lecture_evidence.append(
            evidence
        )

    # -------------------------------------------------
    # OVERALL PROGRESS
    # -------------------------------------------------

    if total_topics > 0:
        progress = round(
            (
                len(completed_topics)
                / total_topics
            )
            * 100,
            2,
        )
    else:
        progress = 0.0

    # -------------------------------------------------
    # OBSERVED COVERAGE
    # -------------------------------------------------

    observed_topic_count = len(
        observed_topic_ids
    )

    if lectures:
        observed_pace = round(
            observed_topic_count
            / len(lectures),
            2,
        )
    else:
        observed_pace = 0.0

    # -------------------------------------------------
    # NEW TOPICS PER LECTURE
    # -------------------------------------------------

    if lectures:
        new_topics_total = sum(
            len(
                evidence["new_topic_ids"]
            )
            for evidence in lecture_evidence
        )

        introduction_pace = round(
            new_topics_total
            / len(lectures),
            2,
        )
    else:
        introduction_pace = 0.0

    # -------------------------------------------------
    # RECENT PACE
    # -------------------------------------------------

    recent_evidence = (
        lecture_evidence[
            -recent_lecture_window:
        ]
    )

    recent_new_topics = sum(
        len(
            evidence["new_topic_ids"]
        )
        for evidence in recent_evidence
    )

    if recent_evidence:
        recent_pace = round(
            recent_new_topics
            / len(recent_evidence),
            2,
        )
    else:
        recent_pace = 0.0

    # -------------------------------------------------
    # REPEATED TOPICS
    # -------------------------------------------------

    repeated_topics = []

    for topic_id, count in (
        topic_match_counts.items()
    ):
        if count <= 1:
            continue

        topic = topic_lookup.get(
            topic_id
        )

        if topic:
            repeated_topics.append(
                {
                    "topic_id": topic.id,
                    "topic": topic.name,
                    "lecture_count": count,
                    "completed": (
                        topic.completed
                    ),
                }
            )

    repeated_topics.sort(
        key=lambda item: (
            -item["lecture_count"],
            item["topic"],
        )
    )

    # -------------------------------------------------
    # UNIT STATE
    # -------------------------------------------------

    unit_states = []

    for unit in units:
        unit_topics = [
            topic
            for topic in topics
            if topic.unit_id == unit.id
        ]

        unit_total = len(
            unit_topics
        )

        unit_completed = sum(
            1
            for topic in unit_topics
            if topic.completed
        )

        if unit_total:
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

        unit_remaining = [
            topic.name
            for topic in unit_topics
            if not topic.completed
        ]

        unit_states.append(
            {
                "unit_id": unit.id,
                "unit_name": unit.name,
                "progress": unit_progress,
                "completed_topics": (
                    unit_completed
                ),
                "total_topics": unit_total,
                "remaining_topics": (
                    unit_remaining
                ),
            }
        )

    # -------------------------------------------------
    # SYLLABUS DRIFT
    # -------------------------------------------------

    drift_signals = []

    if unmapped_lectures:
        drift_signals.append(
            {
                "type": "unmapped_lectures",
                "count": len(
                    unmapped_lectures
                ),
                "lecture_ids": (
                    unmapped_lectures
                ),
                "description": (
                    "Some recorded lectures could "
                    "not be confidently mapped to "
                    "the current syllabus."
                ),
            }
        )

    if repeated_topics:
        drift_signals.append(
            {
                "type": "repeated_topics",
                "topics": (
                    repeated_topics[:10]
                ),
                "description": (
                    "Some syllabus topics appear "
                    "across multiple recorded lectures."
                ),
            }
        )

    # -------------------------------------------------
    # COMPLETED WITHOUT LECTURE EVIDENCE
    # -------------------------------------------------

    completed_not_observed = [
        {
            "topic_id": topic.id,
            "topic": topic.name,
        }
        for topic in completed_topics
        if topic.id not in observed_topic_ids
    ]

    if completed_not_observed:
        drift_signals.append(
            {
                "type": (
                    "completion_without_evidence"
                ),
                "topics": (
                    completed_not_observed
                ),
                "description": (
                    "These topics are marked completed "
                    "but were not found in historical "
                    "lecture mappings."
                ),
            }
        )

    # -------------------------------------------------
    # PLAN GAP
    # -------------------------------------------------

    planned_progress = (
        float(
            course.planned_progress
        )
        if course.planned_progress
        is not None
        else 0.0
    )

    progress_gap = round(
        planned_progress - progress,
        2,
    )

    # -------------------------------------------------
    # EVIDENCE SUMMARY
    # -------------------------------------------------

    evidence_summary = {
        "mapping_threshold": (
            mapping_threshold
        ),
        "lectures_analysed": len(
            lectures
        ),
        "lectures_with_matches": sum(
            1
            for evidence in lecture_evidence
            if evidence["matches"]
        ),
        "lectures_without_matches": len(
            unmapped_lectures
        ),
        "topics_observed": (
            observed_topic_count
        ),
        "topics_completed": len(
            completed_topics
        ),
    }

    # -------------------------------------------------
    # RETURN STATE
    # -------------------------------------------------

    return {
        "status": "ok",

        "course": {
            "id": course.id,
            "code": course.code,
            "name": course.name,
            "short_name": (
                course.short_name
            ),
        },

        "progress": {
            "actual": progress,
            "planned": planned_progress,
            "gap": progress_gap,
        },

        "topics": {
            "total": total_topics,
            "completed": len(
                completed_topics
            ),
            "remaining": len(
                remaining_topics
            ),
            "remaining_list": [
                {
                    "id": topic.id,
                    "name": topic.name,
                }
                for topic in remaining_topics
            ],
        },

        "teaching": {
            "lecture_count": len(
                lectures
            ),
            "observed_topic_count": (
                observed_topic_count
            ),
            "observed_pace": (
                observed_pace
            ),
            "introduction_pace": (
                introduction_pace
            ),
            "recent_pace": (
                recent_pace
            ),
        },

        "units": unit_states,

        "drift": {
            "signals": drift_signals,
            "repeated_topics": (
                repeated_topics[:10]
            ),
            "unmapped_lecture_count": (
                len(unmapped_lectures)
            ),
        },

        "evidence": {
            "lectures": lecture_evidence,
            "summary": evidence_summary,
        },
    }