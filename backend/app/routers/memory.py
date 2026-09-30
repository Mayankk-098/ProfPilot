from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.schemas.memory import MemoryCreate, MemoryResponse
from app.services.memory_service import create_memory, get_memories


router = APIRouter(
    prefix="/memory",
    tags=["Memory"],
)


@router.post("/events", response_model=MemoryResponse)
def add_memory(
    request: MemoryCreate,
    db: Session = Depends(get_db),
):
    return create_memory(
        db=db,
        lecturer_id=request.lecturer_id,
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
):
    return get_memories(
        db=db,
        lecturer_id=lecturer_id,
        course_id=course_id,
        limit=limit,
    )