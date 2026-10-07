from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.models.academic import Course
from app.schemas.academic import (
    CourseCreate,
    CourseDetailResponse,
    CourseSummary,
    CourseUpdate,
    LectureResponse,
    SyllabusTopicResponse,
    SyllabusUnitResponse,
)
from app.services import course_service
from app.services.academic_state import build_course_state
from app.services.auth_service import get_current_user


router = APIRouter(
    prefix="/courses",
    tags=["Courses"],
)


def build_course_summary(
    course: Course,
    actual_progress: float,
) -> CourseSummary:
    """Build an API summary from derived academic metrics."""
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
    state = build_course_state(
        db=db,
        course_id=course.id,
    )

    if state.get("status") != "ok":
        return 0.0

    return float(
        state.get("progress", {}).get("actual", 0.0)
    )


def build_course_detail(
    db: Session,
    course: Course,
) -> CourseDetailResponse:
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
                planned_date=(
                    topic.planned_date.isoformat()
                    if topic.planned_date
                    else None
                ),
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
            date=(
                lecture.lecture_date.isoformat()
                if lecture.lecture_date
                else ""
            ),
            duration=lecture.duration,
            description=lecture.description,
        )
        for lecture in course.lectures
    ]

    summary = build_course_summary(
        course=course,
        actual_progress=actual_progress,
    )

    return CourseDetailResponse(
        **summary.model_dump(),
        department=course.lecturer.department,
        start_date=(
            course.start_date.isoformat()
            if course.start_date
            else None
        ),
        planned_end_date=(
            course.planned_end_date.isoformat()
            if course.planned_end_date
            else None
        ),
        syllabus=syllabus,
        lectures=lectures,
    )


@router.get(
    "/",
    response_model=list[CourseSummary],
)
def get_courses(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Return only courses owned by the authenticated lecturer."""
    courses = (
        db.query(Course)
        .filter(
            Course.lecturer_id == current_user.lecturer_id,
        )
        .order_by(Course.code, Course.id)
        .all()
    )

    return [
        build_course_summary(
            course,
            get_actual_progress(db, course),
        )
        for course in courses
    ]


@router.post(
    "/",
    response_model=CourseDetailResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_course(
    data: CourseCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        course = course_service.create_course(
            db,
            current_user.lecturer_id,
            code=data.code,
            name=data.name,
            short_name=data.short_name,
            section=data.section,
            start_date=data.start_date,
            planned_end_date=data.planned_end_date,
        )
    except ValueError as error:
        message = str(error)
        code = (
            status.HTTP_409_CONFLICT
            if "already exists" in message
            else status.HTTP_422_UNPROCESSABLE_ENTITY
        )
        raise HTTPException(
            status_code=code,
            detail=message,
        ) from error

    return build_course_detail(db, course)


@router.get(
    "/{course_id}",
    response_model=CourseDetailResponse,
)
def get_course(
    course_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    course = (
        db.query(Course)
        .filter(
            Course.id == course_id,
            Course.lecturer_id == current_user.lecturer_id,
        )
        .first()
    )

    if course is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found",
        )

    return build_course_detail(db, course)


@router.patch(
    "/{course_id}",
    response_model=CourseDetailResponse,
)
def update_course(
    course_id: str,
    data: CourseUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    fields = data.model_dump(exclude_unset=True)

    try:
        course = course_service.update_course(
            db,
            current_user.lecturer_id,
            course_id,
            **fields,
        )
    except HTTPException:
        raise
    except ValueError as error:
        message = str(error)
        code = (
            status.HTTP_409_CONFLICT
            if "already exists" in message
            else status.HTTP_422_UNPROCESSABLE_ENTITY
        )
        raise HTTPException(
            status_code=code,
            detail=message,
        ) from error

    return build_course_detail(db, course)


@router.delete(
    "/{course_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_course(
    course_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    course_service.delete_course(
        db,
        current_user.lecturer_id,
        course_id,
    )
