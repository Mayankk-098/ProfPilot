from __future__ import annotations

import re
from datetime import date as Date, datetime
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
from app.models.memory import AcademicEvent
from app.services import clock, schedule_service
from app.services.notification_service import send_class_notification


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
) -> Date:
    """Normalize common proposal date values to a real date object."""
    if isinstance(date_value, Date):
        return date_value

    if date_value is None:
        return datetime.now().date()

    value = str(date_value).strip()

    if not value:
        return datetime.now().date()

    for fmt in ("%Y-%m-%d", "%d %B %Y", "%d %b %Y"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue

    raise ValueError(
        f"Invalid lecture date: {date_value!r}"
    )


def _find_duplicate_lecture(
    db,
    course_id: str,
    lecture_date: Date,
    description: str,
) -> LectureLog | None:
    """
    Detect an exact duplicate lecture submission.

    This protects against:
    - double-clicking confirm
    - mobile retry
    - repeated API requests
    """

    normalized_description = _normalize_text(description)

    lectures = (
        db.query(LectureLog)
        .filter(
            LectureLog.course_id == course_id,
            LectureLog.lecture_date == lecture_date,
        )
        .all()
    )

    for lecture in lectures:
        if (
            _normalize_text(lecture.description)
            == normalized_description
        ):
            return lecture

    return None


def _recalculate_course_progress(
    db: Session,
    course: Course,
) -> dict:
    """
    Read the current derived academic state.

    Progress, pace and completion are now calculated by
    Course/course_metrics rather than written into DB columns.
    """

    # Clear any per-instance metric cache created earlier in the request.
    course.__dict__.pop("_metrics_cache", None)

    # Ensure relationships are reloaded after the new lecture/topic links.
    db.expire(course, ["lectures", "units"])

    metrics = course._metrics()

    total_topics = 0
    completed_topics = 0
    unit_results = []

    for unit in course.units:
        topics = list(unit.topics)
        unit_total = len(topics)
        unit_completed = sum(
            1
            for topic in topics
            if topic.completed
        )

        total_topics += unit_total
        completed_topics += unit_completed

        unit_results.append(
            {
                "unit_id": unit.id,
                "unit_name": unit.name,
                "progress": unit.progress,
                "completed_topics": unit_completed,
                "total_topics": unit_total,
            }
        )

    lecture_count = (
        db.query(LectureLog)
        .filter(
            LectureLog.course_id == course.id
        )
        .count()
    )

    return {
        "course_progress": metrics["progress"],
        "completed_topics": completed_topics,
        "total_topics": total_topics,
        "lecture_count": lecture_count,
        "current_pace": metrics["current_pace"],
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

    lecture_date = _normalize_date(
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
            Course.id == course_id,
            Course.lecturer_id == lecturer_id,
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
        lecture_date=lecture_date,
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
        lecture_date=lecture_date,
        duration=duration,
        description=topic,
        course_id=course_id,
    )

    db.add(lecture)

    # -------------------------------------------------
    # Flush so the lecture becomes valid FK evidence.
    # -------------------------------------------------

    db.flush()

    # -------------------------------------------------
    # MARK SYLLABUS TOPICS
    # -------------------------------------------------
    #
    # Completion is now derived from covered_in_lecture_id.
    # -------------------------------------------------

    completed_topic_names = []

    for syllabus_topic in verified_topics:
        if not syllabus_topic.completed:
            syllabus_topic.covered_in_lecture_id = lecture.id

            completed_topic_names.append(
                syllabus_topic.name
            )

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

    # -------------------------------------------------
    # AUTOMATIC ACADEMIC MEMORY
    # -------------------------------------------------
    #
    # Successful lecture actions become persistent academic
    # events so later AI queries can retrieve them through the
    # existing memory_relevance layer.
    #
    # Keep this in the same transaction as the lecture and
    # syllabus mutation.
    # -------------------------------------------------

    completed_names = ", ".join(
        completed_topic_names
    ) or "no new syllabus topics"

    memory_event = AcademicEvent(
        lecturer_id=lecturer_id,
        course_id=course_id,
        event_type="lecture_logged",
        title=f"Lecture recorded: {topic}",
        summary=(
            f"Recorded a {course.short_name} lecture on "
            f"{lecture_date.isoformat()} covering {topic}. "
            f"Newly completed topics: {completed_names}."
        ),
    )

    db.add(memory_event)

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


def _parse_time(value):
    from datetime import time as Time

    if value is None:
        return None
    if isinstance(value, Time):
        return value

    text = str(value).strip().upper()
    for fmt in ("%H:%M", "%I:%M %p", "%I %p"):
        try:
            return datetime.strptime(text, fmt).time()
        except ValueError:
            continue

    raise ValueError(f"Invalid class time: {value!r}")


def _course_for_action(
    db: Session,
    course_id: str | None,
    lecturer_id: str,
) -> Course | None:
    if not course_id:
        return None

    return (
        db.query(Course)
        .filter(
            Course.id == course_id,
            Course.lecturer_id == lecturer_id,
        )
        .first()
    )


def _notification_for_class_change(
    db: Session,
    *,
    course: Course,
    lecturer_id: str,
    notification_type: str,
    original_date: Date,
    original_start,
    new_date=None,
    new_start=None,
    new_room=None,
    reason=None,
) -> dict:
    try:
        return send_class_notification(
            db,
            course=course,
            lecturer_id=lecturer_id,
            notification_type=notification_type,
            original_date=original_date.isoformat(),
            original_time=original_start.strftime("%H:%M"),
            new_date=new_date.isoformat() if new_date else None,
            new_time=new_start.strftime("%H:%M") if new_start else None,
            new_room=new_room,
            reason=reason,
        )
    except Exception as exc:
        return {
            "status": "notification_error",
            "sent": False,
            "recipient_count": 0,
            "message": f"Notification failed: {exc}",
        }


def execute_cancel_class_action(
    action_plan: dict,
    db: Session,
    lecturer_id: str,
) -> dict:
    proposal = action_plan.get("proposal") or {}
    course_id = proposal.get("course_id")
    item_id = proposal.get("item_id")
    class_date = proposal.get("date")

    course = _course_for_action(db, course_id, lecturer_id)
    if course is None:
        return {
            "status": "error",
            "message": "Course not found or not owned by this lecturer.",
        }

    if not item_id or not class_date:
        return {
            "status": "error",
            "message": "Cancellation proposal is incomplete.",
        }

    original_date = _normalize_date(class_date)

    from app.models.academic import ScheduleItem
    schedule_item = (
        db.query(ScheduleItem)
        .filter(
            ScheduleItem.id == item_id,
            ScheduleItem.lecturer_id == lecturer_id,
            ScheduleItem.course_id == course_id,
            ScheduleItem.item_type == "class",
        )
        .first()
    )

    if schedule_item is None:
        return {
            "status": "error",
            "message": "The scheduled class could not be verified.",
        }

    if original_date.weekday() != schedule_item.weekday:
        return {
            "status": "error",
            "message": "The proposed class date no longer matches the recurring schedule.",
        }

    existing = schedule_service._change_for_date(
        db,
        schedule_item.id,
        original_date,
    )
    if existing is not None:
        return {
            "status": "already_executed",
            "message": "A schedule change already exists for this class date.",
            "change": {
                "item_id": existing.item_id,
                "on_date": existing.on_date.isoformat(),
                "status": existing.status,
            },
        }

    try:
        change = schedule_service.cancel_class(
            db,
            schedule_item.id,
            original_date,
            proposal.get("reason"),
            lecturer_id=lecturer_id,
            today=clock.today(),
        )
    except (LookupError, ValueError) as exc:
        return {"status": "error", "message": str(exc)}

    notification = {"status": "skipped", "sent": False}
    if proposal.get("notify_students", True):
        notification = _notification_for_class_change(
            db,
            course=course,
            lecturer_id=lecturer_id,
            notification_type="cancelled",
            original_date=original_date,
            original_start=schedule_item.start_time,
            reason=proposal.get("reason"),
        )

    db.add(
        AcademicEvent(
            lecturer_id=lecturer_id,
            course_id=course_id,
            event_type="class_cancelled",
            title=f"Class cancelled: {course.short_name}",
            summary=(
                f"Cancelled {course.short_name} on "
                f"{original_date.isoformat()} at "
                f"{schedule_item.start_time.strftime('%H:%M')}."
            ),
        )
    )
    db.commit()

    return {
        "status": "executed",
        "change": {
            "item_id": change.item_id,
            "on_date": change.on_date.isoformat(),
            "status": change.status,
            "reason": change.reason,
        },
        "notification": notification,
    }


def execute_reschedule_class_action(
    action_plan: dict,
    db: Session,
    lecturer_id: str,
) -> dict:
    proposal = action_plan.get("proposal") or {}
    course_id = proposal.get("course_id")
    item_id = proposal.get("item_id")
    class_date = proposal.get("date")
    new_date_value = proposal.get("new_date")
    new_time_value = proposal.get("new_time")

    course = _course_for_action(db, course_id, lecturer_id)
    if course is None:
        return {
            "status": "error",
            "message": "Course not found or not owned by this lecturer.",
        }

    if not item_id or not class_date or not new_date_value:
        return {
            "status": "error",
            "message": "Rescheduling proposal is incomplete.",
        }

    original_date = _normalize_date(class_date)
    new_date = _normalize_date(new_date_value)
    new_start = _parse_time(new_time_value)

    from app.models.academic import ScheduleItem
    schedule_item = (
        db.query(ScheduleItem)
        .filter(
            ScheduleItem.id == item_id,
            ScheduleItem.lecturer_id == lecturer_id,
            ScheduleItem.course_id == course_id,
            ScheduleItem.item_type == "class",
        )
        .first()
    )

    if schedule_item is None:
        return {
            "status": "error",
            "message": "The scheduled class could not be verified.",
        }

    if original_date.weekday() != schedule_item.weekday:
        return {
            "status": "error",
            "message": "The proposed class date no longer matches the recurring schedule.",
        }

    existing = schedule_service._change_for_date(
        db,
        schedule_item.id,
        original_date,
    )
    if existing is not None:
        return {
            "status": "already_executed",
            "message": "A schedule change already exists for this class date.",
            "change": {
                "item_id": existing.item_id,
                "on_date": existing.on_date.isoformat(),
                "status": existing.status,
            },
        }

    try:
        change = schedule_service.reschedule_class(
            db,
            schedule_item.id,
            original_date,
            new_date,
            new_start,
            reason=proposal.get("reason"),
            lecturer_id=lecturer_id,
            today=clock.today(),
        )
    except (LookupError, ValueError) as exc:
        return {"status": "error", "message": str(exc)}

    new_actual_start = change.new_start_time or new_start
    new_actual_end = change.new_end_time or schedule_item.end_time

    notification = {"status": "skipped", "sent": False}
    if proposal.get("notify_students", True):
        notification = _notification_for_class_change(
            db,
            course=course,
            lecturer_id=lecturer_id,
            notification_type="rescheduled",
            original_date=original_date,
            original_start=schedule_item.start_time,
            new_date=change.new_date,
            new_start=new_actual_start,
            new_room=change.new_room,
            reason=proposal.get("reason"),
        )

    db.add(
        AcademicEvent(
            lecturer_id=lecturer_id,
            course_id=course_id,
            event_type="class_rescheduled",
            title=f"Class rescheduled: {course.short_name}",
            summary=(
                f"Moved {course.short_name} from "
                f"{original_date.isoformat()} to "
                f"{change.new_date.isoformat()} at "
                f"{new_actual_start.strftime('%H:%M')}."
            ),
        )
    )
    db.commit()

    return {
        "status": "executed",
        "change": {
            "item_id": change.item_id,
            "on_date": change.on_date.isoformat(),
            "status": change.status,
            "new_date": change.new_date.isoformat(),
            "new_start_time": new_actual_start.strftime("%H:%M"),
            "new_end_time": new_actual_end.strftime("%H:%M"),
            "new_room": change.new_room,
            "reason": change.reason,
        },
        "notification": notification,
    }


def execute_action(
    action_plan: dict,
    db: Session,
    lecturer_id: str = "lecturer_001",
) -> dict:
    """
    Execute a confirmed action.

    Supported:
        log_lecture
        cancel_class
        reschedule_class
    """

    action = action_plan.get(
        "action"
    )

    if action == "cancel_class":
        return execute_cancel_class_action(
            action_plan=action_plan,
            db=db,
            lecturer_id=lecturer_id,
        )

    if action == "reschedule_class":
        return execute_reschedule_class_action(
            action_plan=action_plan,
            db=db,
            lecturer_id=lecturer_id,
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