from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.models.academic import Course
from app.services.academic_state import build_course_state


def _get_course(
    db: Session,
    course_id: str,
) -> Course | None:
    return (
        db.query(Course)
        .filter(Course.id == course_id)
        .first()
    )


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _build_signal(
    signal_type: str,
    severity: str,
    description: str,
    evidence: dict[str, Any],
) -> dict[str, Any]:
    return {
        "type": signal_type,
        "severity": severity,
        "description": description,
        "evidence": evidence,
    }


def detect_syllabus_drift(
    db: Session,
    course_id: str,
) -> dict[str, Any]:
    """
    Detect divergence between planned syllabus progress and
    the observed teaching trajectory.

    V1 is intentionally explainable and read-only.

    The engine combines:
        - planned vs actual progress
        - recent teaching pace vs required pace
        - unmapped lecture rate
        - completed topics without lecture evidence
        - repeated-topic coverage as an efficiency signal

    Repeated coverage is NOT automatically treated as syllabus drift.
    It is reported separately because revisiting a topic can be intentional.
    """

    course = _get_course(
        db=db,
        course_id=course_id,
    )

    if not course:
        return {
            "status": "not_found",
            "course_id": course_id,
        }

    state = build_course_state(
        db=db,
        course_id=course_id,
    )

    if state.get("status") != "ok":
        return state

    progress = state["progress"]
    topics = state["topics"]
    teaching = state["teaching"]
    drift = state["drift"]

    actual_progress = _safe_float(
        progress.get("actual")
    )
    planned_progress = _safe_float(
        progress.get("planned")
    )
    progress_gap = _safe_float(
        progress.get("gap")
    )

    lecture_count = int(
        teaching.get("lecture_count", 0)
        or 0
    )

    recent_pace = _safe_float(
        teaching.get("recent_pace")
    )

    required_pace = _safe_float(
        getattr(course, "required_pace", 0.0)
    )

    unmapped_count = int(
        drift.get("unmapped_lecture_count", 0)
        or 0
    )

    unmapped_ratio = (
        unmapped_count / lecture_count
        if lecture_count > 0
        else 0.0
    )

    completion_without_evidence = []
    for signal in drift.get("signals", []):
        if signal.get("type") == "completion_without_evidence":
            completion_without_evidence = (
                signal.get("topics", [])
                or []
            )
            break

    repeated_topics = (
        drift.get("repeated_topics", [])
        or []
    )

    remaining_topics = int(
        topics.get("remaining", 0)
        or 0
    )

    # --------------------------------
    # DRIFT SCORE
    # --------------------------------
    #
    # This is a transparent V1 heuristic, not a learned model.
    #
    # Maximum contribution:
    #   progress gap       -> 40
    #   unmapped lectures  -> 30
    #   evidence gap       -> 25
    #   pace deficit       -> 20
    #
    # The final score is capped at 100.
    # --------------------------------

    score_components: dict[str, float] = {}

    behind_points = max(progress_gap, 0.0)
    score_components["progress_gap"] = min(
        behind_points * 4.0,
        40.0,
    )

    score_components["unmapped_lectures"] = min(
        unmapped_ratio * 40.0,
        30.0,
    )

    score_components["completion_without_evidence"] = (
        25.0
        if completion_without_evidence
        else 0.0
    )

    pace_deficit = max(
        required_pace - recent_pace,
        0.0,
    )

    score_components["pace_deficit"] = min(
        pace_deficit * 25.0,
        20.0,
    )

    raw_score = sum(
        score_components.values()
    )

    drift_score = round(
        min(raw_score, 100.0),
        2,
    )

    if drift_score >= 60:
        severity = "high_drift"
    elif drift_score >= 35:
        severity = "moderate_drift"
    elif drift_score >= 15:
        severity = "mild_drift"
    else:
        severity = "on_track"

    # --------------------------------
    # EXPLAINABLE SIGNALS
    # --------------------------------

    signals: list[dict[str, Any]] = []

    if behind_points >= 3:
        signals.append(
            _build_signal(
                signal_type="progress_gap",
                severity=(
                    "moderate"
                    if behind_points >= 7
                    else "mild"
                ),
                description=(
                    f"Actual syllabus progress is "
                    f"{behind_points:.2f} percentage points "
                    "behind the planned progress."
                ),
                evidence={
                    "actual_progress": actual_progress,
                    "planned_progress": planned_progress,
                    "gap_points": round(
                        behind_points,
                        2,
                    ),
                },
            )
        )

    if pace_deficit > 0:
        pace_severity = (
            "moderate"
            if pace_deficit >= 0.30
            else "mild"
        )

        signals.append(
            _build_signal(
                signal_type="pace_deficit",
                severity=pace_severity,
                description=(
                    "Recent teaching pace is below "
                    "the required pace."
                ),
                evidence={
                    "recent_pace": recent_pace,
                    "required_pace": required_pace,
                    "pace_gap": round(
                        pace_deficit,
                        2,
                    ),
                },
            )
        )

    if unmapped_count:
        mapping_severity = (
            "high"
            if unmapped_ratio >= 0.40
            else "moderate"
            if unmapped_ratio >= 0.20
            else "mild"
        )

        signals.append(
            _build_signal(
                signal_type="unmapped_lectures",
                severity=mapping_severity,
                description=(
                    "Some recorded lectures could not be "
                    "confidently mapped to the current syllabus."
                ),
                evidence={
                    "unmapped_lecture_count": unmapped_count,
                    "lecture_count": lecture_count,
                    "unmapped_ratio": round(
                        unmapped_ratio,
                        3,
                    ),
                },
            )
        )

    if completion_without_evidence:
        signals.append(
            _build_signal(
                signal_type="completion_without_evidence",
                severity="high",
                description=(
                    "Some topics are marked completed but "
                    "have no supporting lecture-mapping evidence."
                ),
                evidence={
                    "topics": completion_without_evidence,
                },
            )
        )

    # --------------------------------
    # COVERAGE EFFICIENCY
    # --------------------------------
    #
    # Repeated coverage is intentionally kept separate
    # from the drift score.
    # --------------------------------

    repeated_coverage_signal = None

    if repeated_topics and remaining_topics > 0:
        repeated_names = [
            item.get("topic")
            for item in repeated_topics[:5]
            if item.get("topic")
        ]

        repeated_coverage_signal = {
            "type": "repeated_coverage",
            "severity": "info",
            "description": (
                "Some topics have appeared in multiple "
                "lecture mappings while syllabus topics "
                "still remain. This may indicate review, "
                "reinforcement, or inefficient coverage; "
                "it is not treated as drift by itself."
            ),
            "evidence": {
                "repeated_topics": repeated_names,
                "remaining_topics": remaining_topics,
            },
        }

    if repeated_coverage_signal:
        signals.append(
            repeated_coverage_signal
        )

    # --------------------------------
    # RECOMMENDATION
    # --------------------------------

    if severity == "high_drift":
        recommendation = (
            "Review the remaining syllabus against the "
            "recorded lecture history and prioritize "
            "uncovered topics. Some academic-state evidence "
            "also needs reconciliation."
        )
    elif severity == "moderate_drift":
        recommendation = (
            "Increase teaching pace and prioritize remaining "
            "syllabus topics. Review any unmapped lectures "
            "before making schedule decisions."
        )
    elif severity == "mild_drift":
        recommendation = (
            "The course shows a mild deviation from plan. "
            "Prioritize remaining topics and continue "
            "monitoring the recent teaching pace."
        )
    else:
        if repeated_coverage_signal:
            recommendation = (
                "The course is broadly on track. Some recent "
                "topic repetition is visible, so prioritize "
                "the remaining syllabus topics to maintain pace."
            )
        else:
            recommendation = (
                "The course is broadly aligned with the "
                "current teaching plan."
            )

    return {
        "status": "ok",
        "course_id": course_id,
        "severity": severity,
        "drift_score": drift_score,
        "summary": {
            "actual_progress": actual_progress,
            "planned_progress": planned_progress,
            "progress_gap": round(
                progress_gap,
                2,
            ),
            "remaining_topics": remaining_topics,
            "lecture_count": lecture_count,
            "recent_pace": recent_pace,
            "required_pace": required_pace,
            "unmapped_lecture_count": unmapped_count,
            "unmapped_lecture_ratio": round(
                unmapped_ratio,
                3,
            ),
        },
        "signals": signals,
        "score_components": score_components,
        "recommendation": recommendation,
        "evidence": {
            "state_progress": progress,
            "state_topics": topics,
            "state_teaching": teaching,
            "state_drift": drift,
        },
    }
