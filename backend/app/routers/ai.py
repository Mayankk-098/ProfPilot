from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.schemas.academic import AIQuery
from app.services.ai_service import ai
from ai.nlp.pipeline import analyze_query


router = APIRouter(
    prefix="/ai",
    tags=["ProfPilot AI"],
)


@router.post("/query")
def query_ai(
    request: AIQuery,
    db: Session = Depends(get_db),
):
    # Run the learned NLP layer first.
    nlp_analysis = analyze_query(
        request.message
    )

    # Give the NLP result to the academic reasoning layer.
    response = ai.query(
        message=request.message,
        db=db,
        course_id=request.course_id,
        nlp_analysis=nlp_analysis,
    )

    # Keep exposing the NLP result for debugging/evaluation.
    response["nlp"] = nlp_analysis

    return response