"""Tests for lecturer-scoped attendance workflows."""
from __future__ import annotations
import pytest
import os

os.environ.setdefault("SECRET_KEY", "attendance-test-secret")

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.db import Base, get_db
from app.main import app

@pytest.fixture(autouse=True)
def fixed_clock(monkeypatch):
    monkeypatch.setenv(
        "PROFPILOT_FIXED_NOW",
        "2026-10-07T12:00:00",
    )

def make_client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)

    session_local = sessionmaker(
        bind=engine,
        autoflush=False,
    )
    db = session_local()

    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app), db, engine


def _register(client, *, email: str, name: str) -> dict:
    response = client.post(
        "/auth/register",
        json={
            "name": name,
            "email": email,
            "password": "strong-pass-123",
            "department": "Computer Science",
            "title": "Lecturer",
        },
    )
    assert response.status_code == 201, response.text

    return {
        "Authorization": f"Bearer {response.json()['access_token']}"
    }


def _create_course(client, headers, code="ATT-101"):
    response = client.post(
        "/courses/",
        headers=headers,
        json={
            "code": code,
            "name": "Attendance Testing",
            "short_name": "ATT",
            "section": "CSE-A",
            "start_date": "2026-10-01",
            "planned_end_date": "2026-12-01",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


def _add_student(client, headers, course_id, roll_no, name):
    response = client.post(
        f"/courses/{course_id}/students",
        headers=headers,
        json={
            "roll_no": roll_no,
            "name": name,
            "section": "CSE-A",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


def _create_monday_schedule(client, headers, course_id):
    response = client.post(
        "/schedule/templates",
        headers=headers,
        json={
            "weekday": 0,
            "start_time": "09:00",
            "end_time": "10:00",
            "room": "LT-1",
            "course_id": course_id,
        },
    )
    assert response.status_code == 201, response.text


def test_record_and_summarize_attendance():
    client, db, engine = make_client()

    try:
        lecturer = _register(
            client,
            email="attendance@test.edu",
            name="Attendance Lecturer",
        )

        course_id = _create_course(client, lecturer)

        alice_id = _add_student(
            client,
            lecturer,
            course_id,
            "24BCS101",
            "Alice Kumar",
        )
        bob_id = _add_student(
            client,
            lecturer,
            course_id,
            "24BCS102",
            "Bob Singh",
        )

        # 2026-10-05 is a Monday.
        _create_monday_schedule(
            client,
            lecturer,
            course_id,
        )

        response = client.post(
            f"/attendance/{course_id}/records",
            headers=lecturer,
            json={
                "class_date": "2026-10-05",
                "records": [
                    {
                        "student_id": alice_id,
                        "status": "present",
                    },
                    {
                        "student_id": bob_id,
                        "status": "absent",
                    },
                ],
            },
        )

        assert response.status_code == 200, response.text

        body = client.get(
            f"/attendance/{course_id}",
            headers=lecturer,
        )

        assert body.status_code == 200, body.text

        payload = body.json()

        assert payload["course_id"] == course_id
        assert payload["classes_held"] == 1
        assert payload["total_students"] == 2
        assert payload["present_last_class"] == 1
        assert payload["absent_last_class"] == 1
        assert payload["flagged_count"] == 1

        students = {
            student["student_id"]: student
            for student in payload["students"]
        }

        assert students[alice_id]["attended"] == 1
        assert students[alice_id]["total"] == 1
        assert students[alice_id]["percentage"] == 100.0
        assert students[alice_id]["flagged"] is False

        assert students[bob_id]["attended"] == 0
        assert students[bob_id]["total"] == 1
        assert students[bob_id]["percentage"] == 0.0
        assert students[bob_id]["flagged"] is True
        assert students[bob_id]["classes_needed_to_recover"] == 3

    finally:
        app.dependency_overrides.clear()
        db.close()
        engine.dispose()


def test_attendance_requires_complete_roster():
    client, db, engine = make_client()

    try:
        lecturer = _register(
            client,
            email="complete@test.edu",
            name="Complete Roster Lecturer",
        )

        course_id = _create_course(client, lecturer)

        alice_id = _add_student(
            client,
            lecturer,
            course_id,
            "24BCS201",
            "Alice",
        )
        bob_id = _add_student(
            client,
            lecturer,
            course_id,
            "24BCS202",
            "Bob",
        )

        _create_monday_schedule(
            client,
            lecturer,
            course_id,
        )

        response = client.post(
            f"/attendance/{course_id}/records",
            headers=lecturer,
            json={
                "class_date": "2026-10-05",
                "records": [
                    {
                        "student_id": alice_id,
                        "status": "present",
                    }
                ],
            },
        )

        assert response.status_code == 422
        assert "Missing enrolled students" in response.text

    finally:
        app.dependency_overrides.clear()
        db.close()
        engine.dispose()


def test_duplicate_attendance_session_is_rejected():
    client, db, engine = make_client()

    try:
        lecturer = _register(
            client,
            email="duplicate-attendance@test.edu",
            name="Duplicate Lecturer",
        )

        course_id = _create_course(client, lecturer)

        student_id = _add_student(
            client,
            lecturer,
            course_id,
            "24BCS301",
            "Student",
        )

        _create_monday_schedule(
            client,
            lecturer,
            course_id,
        )

        payload = {
            "class_date": "2026-10-05",
            "records": [
                {
                    "student_id": student_id,
                    "status": "present",
                }
            ],
        }

        first = client.post(
            f"/attendance/{course_id}/records",
            headers=lecturer,
            json=payload,
        )
        assert first.status_code == 200, first.text

        second = client.post(
            f"/attendance/{course_id}/records",
            headers=lecturer,
            json=payload,
        )

        assert second.status_code == 422
        assert "already been recorded" in second.text

    finally:
        app.dependency_overrides.clear()
        db.close()
        engine.dispose()


def test_attendance_correction_replaces_session():
    client, db, engine = make_client()

    try:
        lecturer = _register(
            client,
            email="correction@test.edu",
            name="Correction Lecturer",
        )

        course_id = _create_course(client, lecturer)

        alice_id = _add_student(
            client,
            lecturer,
            course_id,
            "24BCS401",
            "Alice",
        )
        bob_id = _add_student(
            client,
            lecturer,
            course_id,
            "24BCS402",
            "Bob",
        )

        _create_monday_schedule(
            client,
            lecturer,
            course_id,
        )

        original = {
            "class_date": "2026-10-05",
            "records": [
                {
                    "student_id": alice_id,
                    "status": "present",
                },
                {
                    "student_id": bob_id,
                    "status": "absent",
                },
            ],
        }

        created = client.post(
            f"/attendance/{course_id}/records",
            headers=lecturer,
            json=original,
        )
        assert created.status_code == 200, created.text

        corrected = client.put(
            f"/attendance/{course_id}/records/2026-10-05",
            headers=lecturer,
            json={
                "class_date": "2026-10-05",
                "records": [
                    {
                        "student_id": alice_id,
                        "status": "absent",
                    },
                    {
                        "student_id": bob_id,
                        "status": "present",
                    },
                ],
            },
        )

        assert corrected.status_code == 200, corrected.text
        assert corrected.json()["updated"] == 2

        summary = client.get(
            f"/attendance/{course_id}",
            headers=lecturer,
        )

        assert summary.status_code == 200

        students = {
            student["student_id"]: student
            for student in summary.json()["students"]
        }

        assert students[alice_id]["attended"] == 0
        assert students[bob_id]["attended"] == 1

    finally:
        app.dependency_overrides.clear()
        db.close()
        engine.dispose()


def test_attendance_rejects_unscheduled_date():
    client, db, engine = make_client()

    try:
        lecturer = _register(
            client,
            email="unscheduled@test.edu",
            name="Schedule Lecturer",
        )

        course_id = _create_course(client, lecturer)

        student_id = _add_student(
            client,
            lecturer,
            course_id,
            "24BCS501",
            "Student",
        )

        _create_monday_schedule(
            client,
            lecturer,
            course_id,
        )

        # Tuesday, not Monday.
        response = client.post(
            f"/attendance/{course_id}/records",
            headers=lecturer,
            json={
                "class_date": "2026-10-06",
                "records": [
                    {
                        "student_id": student_id,
                        "status": "present",
                    }
                ],
            },
        )

        assert response.status_code == 422
        assert "not an active scheduled class date" in response.text

    finally:
        app.dependency_overrides.clear()
        db.close()
        engine.dispose()


def test_attendance_rejects_future_date():
    client, db, engine = make_client()

    try:
        lecturer = _register(
            client,
            email="future@test.edu",
            name="Future Lecturer",
        )

        course_id = _create_course(client, lecturer)

        student_id = _add_student(
            client,
            lecturer,
            course_id,
            "24BCS601",
            "Student",
        )

        response = client.post(
            f"/attendance/{course_id}/records",
            headers=lecturer,
            json={
                "class_date": "2099-01-01",
                "records": [
                    {
                        "student_id": student_id,
                        "status": "present",
                    }
                ],
            },
        )

        assert response.status_code == 422
        assert "future date" in response.text

    finally:
        app.dependency_overrides.clear()
        db.close()
        engine.dispose()


def test_attendance_isolation_between_lecturers():
    client, db, engine = make_client()

    try:
        lecturer_a = _register(
            client,
            email="attendance-a@test.edu",
            name="Lecturer A",
        )
        lecturer_b = _register(
            client,
            email="attendance-b@test.edu",
            name="Lecturer B",
        )

        course_a = _create_course(
            client,
            lecturer_a,
            code="ATT-A",
        )

        student_a = _add_student(
            client,
            lecturer_a,
            course_a,
            "24BCS701",
            "Student A",
        )

        _create_monday_schedule(
            client,
            lecturer_a,
            course_a,
        )

        recorded = client.post(
            f"/attendance/{course_a}/records",
            headers=lecturer_a,
            json={
                "class_date": "2026-10-05",
                "records": [
                    {
                        "student_id": student_a,
                        "status": "present",
                    }
                ],
            },
        )
        assert recorded.status_code == 200, recorded.text

        assert client.get(
            f"/attendance/{course_a}",
            headers=lecturer_b,
        ).status_code == 404

        assert client.post(
            f"/attendance/{course_a}/records",
            headers=lecturer_b,
            json={
                "class_date": "2026-10-05",
                "records": [
                    {
                        "student_id": student_a,
                        "status": "absent",
                    }
                ],
            },
        ).status_code == 404

    finally:
        app.dependency_overrides.clear()
        db.close()
        engine.dispose()