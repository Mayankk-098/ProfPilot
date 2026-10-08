"""DB-backed attendance: per-student totals, <75% flagging, recording sessions."""

from __future__ import annotations

from collections import defaultdict
from datetime import date
from typing import Iterable, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.attendance import (
    ATTENDANCE_STATUSES,
    AttendanceRecord,
    Enrollment,
    Student,
)
from app.services import academic_rules as rules
from app.services import schedule_service
from app.services import clock


# Policy: an EXCUSED class is excluded from both attended and total, so it
# neither helps nor hurts.
EXCUSED_COUNTS_AS_PRESENT = False


def build_course_attendance(
    db: Session, course, flagged_only: bool = False
) -> dict:
    students = db.scalars(
        select(Student)
        .join(Enrollment, Enrollment.student_id == Student.id)
        .where(Enrollment.course_id == course.id)
        .order_by(Student.roll_no)
    ).all()

    rows = db.execute(
        select(
            AttendanceRecord.student_id,
            AttendanceRecord.status,
            func.count(),
        )
        .where(AttendanceRecord.course_id == course.id)
        .group_by(
            AttendanceRecord.student_id,
            AttendanceRecord.status,
        )
    ).all()

    counts: dict[str, dict[str, int]] = defaultdict(
        lambda: defaultdict(int)
    )

    for student_id, status, count in rows:
        counts[student_id][status] = count

    entries = []
    sum_attended = 0
    sum_total = 0

    for student in students:
        student_counts = counts[student.id]

        attended = student_counts["present"] + (
            student_counts["excused"]
            if EXCUSED_COUNTS_AS_PRESENT
            else 0
        )

        total = (
            student_counts["present"]
            + student_counts["absent"]
            + (
                student_counts["excused"]
                if EXCUSED_COUNTS_AS_PRESENT
                else 0
            )
        )

        summary = rules.summarize_attendance(attended, total)

        sum_attended += attended
        sum_total += total

        entries.append(
            {
                "student_id": student.id,
                "roll_no": student.roll_no,
                "name": student.name,
                "attended": summary.attended,
                "total": summary.total,
                "percentage": summary.percentage,
                "flagged": summary.flagged,
                "classes_needed_to_recover": (
                    summary.classes_needed_to_recover
                ),
            }
        )

    flagged_count = sum(
        1 for entry in entries if entry["flagged"]
    )

    # Flagged students first, then lowest percentage first,
    # students with no attendance last.
    entries.sort(
        key=lambda entry: (
            not entry["flagged"],
            (
                entry["percentage"]
                if entry["percentage"] is not None
                else 101
            ),
            entry["roll_no"],
        )
    )

    if flagged_only:
        entries = [
            entry for entry in entries
            if entry["flagged"]
        ]

    classes_held = db.scalar(
        select(
            func.count(
                func.distinct(AttendanceRecord.class_date)
            )
        ).where(
            AttendanceRecord.course_id == course.id
        )
    ) or 0

    last_date = db.scalar(
        select(func.max(AttendanceRecord.class_date)).where(
            AttendanceRecord.course_id == course.id
        )
    )

    present_last = 0
    absent_last = 0

    if last_date is not None:
        last_rows = db.execute(
            select(
                AttendanceRecord.status,
                func.count(),
            )
            .where(
                AttendanceRecord.course_id == course.id,
                AttendanceRecord.class_date == last_date,
            )
            .group_by(AttendanceRecord.status)
        ).all()

        last_counts = {
            status: count
            for status, count in last_rows
        }

        present_last = last_counts.get("present", 0)
        absent_last = last_counts.get("absent", 0)

    return {
        "course_id": course.id,
        "course_code": course.code,
        "short_name": course.short_name,
        "section": course.section,
        "threshold_pct": rules.ATTENDANCE_THRESHOLD_PCT,
        "classes_held": classes_held,
        "last_class_date": (
            last_date.isoformat()
            if last_date
            else None
        ),
        "total_students": len(students),
        "class_average_pct": (
            round(sum_attended / sum_total * 100, 2)
            if sum_total
            else None
        ),
        "present_last_class": present_last,
        "absent_last_class": absent_last,
        "flagged_count": flagged_count,
        "students": entries,
    }



def _validate_course_occurrence(db: Session, course, class_date: date) -> None:
    """Require the date to be an active scheduled occurrence for this course."""
    occurrences = schedule_service.day_schedule(
        db,
        class_date,
        lecturer_id=course.lecturer_id,
        include_cancelled=False,
    )
    if not any(
        item.get("course_id") == course.id
        and item.get("item_type") == "class"
        and item.get("status") != "cancelled"
        for item in occurrences
    ):
        raise ValueError(
            f"{class_date.isoformat()} is not an active scheduled class "
            f"date for {course.id}."
        )


def _validate_roster(
    db: Session,
    course,
    marks: list[tuple[str, str]],
) -> set[str]:
    enrolled_ids = set(
        db.scalars(
            select(Enrollment.student_id).where(
                Enrollment.course_id == course.id
            )
        ).all()
    )
    if not enrolled_ids:
        raise ValueError(f"No students are enrolled in {course.id}.")

    submitted_ids = [student_id for student_id, _ in marks]
    if len(set(submitted_ids)) != len(submitted_ids):
        raise ValueError("A student appears more than once in this submission.")

    for _, status in marks:
        if status not in ATTENDANCE_STATUSES:
            raise ValueError(f"Invalid status '{status}'.")

    unknown = sorted(set(submitted_ids) - enrolled_ids)
    if unknown:
        raise ValueError(
            f"Not enrolled in {course.id}: " + ", ".join(unknown)
        )

    missing = sorted(enrolled_ids - set(submitted_ids))
    if missing:
        raise ValueError(
            "Incomplete attendance submission. Missing enrolled students: "
            + ", ".join(missing)
        )

    return enrolled_ids


def list_attendance_history(
    db: Session,
    course,
) -> list[dict]:
    rows = db.execute(
        select(
            AttendanceRecord.class_date,
            AttendanceRecord.status,
            func.count(),
        )
        .where(AttendanceRecord.course_id == course.id)
        .group_by(
            AttendanceRecord.class_date,
            AttendanceRecord.status,
        )
        .order_by(AttendanceRecord.class_date.desc())
    ).all()

    grouped: dict[date, dict[str, int]] = {}
    for class_date, status, count in rows:
        grouped.setdefault(
            class_date,
            {"present": 0, "absent": 0, "excused": 0},
        )[status] = count

    return [
        {
            "class_date": class_date.isoformat(),
            "present": counts["present"],
            "absent": counts["absent"],
            "excused": counts["excused"],
            "total_records": sum(counts.values()),
        }
        for class_date, counts in grouped.items()
    ]


def get_student_attendance_detail(
    db: Session,
    course,
    student_id: str,
) -> dict:
    student = db.scalar(
        select(Student)
        .join(Enrollment, Enrollment.student_id == Student.id)
        .where(
            Student.id == student_id,
            Student.lecturer_id == course.lecturer_id,
            Enrollment.course_id == course.id,
        )
    )
    if student is None:
        raise ValueError("Student is not enrolled in this course.")

    rows = db.scalars(
        select(AttendanceRecord)
        .where(
            AttendanceRecord.course_id == course.id,
            AttendanceRecord.student_id == student.id,
        )
        .order_by(AttendanceRecord.class_date.desc())
    ).all()

    attended = sum(
        1
        for row in rows
        if row.status == "present"
        or (row.status == "excused" and EXCUSED_COUNTS_AS_PRESENT)
    )
    total = sum(
        1
        for row in rows
        if row.status in ("present", "absent")
        or (row.status == "excused" and EXCUSED_COUNTS_AS_PRESENT)
    )
    summary = rules.summarize_attendance(attended, total)

    return {
        "course_id": course.id,
        "course_code": course.code,
        "threshold_pct": rules.ATTENDANCE_THRESHOLD_PCT,
        "student_id": student.id,
        "roll_no": student.roll_no,
        "name": student.name,
        "section": student.section,
        "attended": summary.attended,
        "total": summary.total,
        "percentage": summary.percentage,
        "flagged": summary.flagged,
        "classes_needed_to_recover": summary.classes_needed_to_recover,
        "history": [
            {
                "class_date": row.class_date.isoformat(),
                "status": row.status,
            }
            for row in rows
        ],
    }



def get_attendance_session(
    db: Session,
    course,
    class_date: date,
) -> dict:
    records = db.scalars(
        select(AttendanceRecord)
        .where(
            AttendanceRecord.course_id == course.id,
            AttendanceRecord.class_date == class_date,
        )
        .order_by(AttendanceRecord.student_id)
    ).all()

    return {
        "course_id": course.id,
        "class_date": class_date.isoformat(),
        "recorded": bool(records),
        "records": [
            {
                "student_id": record.student_id,
                "status": record.status,
            }
            for record in records
        ],
    }



def record_attendance(
    db: Session,
    course,
    class_date: date,
    marks: Iterable[tuple[str, str]],
    today: Optional[date] = None,
) -> dict:
    """Record one complete attendance session; an existing session is rejected."""
    today = today or clock.today()
    if class_date > today:
        raise ValueError("Cannot record attendance for a future date.")

    marks = list(marks)
    _validate_course_occurrence(db, course, class_date)
    _validate_roster(db, course, marks)

    existing_count = db.scalar(
        select(func.count()).select_from(AttendanceRecord).where(
            AttendanceRecord.course_id == course.id,
            AttendanceRecord.class_date == class_date,
        )
    ) or 0
    if existing_count:
        raise ValueError(
            f"Attendance for {course.id} on {class_date.isoformat()} has already been recorded. "
            "Use the correction endpoint to replace it."
        )

    for student_id, status in marks:
        db.add(AttendanceRecord(
            student_id=student_id,
            course_id=course.id,
            class_date=class_date,
            status=status,
        ))
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    return {
        "course_id": course.id,
        "class_date": class_date.isoformat(),
        "created": len(marks),
        "updated": 0,
    }


def correct_attendance(
    db: Session,
    course,
    class_date: date,
    marks: Iterable[tuple[str, str]],
    today: Optional[date] = None,
) -> dict:
    """Replace the complete roster for an already-recorded class session."""
    today = today or clock.today()
    if class_date > today:
        raise ValueError("Cannot correct attendance for a future date.")

    marks = list(marks)
    _validate_course_occurrence(db, course, class_date)
    _validate_roster(db, course, marks)

    existing = db.scalar(
        select(func.count()).select_from(AttendanceRecord).where(
            AttendanceRecord.course_id == course.id,
            AttendanceRecord.class_date == class_date,
        )
    ) or 0
    if not existing:
        raise ValueError(
            f"No attendance session exists for {course.id} on {class_date.isoformat()}. "
            "Use the create endpoint first."
        )

    db.query(AttendanceRecord).filter(
        AttendanceRecord.course_id == course.id,
        AttendanceRecord.class_date == class_date,
    ).delete(synchronize_session=False)

    for student_id, status in marks:
        db.add(AttendanceRecord(
            student_id=student_id,
            course_id=course.id,
            class_date=class_date,
            status=status,
        ))
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    return {
        "course_id": course.id,
        "class_date": class_date.isoformat(),
        "created": 0,
        "updated": len(marks),
    }

