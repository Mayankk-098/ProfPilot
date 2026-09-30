from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.schemas.context import AcademicContextResponse
from app.services.context_engine import (
    build_academic_context,
)


router = APIRouter(
    prefix="/context",
    tags=["Academic Context"],
)


@router.get(
    "/{lecturer_id}",
    response_model=AcademicContextResponse,
)
def get_academic_context(
    lecturer_id: str,
    course_id: str | None = None,
    db: Session = Depends(get_db),
):

    try:
        context = build_academic_context(
            db=db,
            lecturer_id=lecturer_id,
            course_id=course_id,
        )

        return context

    except ValueError as error:

        raise HTTPException(
            status_code=404,
            detail=str(error),
        )