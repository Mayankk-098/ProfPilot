from __future__ import annotations

import math
from datetime import datetime, timedelta
from statistics import median
from typing import Any

from sqlalchemy.orm import Session

from app.services.academic_state import (
    build_course_state,
)


def _parse_date(
    value: str | None,
) -> datetime | None:
    if not value:
        return None

    text = str(value).strip()

    formats = (
        "%Y-%m-%d",
        "%d %B %Y",
        "%d %b %Y",
    )

    for fmt in formats:
        try:
            return datetime.strptime(
                text,
                fmt,
            )
        except ValueError:
            continue

    return None


def _typical_lecture_interval(
    lecture_dates: list[str],
) -> float:
    """
    Estimate the typical number of days between lectures.

    Median is used instead of mean so one unusually large
    gap does not dominate the estimate.
    """

    parsed_dates = []

    for value in lecture_dates:
        parsed = _parse_date(value)

        if parsed:
            parsed_dates.append(parsed)

    parsed_dates.sort()

    if len(parsed_dates) < 2:
        return 7.0

    intervals = []

    for current, previous in zip(
        parsed_dates[1:],
        parsed_dates[:-1],
    ):
        days = (
            current - previous
        ).total_seconds() / 86400

        if days > 0:
            intervals.append(days)

    if not intervals:
        return 7.0

    return round(
        float(median(intervals)),
        2,
    )


def predict_course_completion(
    db: Session,
    course_id: str,
) -> dict[str, Any]:
    """
    Read-only V1 completion forecast.

    This is an explainable baseline, not a trained ML model.

    Forecast uses:
        - remaining syllabus topics
        - overall topic-introduction pace
        - recent topic-introduction pace
        - typical lecture interval
        - latest recorded lecture date
    """

    state = build_course_state(
        db=db,
        course_id=course_id,
    )

    if state.get("status") != "ok":
        return state

    remaining_topics = state[
        "topics"
    ]["remaining"]

    lecture_count = state[
        "teaching"
    ]["lecture_count"]

    overall_pace = state[
        "teaching"
    ]["introduction_pace"]

    recent_pace = state[
        "teaching"
    ]["recent_pace"]

    lecture_evidence = state[
        "evidence"
    ]["lectures"]

    # ---------------------------------------------
    # NO REMAINING TOPICS
    # ---------------------------------------------

    if remaining_topics == 0:
        latest_date = None

        if lecture_evidence:
            latest_date = _parse_date(
                lecture_evidence[-1]["date"]
            )

        return {
            "status": "complete",
            "course_id": course_id,
            "prediction": {
                "predicted_completion": (
                    latest_date.strftime(
                        "%Y-%m-%d"
                    )
                    if latest_date
                    else None
                ),
                "estimated_lectures_remaining": 0,
                "estimated_days_remaining": 0.0,
            },
            "evidence": {
                "remaining_topics": 0,
                "lecture_count": lecture_count,
            },
        }

    # ---------------------------------------------
    # SELECT WORKING PACE
    # ---------------------------------------------

    if recent_pace > 0:
        # Weight recent behaviour more strongly.
        working_pace = round(
            (
                0.4 * overall_pace
                + 0.6 * recent_pace
            ),
            2,
        )
        pace_method = (
            "60% recent pace + 40% overall pace"
        )
    else:
        working_pace = overall_pace
        pace_method = "overall pace"

    # If there is insufficient history,
    # prediction cannot be meaningful.
    if working_pace <= 0:
        return {
            "status": "insufficient_data",
            "course_id": course_id,
            "prediction": None,
            "evidence": {
                "remaining_topics": (
                    remaining_topics
                ),
                "lecture_count": lecture_count,
                "working_pace": working_pace,
            },
        }

    # ---------------------------------------------
    # ESTIMATE REQUIRED LECTURES
    # ---------------------------------------------

    estimated_lectures = math.ceil(
        remaining_topics
        / working_pace
    )

    # ---------------------------------------------
    # ESTIMATE LECTURE INTERVAL
    # ---------------------------------------------

    lecture_dates = [
        evidence["date"]
        for evidence in lecture_evidence
        if evidence.get("date")
    ]

    interval_days = (
        _typical_lecture_interval(
            lecture_dates
        )
    )

    estimated_days = round(
        estimated_lectures
        * interval_days,
        1,
    )

    # ---------------------------------------------
    # LATEST LECTURE
    # ---------------------------------------------

    latest_date = None

    for evidence in reversed(
        lecture_evidence
    ):
        parsed = _parse_date(
            evidence.get("date")
        )

        if parsed:
            latest_date = parsed
            break

    if latest_date is None:
        return {
            "status": "insufficient_data",
            "course_id": course_id,
            "prediction": None,
            "evidence": {
                "reason": (
                    "No parseable lecture dates."
                ),
            },
        }

    today = datetime.now().replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )

    forecast_start = max(
        latest_date,
        today,
    )

    predicted_date = (
        forecast_start
        + timedelta(
            days=estimated_days
        )
    )

    # ---------------------------------------------
    # SIMPLE UNCERTAINTY BAND
    # ---------------------------------------------

    # We intentionally provide a range rather than
    # pretending that a seven-lecture history gives
    # high forecasting certainty.
    lower_date = (
        forecast_start
        + timedelta(
            days=max(
                1,
                estimated_days * 0.75,
            )
        )
    )

    upper_date = (
        forecast_start
        + timedelta(
            days=estimated_days * 1.25
        )
    )

    # ---------------------------------------------
    # CONFIDENCE BAND
    # ---------------------------------------------

    if lecture_count >= 12:
        confidence = "medium"
    elif lecture_count >= 6:
        confidence = "low-medium"
    else:
        confidence = "low"

    return {
        "status": "ok",

        "course_id": course_id,

        "prediction": {
            "predicted_completion": (
                predicted_date.strftime(
                    "%Y-%m-%d"
                )
            ),
            "lower_bound": (
                lower_date.strftime(
                    "%Y-%m-%d"
                )
            ),
            "upper_bound": (
                upper_date.strftime(
                    "%Y-%m-%d"
                )
            ),
            "estimated_lectures_remaining": (
                estimated_lectures
            ),
            "estimated_days_remaining": (
                estimated_days
            ),
            "confidence": confidence,
        },

        "evidence": {
            "remaining_topics": (
                remaining_topics
            ),
            "lecture_count": lecture_count,
            "overall_pace": overall_pace,
            "recent_pace": recent_pace,
            "working_pace": working_pace,
            "pace_method": pace_method,
            "typical_lecture_interval_days": (
                interval_days
            ),
            "latest_lecture_date": (
                latest_date.strftime(
                    "%Y-%m-%d"
                )
            ),
            "forecast_start_date": (
                forecast_start.strftime("%Y-%m-%d")
            ),
        },
    }