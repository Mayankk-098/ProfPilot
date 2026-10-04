from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.schemas.context import AcademicContextResponse
from app.services.context_engine import build_academic_context
from app.services.auth_service import get_current_user


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
    current_user=Depends(get_current_user),
):
    # The URL lecturer_id must match the authenticated lecturer.
    # This preserves the existing endpoint contract while preventing
    # one lecturer from requesting another lecturer's academic context.
    if lecturer_id != current_user.lecturer_id:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to access this lecturer's context",
        )

    try:
        context = build_academic_context(
            db=db,
            lecturer_id=current_user.lecturer_id,
            course_id=course_id,
        )

        return context

    except ValueError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error
