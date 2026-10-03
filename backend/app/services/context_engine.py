from datetime import date, datetime

from sqlalchemy.orm import Session

from app.models.academic import (
    Lecturer,
    Course,
    ScheduleItem,
)
from app.services.academic_state import build_course_state


def time_to_minutes(item: ScheduleItem) -> int:
    hour, minute = map(
        int,
        item.time.split(":"),
    )

    if item.period == "PM" and hour != 12:
        hour += 12

    if item.period == "AM" and hour == 12:
        hour = 0

    return hour * 60 + minute


def lecture_date_value(value: str | None) -> datetime:
    """
    Parse supported lecture date formats so recent lectures
    are sorted chronologically rather than by database ID.

    Supported:
        2026-10-02
        18 September 2026
        18 Sep 2026

    Unknown/missing dates are placed at the end.
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


def course_to_dict(
    course: Course,
    actual_progress: float | None = None,
) -> dict:
    """
    Convert a Course model into the context representation.

    When actual_progress is supplied, it is used instead of
    the cached Course.progress value.
    """

    progress = (
        actual_progress
        if actual_progress is not None
        else course.progress
    )

    return {
        "id": course.id,
        "code": course.code,
        "name": course.name,
        "short_name": course.short_name,
        "section": course.section,
        "progress": progress,
        "planned_progress": course.planned_progress,
        "current_pace": course.current_pace,
        "required_pace": course.required_pace,
        "predicted_completion": course.predicted_completion,
        "planned_completion": course.planned_completion,
        "total_students": course.total_students,
        "present_today": course.present_today,
        "absent_today": course.absent_today,
    }


def schedule_to_dict(
    item: ScheduleItem,
) -> dict:
    return {
        "id": item.id,
        "subject": item.subject,
        "code": item.code,
        "batch": item.batch,
        "time": item.time,
        "period": item.period,
        "room": item.room,
        "item_type": item.item_type,
        "course_id": item.course_id,
    }


def build_academic_context(
    db: Session,
    lecturer_id: str = "lecturer_001",
    course_id: str | None = None,
) -> dict:

    # ----------------------------------------
    # LECTURER
    # ----------------------------------------

    lecturer = (
        db.query(Lecturer)
        .filter(
            Lecturer.id == lecturer_id
        )
        .first()
    )

    if not lecturer:
        raise ValueError(
            "Lecturer not found"
        )

    # ----------------------------------------
    # COURSES
    # ----------------------------------------

    courses = (
        db.query(Course)
        .filter(
            Course.lecturer_id == lecturer_id
        )
        .all()
    )

    # ----------------------------------------
    # DERIVED ACADEMIC STATE
    # ----------------------------------------
    #
    # Academic state is the source of truth for
    # actual progress.
    #
    # Build it once per course so we don't repeatedly
    # run the intelligence/state calculation later.
    # ----------------------------------------

    course_states = {}

    for course in courses:
        state = build_course_state(
            db=db,
            course_id=course.id,
        )

        course_states[course.id] = state

    # ----------------------------------------
    # SELECTED COURSE
    # ----------------------------------------

    selected_course = None

    if course_id:
        selected_course = next(
            (
                course
                for course in courses
                if course.id == course_id
            ),
            None,
        )
    else:
        # Only choose the first course when the caller
        # did not specify a course at all.
        if courses:
            selected_course = courses[0]

    selected_state = (
        course_states.get(
            selected_course.id
        )
        if selected_course
        else None
    )

    selected_actual_progress = (
        float(
            selected_state
            .get("progress", {})
            .get("actual", 0.0)
        )
        if selected_state
        and selected_state.get("status") == "ok"
        else None
    )

    # ----------------------------------------
    # SCHEDULE
    # ----------------------------------------

    schedule = (
        db.query(ScheduleItem)
        .all()
    )

    schedule.sort(
        key=time_to_minutes
    )

    class_items = [
        item
        for item in schedule
        if item.item_type == "class"
    ]

    # ----------------------------------------
    # DEMO NEXT CLASS
    # ----------------------------------------
    #
    # For the current prototype, the earliest
    # class in the demo schedule is treated as
    # the next class.
    #
    # Later this becomes date/time aware.
    # ----------------------------------------

    next_class = (
        class_items[0]
        if class_items
        else None
    )

    # ----------------------------------------
    # RECENT LECTURES
    # ----------------------------------------

    recent_lectures = []

    if selected_course:
        recent_lectures = sorted(
            selected_course.lectures,
            key=lambda lecture: (
                lecture_date_value(
                    lecture.date
                ),
                lecture.id or "",
            ),
            reverse=True,
        )[:5]

    # ----------------------------------------
    # ACADEMIC ALERTS
    # ----------------------------------------

    alerts = []

    for course in courses:

        state = course_states.get(
            course.id
        )

        if not state or state.get("status") != "ok":
            continue

        actual_progress = float(
            state
            .get("progress", {})
            .get("actual", 0.0)
        )

        planned_progress = float(
            state
            .get("progress", {})
            .get("planned", 0.0)
        )

        progress_gap = (
            planned_progress
            - actual_progress
        )

        if progress_gap > 0:
            alerts.append(
                f"{course.short_name} is "
                f"{progress_gap:.0f}% behind "
                f"planned progress."
            )

        elif progress_gap < 0:
            alerts.append(
                f"{course.short_name} is "
                f"{abs(progress_gap):.0f}% ahead "
                f"of planned progress."
            )

    # ----------------------------------------
    # SUMMARY
    # ----------------------------------------

    courses_behind = 0

    for course in courses:
        state = course_states.get(
            course.id
        )

        if not state or state.get("status") != "ok":
            continue

        actual_progress = float(
            state
            .get("progress", {})
            .get("actual", 0.0)
        )

        planned_progress = float(
            state
            .get("progress", {})
            .get("planned", 0.0)
        )

        if actual_progress < planned_progress:
            courses_behind += 1

    courses_on_or_ahead = (
        len(courses)
        - courses_behind
    )

    summary = {
        "total_courses": len(courses),

        "courses_behind": (
            courses_behind
        ),

        "courses_on_or_ahead": (
            courses_on_or_ahead
        ),

        "selected_course_progress": (
            selected_actual_progress
            if selected_course
            else None
        ),

        "selected_course_planned_progress": (
            float(
                selected_course.planned_progress
            )
            if selected_course
            else None
        ),
    }

    # ----------------------------------------
    # FINAL CONTEXT
    # ----------------------------------------

    return {
        "current_date":
            date.today().isoformat(),

        "lecturer": {
            "id": lecturer.id,
            "name": lecturer.name,
            "title": lecturer.title,
            "department": lecturer.department,
        },

        "selected_course":
            course_to_dict(
                selected_course,
                actual_progress=(
                    selected_actual_progress
                ),
            )
            if selected_course
            else None,

        "next_class":
            schedule_to_dict(next_class)
            if next_class
            else None,

        "today_schedule": [
            schedule_to_dict(item)
            for item in schedule
        ],

        "courses": [
            course_to_dict(
                course,
                actual_progress=(
                    float(
                        course_states[
                            course.id
                        ]
                        .get("progress", {})
                        .get("actual", 0.0)
                    )
                    if course_states.get(
                        course.id
                    )
                    and course_states[
                        course.id
                    ].get("status") == "ok"
                    else None
                ),
            )
            for course in courses
        ],

        "recent_lectures": [
            {
                "id": lecture.id,
                "date": lecture.date,
                "duration": lecture.duration,
                "description": lecture.description,
            }
            for lecture in recent_lectures
        ],

        "alerts": alerts,

        "summary": summary,
    }