from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.models.academic import Course
from app.schemas.memory import MemoryCreate, MemoryResponse
from app.services.memory_service import create_memory, get_memories
from app.services.auth_service import get_current_user


router = APIRouter(
    prefix="/memory",
    tags=["Memory"],
)


@router.post("/events", response_model=MemoryResponse)
def add_memory(
    request: MemoryCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    # If a course is supplied, verify that it belongs to
    # the authenticated lecturer.
    if request.course_id is not None:
        course = db.scalar(
            select(Course).where(
                Course.id == request.course_id,
                Course.lecturer_id == current_user.lecturer_id,
            )
        )

        if course is None:
            raise HTTPException(
                status_code=403,
                detail="Not authorized to attach memory to this course",
            )

    # IMPORTANT:
    # Never trust lecturer_id from the request body.
    # The authenticated JWT is the source of truth.
    return create_memory(
        db=db,
        lecturer_id=current_user.lecturer_id,
        event_type=request.event_type,
        title=request.title,
        summary=request.summary,
        course_id=request.course_id,
        occurred_at=request.occurred_at,
    )


@router.get("/{lecturer_id}", response_model=list[MemoryResponse])
def read_memories(
    lecturer_id: str,
    course_id: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    # Prevent one lecturer from reading another lecturer's memories.
    if lecturer_id != current_user.lecturer_id:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to access these memories",
        )

    # If filtering by course, verify that the course belongs
    # to the authenticated lecturer.
    if course_id is not None:
        course = db.scalar(
            select(Course).where(
                Course.id == course_id,
                Course.lecturer_id == current_user.lecturer_id,
            )
        )

        if course is None:
            raise HTTPException(
                status_code=403,
                detail="Not authorized to access this course",
            )

    return get_memories(
        db=db,
        lecturer_id=lecturer_id,
        course_id=course_id,
        limit=limit,
    )
