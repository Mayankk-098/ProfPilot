from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.db import Base


class AcademicEvent(Base):
    __tablename__ = "academic_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    lecturer_id: Mapped[str] = mapped_column(
        String,
        index=True,
    )

    course_id: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
        index=True,
    )

    event_type: Mapped[str] = mapped_column(
        String,
        index=True,
    )

    title: Mapped[str] = mapped_column(
        String,
    )

    summary: Mapped[str] = mapped_column(
        Text,
    )

    occurred_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )