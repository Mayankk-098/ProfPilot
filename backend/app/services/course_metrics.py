"""All DERIVED course values. Nothing here is stored; it is recomputed from
topics, lecture logs, the weekly schedule (+ cancellations) and attendance."""
from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session, object_session

from app.models.academic import ScheduleItem
from app.models.attendance import AttendanceRecord, Enrollment
from app.services import academic_rules as rules
from app.services import schedule_service
from app.services import clock

FUTURE_HORIZON_DAYS = 730


def get_course_metrics(course, now: Optional[datetime] = None) -> dict:
    """Cached per Course instance (a Course instance lives for one request/session)."""
    if now is None:
        cached = course.__dict__.get("_metrics_cache")
        if cached is not None:
            return cached
    db = object_session(course)
    if db is None:
        raise RuntimeError("Course must be attached to a session to compute metrics")
    metrics = compute_course_metrics(db, course, now or clock.now())
    if now is None:
        course.__dict__["_metrics_cache"] = metrics
    return metrics


def compute_course_metrics(db: Session, course, now: datetime) -> dict:
    today = now.date()

    # ---- syllabus: completion is derived from topics ----------------------
    topics = [t for unit in course.units for t in unit.topics]
    total_topics = len(topics)
    done_topics = sum(1 for t in topics if t.completed)
    remaining_topics = total_topics - done_topics

    progress = rules.percent(done_topics, total_topics)
    planned = rules.planned_progress([t.planned_date for t in topics], today)

    # ---- pace: derived from lecture history and the real future schedule --
    lectures_held = len(course.lectures)
    cur_pace = rules.current_pace(done_topics, lectures_held)

    items = db.scalars(
        select(ScheduleItem).where(
            ScheduleItem.course_id == course.id,
            ScheduleItem.item_type == "class",
        )
    ).all()
    slots = [schedule_service.item_to_slot(i) for i in items]
    changes = schedule_service.load_changes(db, [i.id for i in items])
    future = [
        o.start.date()
        for o in rules.occurrences(slots, changes, today, FUTURE_HORIZON_DAYS)
        if o.start > now
    ]
    before_end = [d for d in future if d <= course.planned_end_date]
    req_pace = rules.required_pace(remaining_topics, len(before_end))

    planned_completion = rules.fmt_date(course.planned_end_date)
    if remaining_topics <= 0:
        last = max((l.lecture_date for l in course.lectures), default=today)
        predicted_completion = rules.fmt_date(last)
    else:
        predicted = rules.predict_completion(remaining_topics, cur_pace, future)
        # No pace data yet (or not enough future classes): fall back to the plan.
        predicted_completion = (
            rules.fmt_date(predicted) if predicted else planned_completion
        )

    # ---- attendance snapshot ---------------------------------------------
    total_students = db.scalar(
        select(func.count()).select_from(Enrollment).where(
            Enrollment.course_id == course.id
        )
    ) or 0

    last_date = db.scalar(
        select(func.max(AttendanceRecord.class_date)).where(
            AttendanceRecord.course_id == course.id,
            AttendanceRecord.class_date <= today,
        )
    )
    present = absent = 0
    if last_date is not None:
        rows = db.execute(
            select(AttendanceRecord.status, func.count())
            .where(
                AttendanceRecord.course_id == course.id,
                AttendanceRecord.class_date == last_date,
            )
            .group_by(AttendanceRecord.status)
        ).all()
        counts = {status: n for status, n in rows}
        present = counts.get("present", 0)
        absent = counts.get("absent", 0)

    return {
        "progress": progress,
        "planned_progress": planned,
        "current_pace": cur_pace,
        "required_pace": req_pace,
        "predicted_completion": predicted_completion,
        "planned_completion": planned_completion,
        "total_students": total_students,
        "present_today": present,
        "absent_today": absent,
        "last_attendance_date": last_date.isoformat() if last_date else None,
    }
