from __future__ import annotations

from datetime import date, datetime
from typing import Any

from sqlalchemy.orm import Session

from app.models.academic import Course
from app.services import attendance_service, clock
from app.services.prediction_engine import predict_course_completion


def _parse_iso(value: str | None) -> date | None:
    if not value:
        return None

    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def _risk_level(score: float) -> str:
    if score >= 60:
        return "high"
    if score >= 25:
        return "medium"
    if score > 0:
        return "low"
    return "on_track"


def _add_driver(
    drivers: list[dict[str, Any]],
    *,
    kind: str,
    severity: str,
    message: str,
    evidence: dict[str, Any],
) -> None:
    drivers.append(
        {
            "type": kind,
            "severity": severity,
            "message": message,
            "evidence": evidence,
        }
    )


def _student_recovery(
    student: dict[str, Any],
) -> dict[str, Any]:
    attended = int(student["attended"])
    total = int(student["total"])
    percentage = student["percentage"]
    needed = int(student["classes_needed_to_recover"])

    if percentage is None:
        action = "Record attendance history before planning recovery."
        projected_percentage = None
    elif needed == 0:
        action = "Student is already at or above the attendance threshold."
        projected_percentage = percentage
    else:
        projected_percentage = round(
            (attended + needed) / (total + needed) * 100,
            2,
        )
        action = (
            f"Target the next {needed} consecutive class"
            f"{'' if needed == 1 else 'es'} as present."
        )

    return {
        "student_id": student["student_id"],
        "roll_no": student["roll_no"],
        "name": student["name"],
        "current_attendance": percentage,
        "attended": attended,
        "total": total,
        "classes_needed_to_recover": needed,
        "projected_attendance_after_recovery": projected_percentage,
        "action": action,
    }


def _course_risk(
    db: Session,
    course: Course,
    today: date,
) -> dict[str, Any]:
    attendance = attendance_service.build_course_attendance(
        db,
        course,
    )

    flagged_students = [
        student
        for student in attendance["students"]
        if student["flagged"]
    ]

    state_progress = {
        "actual": float(course.progress),
        "planned": float(course.planned_progress),
        "gap": round(
            float(course.planned_progress) - float(course.progress),
            2,
        ),
    }

    score = 0.0
    drivers: list[dict[str, Any]] = []

    total_students = int(attendance["total_students"])
    flagged_count = int(attendance["flagged_count"])

    if total_students:
        attendance_ratio = flagged_count / total_students
        attendance_points = min(40.0, attendance_ratio * 40.0)

        if flagged_count:
            score += attendance_points
            severity = "high" if attendance_ratio >= 0.30 else "medium"
            _add_driver(
                drivers,
                kind="attendance",
                severity=severity,
                message=(
                    f"{flagged_count} of {total_students} student"
                    f"{'' if flagged_count == 1 else 's'} "
                    "is below the 75% attendance threshold."
                ),
                evidence={
                    "flagged_students": flagged_count,
                    "total_students": total_students,
                    "class_average_pct": attendance["class_average_pct"],
                    "threshold_pct": attendance["threshold_pct"],
                },
            )
    else:
        score += 5.0
        _add_driver(
            drivers,
            kind="attendance_data",
            severity="low",
            message="No students are enrolled yet, so attendance risk cannot be fully assessed.",
            evidence={"total_students": 0},
        )

    gap = state_progress["gap"]
    if gap > 0:
        progress_points = min(25.0, gap * 1.5)
        score += progress_points
        severity = "high" if gap >= 10 else "medium"
        _add_driver(
            drivers,
            kind="syllabus_pace",
            severity=severity,
            message=(
                f"{course.short_name} is {gap:.0f}% behind planned syllabus progress."
            ),
            evidence={
                "actual_progress": state_progress["actual"],
                "planned_progress": state_progress["planned"],
                "progress_gap": gap,
            },
        )

    prediction = predict_course_completion(
        db=db,
        course_id=course.id,
    )

    forecast_date = None
    forecast_status = prediction.get("status")
    if forecast_status == "ok":
        forecast_date = _parse_iso(
            prediction.get("prediction", {}).get("predicted_completion")
        )

    if forecast_date is not None and course.planned_end_date is not None:
        late_days = (forecast_date - course.planned_end_date).days
        if late_days > 0:
            forecast_points = min(25.0, max(5.0, late_days / 14.0 * 25.0))
            score += forecast_points
            severity = "high" if late_days >= 14 else "medium"
            _add_driver(
                drivers,
                kind="completion_forecast",
                severity=severity,
                message=(
                    f"Current teaching pace forecasts completion "
                    f"{late_days} day{'' if late_days == 1 else 's'} after the planned end date."
                ),
                evidence={
                    "predicted_completion": forecast_date.isoformat(),
                    "planned_end_date": course.planned_end_date.isoformat(),
                    "late_days": late_days,
                    "confidence": prediction["prediction"].get("confidence"),
                },
            )
    elif forecast_status == "insufficient_data":
        score += 5.0
        _add_driver(
            drivers,
            kind="forecast_data",
            severity="low",
            message="There is not enough lecture history for a reliable completion forecast.",
            evidence={
                "lecture_count": prediction.get("evidence", {}).get("lecture_count", 0),
                "remaining_topics": prediction.get("evidence", {}).get("remaining_topics"),
            },
        )

    score = round(min(100.0, score), 1)
    level = _risk_level(score)

    # Keep the most actionable drivers first.
    severity_rank = {"high": 0, "medium": 1, "low": 2}
    drivers.sort(key=lambda item: severity_rank.get(item["severity"], 3))

    recovery = [
        _student_recovery(student)
        for student in sorted(
            flagged_students,
            key=lambda item: (
                item["percentage"] is None,
                item["percentage"] if item["percentage"] is not None else 101,
                item["roll_no"],
            ),
        )
    ]

    if not drivers:
        headline = "Course is on track."
    elif level == "high":
        headline = "Immediate academic attention is recommended."
    elif level == "medium":
        headline = "A few academic signals need attention."
    else:
        headline = "Minor academic signals are being watched."

    return {
        "course_id": course.id,
        "course_code": course.code,
        "course_name": course.name,
        "short_name": course.short_name,
        "section": course.section,
        "risk_score": score,
        "risk_level": level,
        "headline": headline,
        "drivers": drivers,
        "attendance": {
            "classes_held": attendance["classes_held"],
            "class_average_pct": attendance["class_average_pct"],
            "flagged_count": flagged_count,
            "total_students": total_students,
        },
        "academic_progress": state_progress,
        "forecast": {
            "status": forecast_status,
            "predicted_completion": (
                forecast_date.isoformat()
                if forecast_date is not None
                else None
            ),
            "planned_end_date": (
                course.planned_end_date.isoformat()
                if course.planned_end_date
                else None
            ),
            "confidence": (
                prediction.get("prediction", {}).get("confidence")
                if prediction.get("prediction")
                else None
            ),
        },
        "recovery_plan": recovery,
        "generated_for": today.isoformat(),
    }


def build_risk_radar(
    db: Session,
    lecturer_id: str,
) -> dict[str, Any]:
    today = clock.today()

    courses = (
        db.query(Course)
        .filter(Course.lecturer_id == lecturer_id)
        .order_by(Course.code, Course.id)
        .all()
    )

    course_risks = [
        _course_risk(db, course, today)
        for course in courses
    ]

    course_risks.sort(
        key=lambda item: (
            -item["risk_score"],
            item["course_code"],
        )
    )

    high = sum(1 for item in course_risks if item["risk_level"] == "high")
    medium = sum(1 for item in course_risks if item["risk_level"] == "medium")
    flagged_students = sum(
        item["attendance"]["flagged_count"]
        for item in course_risks
    )

    return {
        "generated_for": today.isoformat(),
        "summary": {
            "total_courses": len(course_risks),
            "high_risk_courses": high,
            "medium_risk_courses": medium,
            "flagged_students": flagged_students,
        },
        "courses": course_risks,
    }
