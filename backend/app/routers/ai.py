from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.schemas.academic import AIQuery
from app.services.ai_service import ProfPilotAI


router = APIRouter(
    prefix="/ai",
    tags=["ProfPilot AI"],
)


ai = ProfPilotAI()


@router.post("/query")
def query_ai(
    request: AIQuery,
    db: Session = Depends(get_db),
):
    return ai.query(
        message=request.message,
        db=db,
        course_id=request.course_id,
    )