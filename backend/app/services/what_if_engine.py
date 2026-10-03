from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from sqlalchemy.orm import Session

from app.services.prediction_engine import (
    predict_course_completion,
)


def detect_scenario(
    message: str,
) -> str | None:
    """
    Detect the schedule scenario requested by the user.

    Returns:
        "cancel"
        "add"
        None
    """

    text = message.lower().strip()

    cancel_terms = (
        "cancel",
        "miss",
        "skip",
        "postpone",
        "remove",
        "drop",
    )

    add_terms = (
        "add",
        "extra",
        "additional",
        "make up",
        "makeup",
        "one more",
    )

    if any(
        term in text
        for term in cancel_terms
    ):
        return "cancel"

    if any(
        term in text
        for term in add_terms
    ):
        return "add"

    return None


def _parse_date(
    value: str | None,
) -> datetime | None:
    if not value:
        return None

    text = str(value).strip()

    for fmt in (
        "%Y-%m-%d",
        "%d %B %Y",
        "%d %b %Y",
    ):
        try:
            return datetime.strptime(
                text,
                fmt,
            )
        except ValueError:
            continue

    return None


def simulate_schedule_change(
    db: Session,
    course_id: str,
    message: str,
) -> dict[str, Any]:
    """
    Simulate a single schedule change without changing
    the database.

    V1 assumptions:
        - one cancelled class removes one teaching opportunity
        - one extra class adds one teaching opportunity
        - typical lecture interval remains unchanged
        - teaching pace remains unchanged

    The result is therefore an explainable baseline simulation,
    not a full calendar optimizer.
    """

    scenario = detect_scenario(
        message
    )

    if scenario is None:
        return {
            "status": "needs_clarification",
            "course_id": course_id,
            "message": (
                "I couldn't determine whether you want "
                "to cancel/miss a class or add an extra class."
            ),
        }

    prediction = predict_course_completion(
        db=db,
        course_id=course_id,
    )

    if prediction.get("status") == "insufficient_data":
        return {
            "status": "insufficient_data",
            "course_id": course_id,
            "scenario": scenario,
            "prediction": None,
            "message": (
                "There isn't enough historical teaching "
                "data to simulate this change reliably."
            ),
        }

    if prediction.get("status") == "complete":
        return {
            "status": "complete",
            "course_id": course_id,
            "scenario": scenario,
            "prediction": prediction.get(
                "prediction"
            ),
            "message": (
                "This course already has no remaining "
                "syllabus topics."
            ),
        }

    base_prediction = prediction[
        "prediction"
    ]

    evidence = prediction[
        "evidence"
    ]

    base_date = _parse_date(
        base_prediction[
            "predicted_completion"
        ]
    )

    if base_date is None:
        return {
            "status": "error",
            "course_id": course_id,
            "message": (
                "The current prediction date "
                "could not be interpreted."
            ),
        }

    base_lectures = base_prediction[
        "estimated_lectures_remaining"
    ]

    interval_days = float(
        evidence[
            "typical_lecture_interval_days"
        ]
    )

    if interval_days <= 0:
        interval_days = 7.0

    # -------------------------------------------------
    # APPLY SCENARIO
    # -------------------------------------------------

    if scenario == "cancel":
        scenario_label = (
            "cancel one class"
        )

        simulated_lectures = (
            base_lectures + 1
        )

        impact_lectures = 1

    else:
        scenario_label = (
            "add one extra class"
        )

        simulated_lectures = max(
            1,
            base_lectures - 1,
        )

        impact_lectures = -1

    # -------------------------------------------------
    # SIMULATED COMPLETION
    # -------------------------------------------------

    simulated_days = round(
        simulated_lectures
        * interval_days,
        1,
    )

    simulated_date = (
        base_date
        + timedelta(
            days=(
                simulated_lectures
                - base_lectures
            )
            * interval_days
        )
    )

    change_days = round(
        (
            simulated_date
            - base_date
        ).total_seconds()
        / 86400,
        1,
    )

    # -------------------------------------------------
    # RETURN EXPLAINABLE RESULT
    # -------------------------------------------------

    return {
        "status": "ok",
        "course_id": course_id,
        "scenario": scenario,
        "scenario_label": scenario_label,

        "baseline": {
            "predicted_completion": (
                base_prediction[
                    "predicted_completion"
                ]
            ),
            "estimated_lectures_remaining": (
                base_lectures
            ),
        },

        "simulation": {
            "estimated_lectures_remaining": (
                simulated_lectures
            ),
            "predicted_completion": (
                simulated_date.strftime(
                    "%Y-%m-%d"
                )
            ),
            "change_days": change_days,
            "impact_lectures": (
                impact_lectures
            ),
        },

        "evidence": {
            "working_pace": evidence[
                "working_pace"
            ],
            "typical_lecture_interval_days": (
                interval_days
            ),
            "remaining_topics": evidence[
                "remaining_topics"
            ],
        },
    }