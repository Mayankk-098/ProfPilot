from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.schemas.academic import AIQuery
from app.services.ai_service import ai
from ai.nlp.pipeline import analyze_query
from app.services.entity_resolver import resolve_entities


router = APIRouter(
    prefix="/ai",
    tags=["ProfPilot AI"],
)


@router.post("/query")
def query_ai(
    request: AIQuery,
    db: Session = Depends(get_db),
):
    # Run learned NLP first.
    nlp_analysis = analyze_query(
        request.message
    )

    # Resolve NLP entities against the academic database.
    resolved_entities = resolve_entities(
        db=db,
        nlp_analysis=nlp_analysis,
        fallback_course_id=request.course_id,
    )

    # Run the academic reasoning layer.
    response = ai.query(
        message=request.message,
        db=db,
        course_id=request.course_id,
        nlp_analysis=nlp_analysis,
    )

    # Expose NLP + resolved entities for debugging/evaluation.
    response["nlp"] = nlp_analysis
    response["resolved_entities"] = resolved_entities

    return response