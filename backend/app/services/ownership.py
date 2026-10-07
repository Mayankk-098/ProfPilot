from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.academic import Course, ScheduleItem, SyllabusTopic, SyllabusUnit
from app.models.attendance import Student


def require_owned_course(
    db: Session,
    course_id: str,
    lecturer_id: str,
) -> Course:
    course = (
        db.query(Course)
        .filter(
            Course.id == course_id,
            Course.lecturer_id == lecturer_id,
        )
        .first()
    )
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")
    return course


def require_owned_unit(
    db: Session,
    unit_id: str,
    lecturer_id: str,
) -> SyllabusUnit:
    unit = (
        db.query(SyllabusUnit)
        .join(Course, Course.id == SyllabusUnit.course_id)
        .filter(
            SyllabusUnit.id == unit_id,
            Course.lecturer_id == lecturer_id,
        )
        .first()
    )
    if unit is None:
        raise HTTPException(status_code=404, detail="Syllabus unit not found")
    return unit


def require_owned_topic(
    db: Session,
    topic_id: str,
    lecturer_id: str,
) -> SyllabusTopic:
    topic = (
        db.query(SyllabusTopic)
        .join(SyllabusUnit, SyllabusUnit.id == SyllabusTopic.unit_id)
        .join(Course, Course.id == SyllabusUnit.course_id)
        .filter(
            SyllabusTopic.id == topic_id,
            Course.lecturer_id == lecturer_id,
        )
        .first()
    )
    if topic is None:
        raise HTTPException(status_code=404, detail="Syllabus topic not found")
    return topic


def require_owned_student(
    db: Session,
    student_id: str,
    lecturer_id: str,
) -> Student:
    student = (
        db.query(Student)
        .filter(
            Student.id == student_id,
            Student.lecturer_id == lecturer_id,
        )
        .first()
    )
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")
    return student


def require_owned_schedule_item(
    db: Session,
    item_id: str,
    lecturer_id: str,
) -> ScheduleItem:
    item = (
        db.query(ScheduleItem)
        .filter(
            ScheduleItem.id == item_id,
            ScheduleItem.lecturer_id == lecturer_id,
        )
        .first()
    )
    if item is None:
        raise HTTPException(status_code=404, detail="Schedule item not found")
    return item
