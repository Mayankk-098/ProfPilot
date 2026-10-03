from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.schemas.academic import (
    AIActionExecute,
    AIQuery,
)
from app.services.ai_service import ai
from app.services.action_executor import (
    execute_action,
)
from app.services.entity_resolver import (
    resolve_entities,
)
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
    # Run learned NLP first.
    nlp_analysis = analyze_query(
        request.message
    )

    # Resolve NLP entities against the
    # academic database.
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

    # Expose NLP + resolved entities
    # for debugging/evaluation.
    response["nlp"] = nlp_analysis
    response["resolved_entities"] = (
        resolved_entities
    )

    return response


@router.post("/execute")
def execute_ai_action(
    request: AIActionExecute,
    db: Session = Depends(get_db),
):
    """
    Execute an AI action only after explicit
    confirmation from the client.
    """

    if not request.confirmed:
        raise HTTPException(
            status_code=400,
            detail=(
                "Action execution requires "
                "explicit confirmation."
            ),
        )

    action_plan = request.action_plan

    if not action_plan:
        raise HTTPException(
            status_code=400,
            detail="Action plan is required.",
        )

    if (
        action_plan.get("status")
        != "proposed"
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "Only proposed actions "
                "can be executed."
            ),
        )

    if not action_plan.get(
        "requires_confirmation",
        False,
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "This action does not require "
                "confirmation."
            ),
        )

    result = execute_action(
        action_plan=action_plan,
        db=db,
    )

    if result["status"] == "error":
        raise HTTPException(
            status_code=400,
            detail=result["message"],
        )

    if result["status"] == "already_executed":
        return {
            "type": "action_already_executed",
            "answer": result["message"],
            "data": result,
            "confidence": 1.0,
            "requires_confirmation": False,
        }

    if result["status"] == "not_supported":
        raise HTTPException(
            status_code=501,
            detail=result["message"],
        )

    return {
        "type": "action_executed",
        "answer": (
            "The confirmed academic action "
            "has been executed successfully."
        ),
        "data": result,
        "confidence": 1.0,
        "requires_confirmation": False,
    }