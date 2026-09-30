from datetime import datetime

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.db import Base


class Lecturer(Base):
    __tablename__ = "lecturers"

    id: Mapped[str] = mapped_column(
        String(50),
        primary_key=True,
    )

    name: Mapped[str] = mapped_column(String(120))
    initials: Mapped[str] = mapped_column(String(10))
    title: Mapped[str] = mapped_column(String(100))
    department: Mapped[str] = mapped_column(String(150))
    email: Mapped[str] = mapped_column(String(150), unique=True)

    experience: Mapped[int] = mapped_column(Integer)

    courses = relationship(
        "Course",
        back_populates="lecturer",
    )


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[str] = mapped_column(
        String(50),
        primary_key=True,
    )

    code: Mapped[str] = mapped_column(String(30))
    name: Mapped[str] = mapped_column(String(150))
    short_name: Mapped[str] = mapped_column(String(30))
    section: Mapped[str] = mapped_column(String(30))

    progress: Mapped[float] = mapped_column(Float)
    planned_progress: Mapped[float] = mapped_column(Float)

    current_pace: Mapped[float] = mapped_column(Float)
    required_pace: Mapped[float] = mapped_column(Float)

    predicted_completion: Mapped[str] = mapped_column(String(100))
    planned_completion: Mapped[str] = mapped_column(String(100))

    total_students: Mapped[int] = mapped_column(Integer)
    present_today: Mapped[int] = mapped_column(Integer)
    absent_today: Mapped[int] = mapped_column(Integer)

    lecturer_id: Mapped[str] = mapped_column(
        ForeignKey("lecturers.id")
    )

    lecturer = relationship(
        "Lecturer",
        back_populates="courses",
    )

    units = relationship(
        "SyllabusUnit",
        back_populates="course",
        cascade="all, delete-orphan",
    )

    lectures = relationship(
        "LectureLog",
        back_populates="course",
        cascade="all, delete-orphan",
    )


class SyllabusUnit(Base):
    __tablename__ = "syllabus_units"

    id: Mapped[str] = mapped_column(
        String(50),
        primary_key=True,
    )

    name: Mapped[str] = mapped_column(String(150))
    progress: Mapped[float] = mapped_column(Float)

    course_id: Mapped[str] = mapped_column(
        ForeignKey("courses.id")
    )

    course = relationship(
        "Course",
        back_populates="units",
    )

    topics = relationship(
        "SyllabusTopic",
        back_populates="unit",
        cascade="all, delete-orphan",
    )


class SyllabusTopic(Base):
    __tablename__ = "syllabus_topics"

    id: Mapped[str] = mapped_column(
        String(50),
        primary_key=True,
    )

    name: Mapped[str] = mapped_column(String(150))
    completed: Mapped[bool] = mapped_column(default=False)
    planned_date: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    unit_id: Mapped[str] = mapped_column(
        ForeignKey("syllabus_units.id")
    )

    unit = relationship(
        "SyllabusUnit",
        back_populates="topics",
    )


class LectureLog(Base):
    __tablename__ = "lecture_logs"

    id: Mapped[str] = mapped_column(
        String(50),
        primary_key=True,
    )

    date: Mapped[str] = mapped_column(String(50))
    duration: Mapped[int] = mapped_column(Integer)
    description: Mapped[str] = mapped_column(Text)

    course_id: Mapped[str] = mapped_column(
        ForeignKey("courses.id")
    )

    course = relationship(
        "Course",
        back_populates="lectures",
    )


class ScheduleItem(Base):
    __tablename__ = "schedule_items"

    id: Mapped[str] = mapped_column(
        String(50),
        primary_key=True,
    )

    subject: Mapped[str] = mapped_column(String(150))
    code: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )
    batch: Mapped[str] = mapped_column(String(50))

    time: Mapped[str] = mapped_column(String(20))
    period: Mapped[str] = mapped_column(String(5))

    room: Mapped[str] = mapped_column(String(100))
    item_type: Mapped[str] = mapped_column(String(30))

    course_id: Mapped[str | None] = mapped_column(
        ForeignKey("courses.id"),
        nullable=True,
    )