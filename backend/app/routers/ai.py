from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.models.academic import Course
from app.schemas.academic import (
    AIActionExecute,
    AIQuery,
)
from app.services.ai_service import ai
from app.services.action_executor import execute_action
from app.services.action_security import (
    create_action_token,
    verify_action_token,
)
from app.services.entity_resolver import resolve_entities
from app.services.auth_service import get_current_user
from ai.nlp.pipeline import analyze_query


router = APIRouter(
    prefix="/ai",
    tags=["ProfPilot AI"],
)


@router.post("/query")
def query_ai(
    request: AIQuery,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Run the complete ProfPilot intelligence pipeline inside the
    authenticated lecturer's academic scope.
    """

    lecturer_id = current_user.lecturer_id

    # ---------------------------------------------------------
    # AUTHORIZE OPTIONAL COURSE SCOPE
    # ---------------------------------------------------------
    #
    # A caller may provide a course_id to focus the AI request,
    # but that course must belong to the authenticated lecturer.
    # ---------------------------------------------------------

    if request.course_id is not None:
        course = db.scalar(
            select(Course).where(
                Course.id == request.course_id,
                Course.lecturer_id == lecturer_id,
            )
        )

        if course is None:
            raise HTTPException(
                status_code=404,
                detail="Course not found",
            )

    # ---------------------------------------------------------
    # LEARNED NLP
    # ---------------------------------------------------------

    nlp_analysis = analyze_query(
        request.message
    )

    # ---------------------------------------------------------
    # ENTITY RESOLUTION
    # ---------------------------------------------------------

    resolved_entities = resolve_entities(
        db=db,
        nlp_analysis=nlp_analysis,
        fallback_course_id=request.course_id,
    )

    # ---------------------------------------------------------
    # ACADEMIC INTELLIGENCE
    # ---------------------------------------------------------
    #
    # IMPORTANT:
    # lecturer_id comes from the authenticated JWT.
    # The client does not control lecturer scope.
    # ---------------------------------------------------------

    response = ai.query(
        message=request.message,
        db=db,
        course_id=request.course_id,
        lecturer_id=lecturer_id,
        nlp_analysis=nlp_analysis,
    )
    if isinstance(response.get("data"), dict):
        response["data"].setdefault("lecturer_id", lecturer_id)

    # Expose NLP + resolved entities for debugging/evaluation.
    response["nlp"] = nlp_analysis
    response["resolved_entities"] = resolved_entities

    # ---------------------------------------------------------
    # SIGN SERVER-GENERATED ACTION PROPOSALS
    # ---------------------------------------------------------

    data = response.get("data")

    if isinstance(data, dict):
        action_plan = data.get("action_plan")

        if (
            isinstance(action_plan, dict)
            and action_plan.get("status") == "proposed"
        ):
            # Bind the proposal to the authenticated lecturer.
            action_plan["lecturer_id"] = lecturer_id

            action_plan["proposal_token"] = create_action_token(
                action_plan
            )

    return response


@router.post("/execute")
def execute_ai_action(
    request: AIActionExecute,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Execute a previously generated action proposal only after
    explicit confirmation, valid server signature, and lecturer
    ownership validation.
    """

    lecturer_id = current_user.lecturer_id

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

    if action_plan.get("status") != "proposed":
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

    # ---------------------------------------------------------
    # LECTURER OWNERSHIP
    # ---------------------------------------------------------
    #
    # The proposal must belong to the authenticated lecturer.
    # This prevents a signed proposal from lecturer A being
    # replayed by lecturer B.
    # ---------------------------------------------------------

    proposal_lecturer_id = action_plan.get(
        "lecturer_id"
    )

    if proposal_lecturer_id != lecturer_id:
        raise HTTPException(
            status_code=403,
            detail="Action is not owned by this lecturer.",
        )

    # ---------------------------------------------------------
    # VERIFY SERVER-SIGNED PROPOSAL
    # ---------------------------------------------------------

    token_valid, token_message = verify_action_token(
        action_plan
    )

    if not token_valid:
        raise HTTPException(
            status_code=403,
            detail=token_message,
        )

    # ---------------------------------------------------------
    # EXECUTE
    # ---------------------------------------------------------

    result = execute_action(
        action_plan=action_plan,
        db=db,
        lecturer_id=lecturer_id,
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
