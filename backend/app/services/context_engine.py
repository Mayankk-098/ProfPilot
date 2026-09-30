from datetime import date
from sqlalchemy.orm import Session

from app.models.academic import (
    Lecturer,
    Course,
    ScheduleItem,
)


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


def course_to_dict(course):
    return {
        "id": course.id,
        "code": course.code,
        "name": course.name,
        "short_name": course.short_name,
        "section": course.section,
        "progress": course.progress,
        "planned_progress": course.planned_progress,
        "current_pace": course.current_pace,
        "required_pace": course.required_pace,
        "predicted_completion": course.predicted_completion,
        "planned_completion": course.planned_completion,
        "total_students": course.total_students,
        "present_today": course.present_today,
        "absent_today": course.absent_today,
    }

def schedule_to_dict(item: ScheduleItem) -> dict:
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
    # SELECTED COURSE
    # ----------------------------------------

    selected_course = None

    if course_id:
        selected_course = next(
            (
                c
                for c in courses
                if c.id == course_id
            ),
            None,
        )

    if selected_course is None and courses:
        selected_course = courses[0]


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
            key=lambda lecture: lecture.id,
            reverse=True,
        )[:5]


    # ----------------------------------------
    # ACADEMIC ALERTS
    # ----------------------------------------

    alerts = []

    for course in courses:

        progress_gap = (
            course.planned_progress
            - course.progress
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

    courses_behind = sum(
        1
        for course in courses
        if course.progress <
        course.planned_progress
    )

    courses_on_or_ahead = (
        len(courses) - courses_behind
    )


    summary = {
        "total_courses": len(courses),

        "courses_behind":
            courses_behind,

        "courses_on_or_ahead":
            courses_on_or_ahead,

        "selected_course_progress":
            selected_course.progress
            if selected_course
            else None,

        "selected_course_planned_progress":
            selected_course.planned_progress
            if selected_course
            else None,
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
            course_to_dict(selected_course)
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
            course_to_dict(course)
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