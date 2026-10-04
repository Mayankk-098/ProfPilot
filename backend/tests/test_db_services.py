"""DB-backed tests against an in-memory SQLite DB seeded with demo data.
Run from backend/:  pytest tests/test_db_services.py

All dates are pinned (today = Thu 2026-10-01) so results are deterministic.
NOTE: written against the real stack but NOT executed in the authoring sandbox
(no SQLAlchemy/FastAPI available there) - run them once and report failures.
"""
from datetime import date, datetime, time
from app.models.attendance import Enrollment

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.db import Base
from app import models  # noqa: F401
from app.models.academic import Course, ScheduleItem, SyllabusUnit
from app.services import attendance_service, schedule_service
from app.services.course_metrics import compute_course_metrics
from seed.seed_demo import populate

TODAY = date(2026, 10, 1)                       # Thursday
NOW = datetime(2026, 10, 1, 9, 0)


@pytest.fixture()
def db():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, autoflush=False)()
    populate(session, today=TODAY)
    yield session
    session.close()


# ---------------- attendance ----------------
def test_attendance_flags_and_exact_75(db):
    res = attendance_service.build_course_attendance(db, db.get(Course, "dbms"))
    by_roll = {s["roll_no"]: s for s in res["students"]}
    assert res["classes_held"] == 8 and res["total_students"] == 62
    assert by_roll["24BCS018"]["flagged"] and by_roll["24BCS018"]["classes_needed_to_recover"] == 4
    assert by_roll["24BCS031"]["flagged"]
    assert by_roll["24BCS047"]["percentage"] == 75.0 and not by_roll["24BCS047"]["flagged"]
    assert by_roll["24BCS009"]["total"] == 7 and by_roll["24BCS009"]["percentage"] == 100.0  # excused excluded
    assert res["flagged_count"] == 2
    assert [s["roll_no"] for s in res["students"][:2]] == ["24BCS031", "24BCS018"]  # flagged first, lowest first


def test_flagged_only(db):
    res = attendance_service.build_course_attendance(db, db.get(Course, "ai"), flagged_only=True)
    assert {s["roll_no"] for s in res["students"]} == {"24ACS007", "24ACS022"}

def test_record_attendance_validation_and_full_roster(db):
    course = db.get(Course, "dbms")
    class_date = date(2026, 10, 2)  # real DBMS Friday occurrence

    with pytest.raises(ValueError):
        attendance_service.record_attendance(
            db, course, date(2026, 10, 9),
            [("stu_24BCS001", "present")], today=TODAY,
        )

    with pytest.raises(ValueError):
        attendance_service.record_attendance(
            db, course, class_date,
            [("stu_24ACS001", "present")], today=date(2026, 10, 3),
        )

    enrolled_ids = [
        enrollment.student_id
        for enrollment in db.query(Enrollment)
        .filter(Enrollment.course_id == "dbms")
        .all()
    ]
    marks = [(student_id, "present") for student_id in enrolled_ids]

    with pytest.raises(ValueError):
        attendance_service.record_attendance(
            db, course, class_date, marks[:-1], today=date(2026, 10, 3),
        )

    result = attendance_service.record_attendance(
        db, course, class_date, marks, today=date(2026, 10, 3),
    )
    assert result["created"] == len(enrolled_ids)
    assert result["updated"] == 0

    with pytest.raises(ValueError):
        attendance_service.record_attendance(
            db, course, class_date, marks, today=date(2026, 10, 3),
        )

    marks[0] = (marks[0][0], "absent")
    corrected = attendance_service.correct_attendance(
        db, course, class_date, marks, today=date(2026, 10, 3),
    )
    assert corrected["updated"] == len(enrolled_ids)


# ---------------- derived academic data ----------------
def test_progress_derived_and_consistent(db):
    course = db.get(Course, "dbms")
    m = compute_course_metrics(db, course, NOW)
    assert m["progress"] == 21.9                      # 7 of 32 topics
    assert m["planned_progress"] == 25.0
    assert m["predicted_completion"] == "7 December 2026"
    assert m["planned_completion"] == "3 December 2026"
    assert m["total_students"] == 62
    assert m["last_attendance_date"] == "2026-09-30"
    units = {u.id: u.progress for u in db.query(SyllabusUnit).filter_by(course_id="dbms")}
    assert units["dbms-u1"] == 60.0
    topics = [t for u in course.units for t in u.topics]
    assert sum(t.completed for t in topics) == 7
    # every completed topic points at a lecture that exists in this course
    lecture_ids = {l.id for l in course.lectures}
    assert all(t.covered_in_lecture_id in lecture_ids for t in topics if t.completed)


def test_course_with_tiny_syllabus_has_no_division_errors(db):
    m = compute_course_metrics(db, db.get(Course, "os"), NOW)
    assert m["progress"] == 50.0 and m["total_students"] == 10


# ---------------- schedule ----------------
def test_today_is_thursday_only_ai(db):
    items = schedule_service.day_schedule(db, TODAY, lecturer_id="lecturer_001")
    assert [i["id"] for i in items] == ["ai-thu"]


def test_next_class_is_time_aware_and_lecturer_specific(db):
    assert schedule_service.next_class(db, NOW, "lecturer_001")["id"] == "ai-thu"
    after = datetime(2026, 10, 1, 13, 0)
    assert schedule_service.next_class(db, after, "lecturer_001")["id"] == "dbms-fri"
    assert schedule_service.next_class(db, after, "lecturer_002")["id"] == "os-fri"
    # the 15:00 Friday meeting is never returned as a "class"
    assert schedule_service.next_class(db, datetime(2026, 10, 2, 10, 30), "lecturer_001")["item_type"] == "class"


def test_cancel_changes_next_class_and_can_be_restored(db):
    after = datetime(2026, 10, 1, 13, 0)
    schedule_service.cancel_class(db, "dbms-fri", date(2026, 10, 2), "Conference", today=TODAY)
    assert schedule_service.next_class(db, after, "lecturer_001")["id"] == "dbms-mon"
    shown = schedule_service.day_schedule(db, date(2026, 10, 2), "lecturer_001", include_cancelled=True)
    assert [(i["id"], i["status"]) for i in shown] == [("dbms-fri", "cancelled"), ("meeting-faculty-fri", "scheduled")]
    schedule_service.restore_class(db, "dbms-fri", date(2026, 10, 2))
    assert schedule_service.next_class(db, after, "lecturer_001")["id"] == "dbms-fri"


def test_reschedule_and_conflict(db):
    with pytest.raises(ValueError):                                   # clashes with AI Mon 12:00
        schedule_service.reschedule_class(db, "dbms-fri", date(2026, 10, 2), date(2026, 10, 5), time(12, 0), today=TODAY)
    schedule_service.reschedule_class(db, "dbms-fri", date(2026, 10, 2), date(2026, 10, 5), time(14, 0), today=TODAY)
    mon = schedule_service.day_schedule(db, date(2026, 10, 5), "lecturer_001")
    assert [i["id"] for i in mon] == ["dbms-mon", "ai-mon", "dbms-fri"]
    moved = mon[-1]
    assert moved["status"] == "rescheduled" and moved["start_time"] == "14:00"
    assert (moved["time"], moved["period"]) == ("02:00", "PM") and moved["original_date"] == "2026-10-02"


def test_invalid_changes(db):
    with pytest.raises(ValueError):                                   # Saturday is not a dbms-fri date
        schedule_service.cancel_class(db, "dbms-fri", date(2026, 10, 3), today=TODAY)
    with pytest.raises(ValueError):                                   # already in the past
        schedule_service.cancel_class(db, "dbms-fri", date(2026, 9, 25), today=TODAY)
    with pytest.raises(LookupError):
        schedule_service.cancel_class(db, "nope", date(2026, 10, 2), today=TODAY)


def test_cancelling_a_class_moves_predicted_completion_later(db):
    course = db.get(Course, "dbms")
    before = compute_course_metrics(db, course, NOW)["predicted_completion"]
    schedule_service.cancel_class(db, "dbms-fri", date(2026, 10, 2), today=TODAY)
    after = compute_course_metrics(db, course, NOW)["predicted_completion"]
    assert datetime.strptime(after, "%d %B %Y") > datetime.strptime(before, "%d %B %Y")


def test_attendance_date_must_be_active_and_reschedule_moves_valid_date(db):
    course = db.get(Course, "dbms")
    enrolled_ids = [
        enrollment.student_id
        for enrollment in db.query(Enrollment)
        .filter(Enrollment.course_id == "dbms")
        .all()
    ]
    marks = [(student_id, "present") for student_id in enrolled_ids]

    schedule_service.cancel_class(
        db, "dbms-fri", date(2026, 10, 2),
        today=TODAY,
    )
    with pytest.raises(ValueError, match="active scheduled class date"):
        attendance_service.record_attendance(
            db, course, date(2026, 10, 2), marks, today=date(2026, 10, 3),
        )

    schedule_service.restore_class(db, "dbms-fri", date(2026, 10, 2))
    schedule_service.reschedule_class(
        db, "dbms-fri", date(2026, 10, 2), date(2026, 10, 8),
        time(14, 0), time(15, 0), today=TODAY,
    )

    with pytest.raises(ValueError, match="active scheduled class date"):
        attendance_service.record_attendance(
            db, course, date(2026, 10, 2), marks, today=date(2026, 10, 8),
        )

    result = attendance_service.record_attendance(
        db, course, date(2026, 10, 8), marks, today=date(2026, 10, 8),
    )
    assert result["created"] == len(marks)
