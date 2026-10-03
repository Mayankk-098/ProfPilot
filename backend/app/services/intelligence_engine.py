from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.models.academic import Course
from app.services.academic_state import build_course_state
from app.services.prediction_engine import predict_course_completion
from app.services.syllabus_drift_engine import detect_syllabus_drift


def _course(db: Session, course_id: str) -> Course | None:
    return (
        db.query(Course)
        .filter(Course.id == course_id)
        .first()
    )


def _status_from_gap(gap: float) -> str:
    if gap > 5:
        return "behind"
    if gap < -5:
        return "ahead"
    return "on_track"


def _build_recommendation(
    state: dict[str, Any],
    prediction: dict[str, Any],
    drift: dict[str, Any],
) -> dict[str, Any]:
    remaining = state["topics"]["remaining_list"]
    teaching = state["teaching"]
    progress = state["progress"]

    if not remaining:
        return {
            "type": "complete",
            "priority": "low",
            "message": "All syllabus topics are currently marked complete.",
            "topics": [],
        }

    severity = drift.get("severity", "on_track")
    signals = drift.get("signals", [])

    if severity in {"high_drift", "moderate_drift", "mild_drift"}:
        reason = drift.get("recommendation") or "Prioritize remaining syllabus topics."
        priority = "high" if severity == "high_drift" else "medium"
    elif any(signal.get("type") == "repeated_coverage" for signal in signals):
        reason = "Recent lectures include repeated coverage; prioritize the remaining syllabus topics next."
        priority = "medium"
    else:
        reason = "Continue with the next uncovered syllabus topic while maintaining the observed teaching pace."
        priority = "medium"

    return {
        "type": "next_topic",
        "priority": priority,
        "message": reason,
        "topics": remaining[:3],
        "progress_gap": progress["gap"],
        "recent_pace": teaching["recent_pace"],
        "prediction_status": prediction.get("status"),
    }


def build_course_intelligence(
    db: Session,
    course_id: str,
) -> dict[str, Any]:
    """Compose existing academic engines into one read-only overview."""
    course = _course(db, course_id)
    if not course:
        return {"status": "not_found", "course_id": course_id}

    state = build_course_state(db=db, course_id=course_id)
    if state.get("status") != "ok":
        return state

    prediction = predict_course_completion(db=db, course_id=course_id)
    drift = detect_syllabus_drift(db=db, course_id=course_id)

    gap = float(state["progress"].get("gap", 0.0) or 0.0)
    predicted = prediction.get("prediction") or {}

    summary = {
        "course_id": course.id,
        "course": course.short_name,
        "status": _status_from_gap(gap),
        "actual_progress": state["progress"]["actual"],
        "planned_progress": state["progress"]["planned"],
        "progress_gap": gap,
        "remaining_topics": state["topics"]["remaining"],
        "remaining_topic_list": state["topics"]["remaining_list"],
        "lecture_count": state["teaching"]["lecture_count"],
        "recent_pace": state["teaching"]["recent_pace"],
        "required_pace": getattr(course, "required_pace", 0.0),
        "predicted_completion": predicted.get("predicted_completion"),
        "forecast_confidence": predicted.get("confidence"),
        "drift_severity": drift.get("severity"),
        "drift_score": drift.get("drift_score"),
    }

    return {
        "status": "ok",
        "course": {
            "id": course.id,
            "code": course.code,
            "name": course.name,
            "short_name": course.short_name,
        },
        "summary": summary,
        "recommendation": _build_recommendation(
            state=state,
            prediction=prediction,
            drift=drift,
        ),
        "evidence": {
            "academic_state": state,
            "prediction": prediction,
            "drift": drift,
        },
    }
