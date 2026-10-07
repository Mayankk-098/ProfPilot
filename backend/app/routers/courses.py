from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.models.academic import Course, SyllabusTopic, SyllabusUnit
from app.schemas.academic import (
    CourseCreate,
    CourseDetailResponse,
    CourseSummary,
    CourseUpdate,
    LectureResponse,
    ReorderRequest,
    SyllabusTopicCreate,
    SyllabusTopicResponse,
    SyllabusTopicUpdate,
    SyllabusUnitCreate,
    SyllabusUnitResponse,
    SyllabusUnitUpdate,
)
from app.services import course_service, syllabus_service
from app.services.academic_state import build_course_state
from app.services.auth_service import get_current_user
from app.services.ownership import (
    require_owned_course,
    require_owned_topic,
    require_owned_unit,
)


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


def _topic_response(topic: SyllabusTopic) -> SyllabusTopicResponse:
    return SyllabusTopicResponse(
        id=topic.id,
        name=topic.name,
        completed=topic.completed,
        planned_date=(
            topic.planned_date.isoformat()
            if topic.planned_date
            else None
        ),
    )


def _unit_response(unit: SyllabusUnit) -> SyllabusUnitResponse:
    return SyllabusUnitResponse(
        id=unit.id,
        name=unit.name,
        progress=unit.progress,
        topics=[
            _topic_response(topic)
            for topic in unit.topics
        ],
    )


def build_course_detail(
    db: Session,
    course: Course,
) -> CourseDetailResponse:
    actual_progress = get_actual_progress(
        db=db,
        course=course,
    )

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
        syllabus=[
            _unit_response(unit)
            for unit in course.units
        ],
        lectures=[
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
        ],
    )


def _owned_unit_for_course(
    db: Session,
    course_id: str,
    unit_id: str,
    lecturer_id: str,
) -> SyllabusUnit:
    require_owned_course(db, course_id, lecturer_id)
    unit = require_owned_unit(db, unit_id, lecturer_id)
    if unit.course_id != course_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Syllabus unit not found",
        )
    return unit


def _owned_topic_for_course_unit(
    db: Session,
    course_id: str,
    unit_id: str,
    topic_id: str,
    lecturer_id: str,
) -> SyllabusTopic:
    unit = _owned_unit_for_course(
        db,
        course_id,
        unit_id,
        lecturer_id,
    )
    topic = require_owned_topic(
        db,
        topic_id,
        lecturer_id,
    )
    if topic.unit_id != unit.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Syllabus topic not found",
        )
    return topic


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


# ============================================================
# SYLLABUS
# ============================================================


@router.post(
    "/{course_id}/units",
    response_model=SyllabusUnitResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_unit(
    course_id: str,
    data: SyllabusUnitCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        unit = syllabus_service.add_unit(
            db,
            current_user.lecturer_id,
            course_id,
            data.name,
        )
    except HTTPException:
        raise
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error),
        ) from error

    return _unit_response(unit)


@router.patch(
    "/{course_id}/units/{unit_id}",
    response_model=SyllabusUnitResponse,
)
def update_unit(
    course_id: str,
    unit_id: str,
    data: SyllabusUnitUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    _owned_unit_for_course(
        db,
        course_id,
        unit_id,
        current_user.lecturer_id,
    )

    try:
        unit = syllabus_service.update_unit(
            db,
            current_user.lecturer_id,
            unit_id,
            data.name,
        )
    except HTTPException:
        raise
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error),
        ) from error

    return _unit_response(unit)


@router.delete(
    "/{course_id}/units/{unit_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_unit(
    course_id: str,
    unit_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    _owned_unit_for_course(
        db,
        course_id,
        unit_id,
        current_user.lecturer_id,
    )

    syllabus_service.delete_unit(
        db,
        current_user.lecturer_id,
        unit_id,
    )


@router.put(
    "/{course_id}/units/reorder",
    response_model=list[SyllabusUnitResponse],
)
def reorder_units(
    course_id: str,
    data: ReorderRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        units = syllabus_service.reorder_units(
            db,
            current_user.lecturer_id,
            course_id,
            data.ids,
        )
    except HTTPException:
        raise
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error),
        ) from error

    return [
        _unit_response(unit)
        for unit in units
    ]


@router.post(
    "/{course_id}/units/{unit_id}/topics",
    response_model=SyllabusTopicResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_topic(
    course_id: str,
    unit_id: str,
    data: SyllabusTopicCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    unit = _owned_unit_for_course(
        db,
        course_id,
        unit_id,
        current_user.lecturer_id,
    )

    try:
        topic = syllabus_service.add_topic(
            db,
            current_user.lecturer_id,
            unit.id,
            data.name,
            data.planned_date,
        )
    except HTTPException:
        raise
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error),
        ) from error

    return _topic_response(topic)


@router.patch(
    "/{course_id}/units/{unit_id}/topics/{topic_id}",
    response_model=SyllabusTopicResponse,
)
def update_topic(
    course_id: str,
    unit_id: str,
    topic_id: str,
    data: SyllabusTopicUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    _owned_topic_for_course_unit(
        db,
        course_id,
        unit_id,
        topic_id,
        current_user.lecturer_id,
    )

    try:
        topic = syllabus_service.update_topic(
            db,
            current_user.lecturer_id,
            topic_id,
            name=data.name,
            planned_date=data.planned_date,
            clear_planned_date=data.clear_planned_date,
        )
    except HTTPException:
        raise
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error),
        ) from error

    return _topic_response(topic)


@router.delete(
    "/{course_id}/units/{unit_id}/topics/{topic_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_topic(
    course_id: str,
    unit_id: str,
    topic_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    _owned_topic_for_course_unit(
        db,
        course_id,
        unit_id,
        topic_id,
        current_user.lecturer_id,
    )

    syllabus_service.delete_topic(
        db,
        current_user.lecturer_id,
        topic_id,
    )


@router.put(
    "/{course_id}/units/{unit_id}/topics/reorder",
    response_model=list[SyllabusTopicResponse],
)
def reorder_topics(
    course_id: str,
    unit_id: str,
    data: ReorderRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    unit = _owned_unit_for_course(
        db,
        course_id,
        unit_id,
        current_user.lecturer_id,
    )

    try:
        topics = syllabus_service.reorder_topics(
            db,
            current_user.lecturer_id,
            unit.id,
            data.ids,
        )
    except HTTPException:
        raise
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error),
        ) from error

    return [
        _topic_response(topic)
        for topic in topics
    ]
