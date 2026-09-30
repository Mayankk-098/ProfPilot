from datetime import datetime

from sqlalchemy.orm import Session

from app.models.memory import AcademicEvent


def create_memory(
    db: Session,
    lecturer_id: str,
    event_type: str,
    title: str,
    summary: str,
    course_id: str | None = None,
    occurred_at: datetime | None = None,
) -> AcademicEvent:
    memory = AcademicEvent(
        lecturer_id=lecturer_id,
        course_id=course_id,
        event_type=event_type,
        title=title,
        summary=summary,
        occurred_at=occurred_at or datetime.utcnow(),
    )

    db.add(memory)
    db.commit()
    db.refresh(memory)

    return memory


def get_memories(
    db: Session,
    lecturer_id: str,
    course_id: str | None = None,
    limit: int = 20,
) -> list[AcademicEvent]:
    query = (
        db.query(AcademicEvent)
        .filter(AcademicEvent.lecturer_id == lecturer_id)
    )

    if course_id:
        query = query.filter(AcademicEvent.course_id == course_id)

    return (
        query
        .order_by(AcademicEvent.occurred_at.desc())
        .limit(limit)
        .all()
    )