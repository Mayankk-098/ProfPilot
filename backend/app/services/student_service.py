from __future__ import annotations

import csv
import io
import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.attendance import AttendanceRecord, Enrollment, Student
from app.services.ids import new_id
from app.services.ownership import require_owned_course, require_owned_student



def _normalize_email(value: str | None) -> str | None:
    if value is None:
        return None
    email = value.strip().lower()
    if not email:
        return None
    if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email):
        raise ValueError("Invalid student email address")
    return email


def list_students(
    db: Session,
    lecturer_id: str,
) -> list[Student]:
    return list(
        db.scalars(
            select(Student)
            .where(Student.lecturer_id == lecturer_id)
            .order_by(Student.roll_no, Student.id)
        ).all()
    )


def list_course_students(
    db: Session,
    lecturer_id: str,
    course_id: str,
) -> list[Student]:
    course = require_owned_course(db, course_id, lecturer_id)
    return list(
        db.scalars(
            select(Student)
            .join(Enrollment, Enrollment.student_id == Student.id)
            .where(
                Enrollment.course_id == course.id,
                Student.lecturer_id == lecturer_id,
            )
            .order_by(Student.roll_no)
        ).all()
    )


def _find_by_roll(
    db: Session,
    lecturer_id: str,
    roll_no: str,
) -> Student | None:
    return db.scalar(
        select(Student).where(
            Student.lecturer_id == lecturer_id,
            Student.roll_no == roll_no.strip(),
        )
    )


def add_student(
    db: Session,
    lecturer_id: str,
    course_id: str,
    *,
    roll_no: str,
    name: str,
    section: str,
    email: str | None = None,
) -> Student:
    course = require_owned_course(db, course_id, lecturer_id)
    roll = roll_no.strip()
    normalized_email = _normalize_email(email)
    if not roll or not name.strip():
        raise ValueError("roll_no and name are required")

    student = _find_by_roll(db, lecturer_id, roll)
    if student is None:
        student = Student(
            id=new_id("stu"),
            roll_no=roll,
            name=name.strip(),
            section=section.strip() or course.section,
            email=normalized_email,
            lecturer_id=lecturer_id,
        )
        db.add(student)
        db.flush()
    else:
        student.name = name.strip()
        if section.strip():
            student.section = section.strip()
        if email is not None:
            student.email = normalized_email

    existing = db.get(Enrollment, (student.id, course.id))
    if existing is None:
        db.add(Enrollment(student_id=student.id, course_id=course.id))

    db.commit()
    db.refresh(student)
    return student


def update_student(
    db: Session,
    lecturer_id: str,
    student_id: str,
    *,
    name: str | None = None,
    section: str | None = None,
    roll_no: str | None = None,
    email: str | None = None,
) -> Student:
    student = require_owned_student(db, student_id, lecturer_id)
    if roll_no is not None:
        roll = roll_no.strip()
        clash = _find_by_roll(db, lecturer_id, roll)
        if clash is not None and clash.id != student.id:
            raise ValueError("A student with this roll number already exists")
        student.roll_no = roll
    if name is not None:
        student.name = name.strip()
    if section is not None:
        student.section = section.strip()
    if email is not None:
        student.email = _normalize_email(email)
    db.commit()
    db.refresh(student)
    return student


def unenroll_student(
    db: Session,
    lecturer_id: str,
    course_id: str,
    student_id: str,
) -> None:
    course = require_owned_course(db, course_id, lecturer_id)
    student = require_owned_student(db, student_id, lecturer_id)
    enrollment = db.get(Enrollment, (student.id, course.id))
    if enrollment is None:
        raise LookupError("Student is not enrolled in this course")

    db.delete(enrollment)
    db.query(AttendanceRecord).filter(
        AttendanceRecord.student_id == student.id,
        AttendanceRecord.course_id == course.id,
    ).delete(synchronize_session=False)
    db.flush()

    remaining = db.scalar(
        select(Enrollment.student_id).where(Enrollment.student_id == student.id)
    )
    if remaining is None:
        db.delete(student)
    db.commit()


def parse_csv(content: str | bytes) -> list[dict]:
    if isinstance(content, bytes):
        text = content.decode("utf-8-sig")
    else:
        text = content
    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        raise ValueError("CSV file is empty")

    headers = {name.strip().lower(): name for name in reader.fieldnames if name}
    required = {"roll_no", "name"}
    missing = required - set(headers)
    if missing:
        raise ValueError("CSV must include roll_no and name columns")

    rows = []
    for index, raw in enumerate(reader, start=2):
        roll = (raw.get(headers["roll_no"]) or "").strip()
        name = (raw.get(headers["name"]) or "").strip()
        section = ""
        if "section" in headers:
            section = (raw.get(headers["section"]) or "").strip()
        email = ""
        if "email" in headers:
            email = (raw.get(headers["email"]) or "").strip()
        rows.append(
            {
                "line": index,
                "roll_no": roll,
                "name": name,
                "section": section,
                "email": email,
            }
        )
    return rows


def preview_import(
    db: Session,
    lecturer_id: str,
    course_id: str,
    content: str | bytes,
) -> dict:
    course = require_owned_course(db, course_id, lecturer_id)
    parsed = parse_csv(content)
    seen: dict[str, int] = {}
    results = []
    valid = 0
    errors = 0

    for row in parsed:
        status = "ok"
        message = "Will create and enroll"
        roll = row["roll_no"]
        name = row["name"]

        if not roll or not name:
            status = "invalid"
            message = "roll_no and name are required"
        elif roll in seen:
            status = "duplicate"
            message = f"Duplicate roll number in file (line {seen[roll]})"
        else:
            existing = _find_by_roll(db, lecturer_id, roll)
            if existing is not None:
                enrolled = db.get(Enrollment, (existing.id, course.id))
                if enrolled is not None:
                    status = "duplicate"
                    message = "Already enrolled in this course"
                else:
                    message = "Will enroll existing student"

        seen.setdefault(roll, row["line"])
        if status == "ok":
            valid += 1
        else:
            errors += 1

        results.append({**row, "status": status, "message": message})

    return {
        "course_id": course.id,
        "valid_count": valid,
        "error_count": errors,
        "rows": results,
    }


def confirm_import(
    db: Session,
    lecturer_id: str,
    course_id: str,
    students: list[dict],
) -> dict:
    created = 0
    enrolled = 0
    for row in students:
        before = _find_by_roll(db, lecturer_id, row["roll_no"])
        student = add_student(
            db,
            lecturer_id,
            course_id,
            roll_no=row["roll_no"],
            name=row["name"],
            section=row.get("section") or "",
            email=row.get("email"),
        )
        enrolled += 1
        if before is None:
            created += 1
        _ = student
    return {"created": created, "enrolled": enrolled}
