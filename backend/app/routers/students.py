from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.schemas.students import (
    StudentCreate,
    StudentImportConfirm,
    StudentImportContent,
    StudentImportPreviewResponse,
    StudentImportResult,
    StudentResponse,
    StudentUpdate,
)
from app.services import student_service
from app.services.auth_service import get_current_user


router = APIRouter(tags=["Students"])


def _response(student) -> StudentResponse:
    return StudentResponse(
        id=student.id,
        roll_no=student.roll_no,
        name=student.name,
        section=student.section,
        email=student.email,
        lecturer_id=student.lecturer_id,
    )


@router.get(
    "/students",
    response_model=list[StudentResponse],
)
def list_students(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return [
        _response(student)
        for student in student_service.list_students(
            db,
            current_user.lecturer_id,
        )
    ]


@router.get(
    "/courses/{course_id}/students",
    response_model=list[StudentResponse],
)
def list_course_students(
    course_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        students = student_service.list_course_students(
            db,
            current_user.lecturer_id,
            course_id,
        )
    except HTTPException:
        raise

    return [_response(student) for student in students]


@router.post(
    "/courses/{course_id}/students",
    response_model=StudentResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_course_student(
    course_id: str,
    data: StudentCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        student = student_service.add_student(
            db,
            current_user.lecturer_id,
            course_id,
            roll_no=data.roll_no,
            name=data.name,
            section=data.section or "",
            email=data.email,
        )
    except HTTPException:
        raise
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error),
        ) from error

    return _response(student)


@router.patch(
    "/students/{student_id}",
    response_model=StudentResponse,
)
def update_student(
    student_id: str,
    data: StudentUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    fields = data.model_dump(exclude_unset=True)

    try:
        student = student_service.update_student(
            db,
            current_user.lecturer_id,
            student_id,
            **fields,
        )
    except HTTPException:
        raise
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error

    return _response(student)


@router.delete(
    "/courses/{course_id}/students/{student_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_course_student(
    course_id: str,
    student_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        student_service.unenroll_student(
            db,
            current_user.lecturer_id,
            course_id,
            student_id,
        )
    except HTTPException:
        raise
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.post(
    "/courses/{course_id}/students/import/preview",
    response_model=StudentImportPreviewResponse,
)
def preview_student_import(
    course_id: str,
    data: StudentImportContent,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        return student_service.preview_import(
            db,
            current_user.lecturer_id,
            course_id,
            data.content,
        )
    except HTTPException:
        raise
    except (ValueError, UnicodeDecodeError) as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error),
        ) from error


@router.post(
    "/courses/{course_id}/students/import/confirm",
    response_model=StudentImportResult,
)
def confirm_student_import(
    course_id: str,
    data: StudentImportConfirm,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    seen: set[str] = set()
    rows = []

    for row in data.students:
        roll = row.roll_no.strip()
        if roll in seen:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Duplicate roll number in request: {roll}",
            )
        seen.add(roll)
        rows.append(
            {
                "roll_no": roll,
                "name": row.name.strip(),
                "section": (row.section or "").strip(),
                "email": (row.email or "").strip() or None,
            }
        )

    try:
        return student_service.confirm_import(
            db,
            current_user.lecturer_id,
            course_id,
            rows,
        )
    except HTTPException:
        raise
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error),
        ) from error
