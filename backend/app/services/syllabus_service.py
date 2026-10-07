from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from app.models.academic import SyllabusTopic, SyllabusUnit
from app.services.ids import new_id
from app.services.ownership import (
    require_owned_course,
    require_owned_topic,
    require_owned_unit,
)


def add_unit(
    db: Session,
    lecturer_id: str,
    course_id: str,
    name: str,
) -> SyllabusUnit:
    course = require_owned_course(db, course_id, lecturer_id)
    position = len(course.units)
    unit = SyllabusUnit(
        id=new_id("unit"),
        name=name.strip(),
        position=position,
        course_id=course.id,
    )
    db.add(unit)
    db.commit()
    db.refresh(unit)
    return unit


def update_unit(
    db: Session,
    lecturer_id: str,
    unit_id: str,
    name: str | None = None,
) -> SyllabusUnit:
    unit = require_owned_unit(db, unit_id, lecturer_id)
    if name is not None:
        unit.name = name.strip()
    db.commit()
    db.refresh(unit)
    return unit


def delete_unit(
    db: Session,
    lecturer_id: str,
    unit_id: str,
) -> None:
    unit = require_owned_unit(db, unit_id, lecturer_id)
    course_id = unit.course_id
    db.delete(unit)
    db.flush()
    remaining = (
        db.query(SyllabusUnit)
        .filter(SyllabusUnit.course_id == course_id)
        .order_by(SyllabusUnit.position, SyllabusUnit.id)
        .all()
    )
    for index, item in enumerate(remaining):
        item.position = index
    db.commit()


def reorder_units(
    db: Session,
    lecturer_id: str,
    course_id: str,
    unit_ids: list[str],
) -> list[SyllabusUnit]:
    course = require_owned_course(db, course_id, lecturer_id)
    current = {unit.id: unit for unit in course.units}
    if set(unit_ids) != set(current):
        raise ValueError("Reorder list must include every unit exactly once")
    for index, unit_id in enumerate(unit_ids):
        current[unit_id].position = index
    db.commit()
    return (
        db.query(SyllabusUnit)
        .filter(SyllabusUnit.course_id == course.id)
        .order_by(SyllabusUnit.position)
        .all()
    )


def add_topic(
    db: Session,
    lecturer_id: str,
    unit_id: str,
    name: str,
    planned_date: date | None = None,
) -> SyllabusTopic:
    unit = require_owned_unit(db, unit_id, lecturer_id)
    position = len(unit.topics)
    topic = SyllabusTopic(
        id=new_id("top"),
        name=name.strip(),
        position=position,
        planned_date=planned_date,
        unit_id=unit.id,
    )
    db.add(topic)
    db.commit()
    db.refresh(topic)
    return topic


def update_topic(
    db: Session,
    lecturer_id: str,
    topic_id: str,
    *,
    name: str | None = None,
    planned_date: date | None = None,
    clear_planned_date: bool = False,
) -> SyllabusTopic:
    topic = require_owned_topic(db, topic_id, lecturer_id)
    if name is not None:
        topic.name = name.strip()
    if clear_planned_date:
        topic.planned_date = None
    elif planned_date is not None:
        topic.planned_date = planned_date
    db.commit()
    db.refresh(topic)
    return topic


def delete_topic(
    db: Session,
    lecturer_id: str,
    topic_id: str,
) -> None:
    topic = require_owned_topic(db, topic_id, lecturer_id)
    unit_id = topic.unit_id
    db.delete(topic)
    db.flush()
    remaining = (
        db.query(SyllabusTopic)
        .filter(SyllabusTopic.unit_id == unit_id)
        .order_by(SyllabusTopic.position, SyllabusTopic.id)
        .all()
    )
    for index, item in enumerate(remaining):
        item.position = index
    db.commit()


def reorder_topics(
    db: Session,
    lecturer_id: str,
    unit_id: str,
    topic_ids: list[str],
) -> list[SyllabusTopic]:
    unit = require_owned_unit(db, unit_id, lecturer_id)
    current = {topic.id: topic for topic in unit.topics}
    if set(topic_ids) != set(current):
        raise ValueError("Reorder list must include every topic exactly once")
    for index, topic_id in enumerate(topic_ids):
        current[topic_id].position = index
    db.commit()
    return (
        db.query(SyllabusTopic)
        .filter(SyllabusTopic.unit_id == unit.id)
        .order_by(SyllabusTopic.position)
        .all()
    )
