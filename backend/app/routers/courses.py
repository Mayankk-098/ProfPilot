from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.models.academic import Course
from app.services.academic_state import build_course_state
from app.schemas.academic import (
    CourseSummary,
    CourseDetailResponse,
    SyllabusUnitResponse,
    SyllabusTopicResponse,
    LectureResponse,
)


router = APIRouter(
    prefix="/courses",
    tags=["Courses"],
)


def build_course_summary(
    course: Course,
    actual_progress: float,
) -> CourseSummary:
    """
    Build a course summary using derived academic progress
    instead of the cached Course.progress value.
    """
    return CourseSummary(
        id=course.id,
        code=course.code,
        name=course.name,
        short_name=course.short_name,
        section=course.section,
        progress=actual_progress,
        planned_progress=course.planned_progress,
        current_pace=course.current_pace,
        required_pace=course.required_pace,
        predicted_completion=course.predicted_completion,
        planned_completion=course.planned_completion,
        total_students=course.total_students,
        present_today=course.present_today,
        absent_today=course.absent_today,
    )


def get_actual_progress(
    db: Session,
    course: Course,
) -> float:
    """
    Get the authoritative derived progress from academic state.

    academic_state.py calculates progress directly from the
    number of completed syllabus topics, so this keeps API
    responses consistent with the intelligence layer.
    """
    state = build_course_state(
        db=db,
        course_id=course.id,
    )

    if state.get("status") != "ok":
        return 0.0

    return float(
        state.get("progress", {}).get(
            "actual",
            0.0,
        )
    )


@router.get(
    "/",
    response_model=list[CourseSummary],
)
def get_courses(
    db: Session = Depends(get_db),
):
    courses = db.query(Course).all()

    summaries = []

    for course in courses:
        actual_progress = get_actual_progress(
            db=db,
            course=course,
        )

        summaries.append(
            build_course_summary(
                course=course,
                actual_progress=actual_progress,
            )
        )

    return summaries


@router.get(
    "/{course_id}",
    response_model=CourseDetailResponse,
)
def get_course(
    course_id: str,
    db: Session = Depends(get_db),
):
    course = (
        db.query(Course)
        .filter(Course.id == course_id)
        .first()
    )

    if not course:
        raise HTTPException(
            status_code=404,
            detail="Course not found",
        )

    actual_progress = get_actual_progress(
        db=db,
        course=course,
    )

    syllabus = []

    for unit in course.units:
        topics = [
            SyllabusTopicResponse(
                id=topic.id,
                name=topic.name,
                completed=topic.completed,
                planned_date=topic.planned_date,
            )
            for topic in unit.topics
        ]

        syllabus.append(
            SyllabusUnitResponse(
                id=unit.id,
                name=unit.name,
                progress=unit.progress,
                topics=topics,
            )
        )

    lectures = [
        LectureResponse(
            id=lecture.id,
            date=lecture.date,
            duration=lecture.duration,
            description=lecture.description,
        )
        for lecture in course.lectures
    ]

    course_summary = build_course_summary(
        course=course,
        actual_progress=actual_progress,
    )

    return CourseDetailResponse(
        **course_summary.model_dump(),
        department="Computer Science & Engineering",
        syllabus=syllabus,
        lectures=lectures,
    )