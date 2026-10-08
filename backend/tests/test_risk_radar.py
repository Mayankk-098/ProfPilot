"""Deterministic tests for the academic risk radar."""

from datetime import date, datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.db import Base
from app.models.academic import Course
from app import models  # noqa: F401
from app.services import clock
from app.services.risk_radar_service import build_risk_radar
from seed.seed_demo import populate


def test_risk_radar_explains_attendance_and_recovery():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)

    session = sessionmaker(bind=engine, autoflush=False)()
    try:
        populate(session, today=date(2026, 10, 1))

        result = build_risk_radar(
            session,
            lecturer_id="lecturer_001",
        )

        assert result["summary"]["total_courses"] == 2
        assert result["summary"]["flagged_students"] == 4

        dbms = next(
            course
            for course in result["courses"]
            if course["course_id"] == "dbms"
        )

        assert dbms["risk_level"] == "low"
        assert dbms["risk_score"] < 25
        assert dbms["attendance"]["flagged_count"] == 2

        attendance_driver = next(
            driver
            for driver in dbms["drivers"]
            if driver["type"] == "attendance"
        )

        assert "2 of 62" in attendance_driver["message"]

        recovery = next(
            student
            for student in dbms["recovery_plan"]
            if student["roll_no"] == "24BCS018"
        )

        assert recovery["classes_needed_to_recover"] == 4
        assert recovery["projected_attendance_after_recovery"] >= 75
        assert "next 4 consecutive classes" in recovery["action"]
    finally:
        session.close()
