from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.academic import Course, ScheduleItem, SyllabusTopic
from app.models.attendance import AttendanceRecord, Enrollment, Student
from app.models.memory import AcademicEvent
from app.services.ids import new_id
from app.services.ownership import require_owned_course


def create_course(
    db: Session,
    lecturer_id: str,
    *,
    code: str,
    name: str,
    short_name: str,
    section: str,
    start_date: date,
    planned_end_date: date,
) -> Course:
    if planned_end_date < start_date:
        raise ValueError("planned_end_date must be on or after start_date")

    existing = db.scalar(
        select(Course.id).where(
            Course.lecturer_id == lecturer_id,
            Course.code == code.strip(),
        )
    )
    if existing is not None:
        raise ValueError("A course with this code already exists")

    course = Course(
        id=new_id("crs"),
        code=code.strip(),
        name=name.strip(),
        short_name=short_name.strip(),
        section=section.strip(),
        start_date=start_date,
        planned_end_date=planned_end_date,
        lecturer_id=lecturer_id,
    )
    db.add(course)
    db.commit()
    db.refresh(course)
    return course


def update_course(
    db: Session,
    lecturer_id: str,
    course_id: str,
    **fields,
) -> Course:
    course = require_owned_course(db, course_id, lecturer_id)

    if "code" in fields and fields["code"] is not None:
        code = fields["code"].strip()
        clash = db.scalar(
            select(Course.id).where(
                Course.lecturer_id == lecturer_id,
                Course.code == code,
                Course.id != course.id,
            )
        )
        if clash is not None:
            raise ValueError("A course with this code already exists")
        course.code = code

    for key in ("name", "short_name", "section"):
        if key in fields and fields[key] is not None:
            setattr(course, key, fields[key].strip())

    if fields.get("start_date") is not None:
        course.start_date = fields["start_date"]
    if fields.get("planned_end_date") is not None:
        course.planned_end_date = fields["planned_end_date"]
    if course.planned_end_date < course.start_date:
        raise ValueError("planned_end_date must be on or after start_date")

    db.commit()
    db.refresh(course)
    return course


def delete_course(
    db: Session,
    lecturer_id: str,
    course_id: str,
) -> None:
    course = require_owned_course(db, course_id, lecturer_id)

    unit_ids = [unit.id for unit in course.units]
    if unit_ids:
        db.query(SyllabusTopic).filter(
            SyllabusTopic.unit_id.in_(unit_ids)
        ).update(
            {SyllabusTopic.covered_in_lecture_id: None},
            synchronize_session=False,
        )

    db.query(AttendanceRecord).filter(
        AttendanceRecord.course_id == course.id
    ).delete(synchronize_session=False)

    db.query(ScheduleItem).filter(
        ScheduleItem.course_id == course.id,
        ScheduleItem.lecturer_id == lecturer_id,
    ).delete(synchronize_session=False)

    db.query(AcademicEvent).filter(
        AcademicEvent.course_id == course.id,
        AcademicEvent.lecturer_id == lecturer_id,
    ).delete(synchronize_session=False)

    enrolled_ids = [
        row[0]
        for row in db.query(Enrollment.student_id)
        .filter(Enrollment.course_id == course.id)
        .all()
    ]

    db.delete(course)
    db.flush()

    if enrolled_ids:
        still_enrolled = {
            row[0]
            for row in db.query(Enrollment.student_id)
            .filter(Enrollment.student_id.in_(enrolled_ids))
            .all()
        }
        orphans = [
            student_id
            for student_id in enrolled_ids
            if student_id not in still_enrolled
        ]
        if orphans:
            db.query(Student).filter(
                Student.id.in_(orphans),
                Student.lecturer_id == lecturer_id,
            ).delete(synchronize_session=False)

    db.commit()
