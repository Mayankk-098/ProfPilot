from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.models.academic import Course
from app.schemas.attendance import (
    AttendanceCourseResponse,
    AttendanceSessionResponse,
    AttendanceSessionSummary,
    AttendanceStudentDetailResponse,
    AttendanceSubmit,
    AttendanceSubmitResult,
)
from app.services import attendance_service
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/attendance", tags=["Attendance"])


def _get_course(db: Session, course_id: str, lecturer_id: str) -> Course:
    course = (
        db.query(Course)
        .filter(
            Course.id == course_id,
            Course.lecturer_id == lecturer_id,
        )
        .first()
    )
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")
    return course


@router.get("/{course_id}", response_model=AttendanceCourseResponse)
def get_course_attendance(
    course_id: str,
    flagged_only: bool = False,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    course = _get_course(db, course_id, current_user.lecturer_id)
    return attendance_service.build_course_attendance(
        db, course, flagged_only=flagged_only
    )


@router.get(
    "/{course_id}/history",
    response_model=list[AttendanceSessionSummary],
)
def get_attendance_history(
    course_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    course = _get_course(db, course_id, current_user.lecturer_id)
    return attendance_service.list_attendance_history(db, course)


@router.get(
    "/{course_id}/students/{student_id}",
    response_model=AttendanceStudentDetailResponse,
)
def get_student_attendance_detail(
    course_id: str,
    student_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    course = _get_course(db, course_id, current_user.lecturer_id)
    try:
        return attendance_service.get_student_attendance_detail(
            db,
            course,
            student_id,
        )
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.get(
    "/{course_id}/records/{class_date}",
    response_model=AttendanceSessionResponse,
)
def get_attendance_session(
    course_id: str,
    class_date: date,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    course = _get_course(db, course_id, current_user.lecturer_id)
    return attendance_service.get_attendance_session(
        db,
        course,
        class_date,
    )


@router.post("/{course_id}/records", response_model=AttendanceSubmitResult)
def submit_attendance(
    course_id: str,
    request: AttendanceSubmit,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create one complete attendance session. Existing sessions are rejected."""
    course = _get_course(db, course_id, current_user.lecturer_id)
    try:
        return attendance_service.record_attendance(
            db,
            course,
            request.class_date,
            [(m.student_id, m.status) for m in request.records],
        )
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.put(
    "/{course_id}/records/{class_date}",
    response_model=AttendanceSubmitResult,
)
def correct_attendance(
    course_id: str,
    class_date: date,
    request: AttendanceSubmit,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Replace a previously recorded complete session for correction purposes."""
    if request.class_date != class_date:
        raise HTTPException(
            status_code=422,
            detail="Path date and request class_date must match",
        )
    course = _get_course(db, course_id, current_user.lecturer_id)
    try:
        return attendance_service.correct_attendance(
            db,
            course,
            class_date,
            [(m.student_id, m.status) for m in request.records],
        )
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
