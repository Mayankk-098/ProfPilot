from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
import datetime as dt

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    Time,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.db import Base


class Lecturer(Base):
    __tablename__ = "lecturers"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)

    name: Mapped[str] = mapped_column(String(120))
    initials: Mapped[str] = mapped_column(String(10))
    title: Mapped[str] = mapped_column(String(100))
    department: Mapped[str] = mapped_column(String(150))
    email: Mapped[str] = mapped_column(String(150), unique=True)

    experience: Mapped[int] = mapped_column(Integer)

    courses = relationship("Course", back_populates="lecturer")
    schedule_items = relationship("ScheduleItem", back_populates="lecturer")
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    email: Mapped[str] = mapped_column(
        String(150),
        unique=True,
        nullable=False,
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    lecturer_id: Mapped[str] = mapped_column(
        ForeignKey("lecturers.id"),
        unique=True,
        nullable=False,
    )

    lecturer = relationship("Lecturer")


class Course(Base):
    """Stored: identity + term dates. Everything about progress, pace, completion
    dates and attendance counts is DERIVED (see app/services/course_metrics.py)
    and exposed below as read-only properties with the same names as the old
    columns, so existing callers (routers, context engine, AI) keep working."""

    __tablename__ = "courses"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)

    code: Mapped[str] = mapped_column(String(30))
    name: Mapped[str] = mapped_column(String(150))
    short_name: Mapped[str] = mapped_column(String(30))
    section: Mapped[str] = mapped_column(String(30))

    start_date: Mapped[dt.date] = mapped_column(Date)
    planned_end_date: Mapped[dt.date] = mapped_column(Date)

    lecturer_id: Mapped[str] = mapped_column(ForeignKey("lecturers.id"))

    lecturer = relationship("Lecturer", back_populates="courses")

    units = relationship(
        "SyllabusUnit",
        back_populates="course",
        cascade="all, delete-orphan",
        order_by="SyllabusUnit.position",
    )

    lectures = relationship(
        "LectureLog",
        back_populates="course",
        cascade="all, delete-orphan",
        order_by="LectureLog.lecture_date",
    )

    enrollments = relationship(
        "Enrollment",
        back_populates="course",
        cascade="all, delete-orphan",
    )

    # ---- derived (read-only) -------------------------------------------
    def _metrics(self) -> dict:
        from app.services.course_metrics import get_course_metrics

        return get_course_metrics(self)

    @property
    def progress(self) -> float:
        return self._metrics()["progress"]

    @property
    def planned_progress(self) -> float:
        return self._metrics()["planned_progress"]

    @property
    def current_pace(self) -> float:
        return self._metrics()["current_pace"]

    @property
    def required_pace(self) -> float:
        return self._metrics()["required_pace"]

    @property
    def predicted_completion(self) -> str:
        return self._metrics()["predicted_completion"]

    @property
    def planned_completion(self) -> str:
        return self._metrics()["planned_completion"]

    @property
    def total_students(self) -> int:
        return self._metrics()["total_students"]

    @property
    def present_today(self) -> int:
        return self._metrics()["present_today"]

    @property
    def absent_today(self) -> int:
        return self._metrics()["absent_today"]

    @property
    def last_attendance_date(self) -> str | None:
        return self._metrics()["last_attendance_date"]


class SyllabusUnit(Base):
    __tablename__ = "syllabus_units"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)

    name: Mapped[str] = mapped_column(String(150))
    position: Mapped[int] = mapped_column(Integer, default=0)

    course_id: Mapped[str] = mapped_column(ForeignKey("courses.id"))

    course = relationship("Course", back_populates="units")

    topics = relationship(
        "SyllabusTopic",
        back_populates="unit",
        cascade="all, delete-orphan",
        order_by="SyllabusTopic.position",
    )

    @property
    def progress(self) -> float:
        """Derived: % of this unit's topics that have been covered."""
        total = len(self.topics)
        done = sum(1 for t in self.topics if t.completed)
        return round(done / total * 100, 1) if total else 0.0


class SyllabusTopic(Base):
    __tablename__ = "syllabus_topics"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)

    name: Mapped[str] = mapped_column(String(150))
    position: Mapped[int] = mapped_column(Integer, default=0)
    planned_date: Mapped[dt.date | None] = mapped_column(Date, nullable=True)

    # A topic is complete exactly when a lecture is recorded as covering it.
    covered_in_lecture_id: Mapped[str | None] = mapped_column(
        ForeignKey("lecture_logs.id"),
        nullable=True,
    )

    # Preserves completion recorded in the legacy ProfPilot database
    # when no historical lecture linkage exists.
    legacy_completed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    unit_id: Mapped[str] = mapped_column(ForeignKey("syllabus_units.id"))

    unit = relationship("SyllabusUnit", back_populates="topics")

    @property
    def completed(self) -> bool:
        return (
            self.covered_in_lecture_id is not None
            or self.legacy_completed
        )


class LectureLog(Base):
    __tablename__ = "lecture_logs"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)

    lecture_date: Mapped[dt.date] = mapped_column(Date, index=True)
    duration: Mapped[int] = mapped_column(Integer)
    description: Mapped[str] = mapped_column(Text)

    course_id: Mapped[str] = mapped_column(ForeignKey("courses.id"))

    course = relationship("Course", back_populates="lectures")

    @property
    def date(self) -> str:
        """Display string, same format the API always returned: '18 September 2026'."""
        return f"{self.lecture_date.day} {self.lecture_date.strftime('%B %Y')}"

    @property
    def date_iso(self) -> str:
        return self.lecture_date.isoformat()


class ScheduleItem(Base):
    """One recurring weekly slot (class or meeting) belonging to a lecturer."""

    __tablename__ = "schedule_items"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)

    subject: Mapped[str] = mapped_column(String(150))
    code: Mapped[str | None] = mapped_column(String(30), nullable=True)
    batch: Mapped[str] = mapped_column(String(50))

    weekday: Mapped[int] = mapped_column(Integer)          # Mon=0 .. Sun=6
    start_time: Mapped[dt.time] = mapped_column(Time)
    end_time: Mapped[dt.time] = mapped_column(Time)

    room: Mapped[str] = mapped_column(String(100))
    item_type: Mapped[str] = mapped_column(String(30))     # class | meeting

    lecturer_id: Mapped[str] = mapped_column(ForeignKey("lecturers.id"))
    course_id: Mapped[str | None] = mapped_column(
        ForeignKey("courses.id"),
        nullable=True,
    )

    lecturer = relationship("Lecturer", back_populates="schedule_items")
    changes = relationship(
        "ScheduleChange",
        back_populates="item",
        cascade="all, delete-orphan",
    )

    # Old 12-hour columns are now derived from start_time.
    @property
    def time(self) -> str:
        return self.start_time.strftime("%I:%M")

    @property
    def period(self) -> str:
        return "AM" if self.start_time.hour < 12 else "PM"


class ScheduleChange(Base):
    """A one-off cancellation or reschedule of a weekly slot on a specific date."""

    __tablename__ = "schedule_changes"
    __table_args__ = (UniqueConstraint("item_id", "on_date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    item_id: Mapped[str] = mapped_column(ForeignKey("schedule_items.id"))
    on_date: Mapped[dt.date] = mapped_column(Date)         # original date

    status: Mapped[str] = mapped_column(String(20))        # cancelled | rescheduled
    new_date: Mapped[dt.date | None] = mapped_column(Date, nullable=True)
    new_start_time: Mapped[dt.time | None] = mapped_column(Time, nullable=True)
    new_end_time: Mapped[dt.time | None] = mapped_column(Time, nullable=True)
    new_room: Mapped[str | None] = mapped_column(String(100), nullable=True)
    reason: Mapped[str | None] = mapped_column(String(300), nullable=True)

    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime, default=dt.datetime.now
    )

    item = relationship("ScheduleItem", back_populates="changes")
