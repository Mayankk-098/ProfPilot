from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.models.academic import Course
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


def build_course_summary(course: Course) -> CourseSummary:
    return CourseSummary(
        id=course.id,
        code=course.code,
        name=course.name,
        short_name=course.short_name,
        section=course.section,
        progress=course.progress,
        planned_progress=course.planned_progress,
        current_pace=course.current_pace,
        required_pace=course.required_pace,
        predicted_completion=course.predicted_completion,
        planned_completion=course.planned_completion,
        total_students=course.total_students,
        present_today=course.present_today,
        absent_today=course.absent_today,
    )


@router.get("/", response_model=list[CourseSummary])
def get_courses(
    db: Session = Depends(get_db),
):
    courses = db.query(Course).all()

    return [
        build_course_summary(course)
        for course in courses
    ]


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

    return CourseDetailResponse(
        **build_course_summary(course).model_dump(),
        department="Computer Science & Engineering",
        syllabus=syllabus,
        lectures=lectures,
    )