import datetime as dt

from sqlalchemy import CheckConstraint, Date, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.db import Base

ATTENDANCE_STATUSES = ("present", "absent", "excused")


class Student(Base):
    __tablename__ = "students"
    __table_args__ = (
        UniqueConstraint("lecturer_id", "roll_no"),
    )

    id: Mapped[str] = mapped_column(String(50), primary_key=True)

    roll_no: Mapped[str] = mapped_column(String(30), index=True)
    name: Mapped[str] = mapped_column(String(120))
    section: Mapped[str] = mapped_column(String(30))
    lecturer_id: Mapped[str] = mapped_column(
        ForeignKey("lecturers.id"),
        index=True,
        nullable=False,
    )

    enrollments = relationship(
        "Enrollment",
        back_populates="student",
        cascade="all, delete-orphan",
    )


class Enrollment(Base):
    """Which students are in which course (a student can take many courses)."""

    __tablename__ = "enrollments"

    student_id: Mapped[str] = mapped_column(
        ForeignKey("students.id"), primary_key=True
    )
    course_id: Mapped[str] = mapped_column(
        ForeignKey("courses.id"), primary_key=True
    )

    student = relationship("Student", back_populates="enrollments")
    course = relationship("Course", back_populates="enrollments")


class AttendanceRecord(Base):
    """One student, one course, one class date."""

    __tablename__ = "attendance_records"
    __table_args__ = (
        UniqueConstraint("student_id", "course_id", "class_date"),
        CheckConstraint("status IN ('present', 'absent', 'excused')"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    student_id: Mapped[str] = mapped_column(
        ForeignKey("students.id"), index=True
    )
    course_id: Mapped[str] = mapped_column(
        ForeignKey("courses.id"), index=True
    )
    class_date: Mapped[dt.date] = mapped_column(Date, index=True)
    status: Mapped[str] = mapped_column(String(10))
