"""Real HTTP integration tests for the FastAPI contracts.

All tests use TestClient against an isolated in-memory SQLite database.
The application clock is fixed so date-relative behavior is deterministic.
"""
from __future__ import annotations

import os
from datetime import date

os.environ.setdefault("SECRET_KEY", "integration-test-secret")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app import models  # noqa: F401
from app.database.db import Base, get_db
from app.main import app
from app.models.academic import User
from app.services.auth_service import hash_password
from seed.seed_demo import populate

TODAY = date(2026, 10, 1)


@pytest.fixture()
def http_client(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "integration-test-secret")
    monkeypatch.setenv("PROFPILOT_FIXED_NOW", "2026-10-03T09:00:00")

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    db = SessionLocal()
    populate(db, today=TODAY)

    db.add_all([
        User(
            email="sharma@university.edu",
            password_hash=hash_password("sharma-pass"),
            lecturer_id="lecturer_001",
        ),
        User(
            email="verma@university.edu",
            password_hash=hash_password("verma-pass"),
            lecturer_id="lecturer_002",
        ),
    ])
    db.commit()

    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client, db
    app.dependency_overrides.clear()
    db.close()
    engine.dispose()


def login(client: TestClient, email: str, password: str) -> dict:
    response = client.post("/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def full_roster(db: Session, course_id: str, status: str = "present") -> list[dict]:
    rows = db.execute(
        __import__("sqlalchemy").text(
            "SELECT student_id FROM enrollments WHERE course_id=:course_id ORDER BY student_id"
        ),
        {"course_id": course_id},
    ).all()
    return [{"student_id": row[0], "status": status} for row in rows]


# 1. Authentication

def test_auth_login_and_me(http_client):
    client, _ = http_client
    headers = login(client, "sharma@university.edu", "sharma-pass")
    response = client.get("/auth/me", headers=headers)
    assert response.status_code == 200
    assert response.json()["lecturer_id"] == "lecturer_001"
    assert client.get("/auth/me").status_code == 401


# 2. Attendance endpoints + incomplete roster + date validation + correction

def test_attendance_http_contract_and_correction(http_client):
    client, db = http_client
    headers = login(client, "sharma@university.edu", "sharma-pass")

    response = client.get("/attendance/dbms", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["threshold_pct"] == 75
    assert any(s["roll_no"] == "24BCS047" and not s["flagged"] for s in body["students"])

    roster = full_roster(db, "dbms")
    incomplete = client.post(
        "/attendance/dbms/records",
        headers=headers,
        json={"class_date": "2026-10-02", "records": roster[:-1]},
    )
    assert incomplete.status_code == 422

    invalid_date = client.post(
        "/attendance/dbms/records",
        headers=headers,
        json={"class_date": "2026-10-01", "records": roster},
    )
    assert invalid_date.status_code == 422
    assert "scheduled class date" in invalid_date.json()["detail"]

    created = client.post(
        "/attendance/dbms/records",
        headers=headers,
        json={"class_date": "2026-10-02", "records": roster},
    )
    assert created.status_code == 200
    assert created.json()["created"] == len(roster)

    duplicate = client.post(
        "/attendance/dbms/records",
        headers=headers,
        json={"class_date": "2026-10-02", "records": roster},
    )
    assert duplicate.status_code == 422

    corrected_roster = list(roster)
    corrected_roster[0] = {"student_id": corrected_roster[0]["student_id"], "status": "absent"}
    corrected = client.put(
        "/attendance/dbms/records/2026-10-02",
        headers=headers,
        json={"class_date": "2026-10-02", "records": corrected_roster},
    )
    assert corrected.status_code == 200
    assert corrected.json()["updated"] == len(roster)


# 3. Schedule endpoints + next/cancel/reschedule

def test_schedule_http_contract_and_changes(http_client, monkeypatch):
    monkeypatch.setenv("PROFPILOT_FIXED_NOW", "2026-10-01T09:00:00")
    client, _ = http_client
    headers = login(client, "sharma@university.edu", "sharma-pass")

    today = client.get("/schedule/?date=2026-10-01", headers=headers)
    assert today.status_code == 200
    assert [x["id"] for x in today.json()] == ["ai-thu"]

    upcoming = client.get(
        "/schedule/upcoming?days=5&at=2026-10-01T09:00:00",
        headers=headers,
    )
    assert upcoming.status_code == 200
    dates = [x["date"] for x in upcoming.json()]
    assert dates == sorted(dates)

    nxt = client.get("/schedule/next?at=2026-10-01T09:00:00", headers=headers)
    assert nxt.status_code == 200
    assert nxt.json()["id"] == "ai-thu"

    cancelled = client.post(
        "/schedule/dbms-fri/cancel",
        headers=headers,
        json={"on_date": "2026-10-02", "reason": "Conference"},
    )
    assert cancelled.status_code == 200
    assert all(item["id"] != "dbms-fri" for item in client.get("/schedule/?date=2026-10-02", headers=headers).json())

    rescheduled = client.post(
        "/schedule/ai-thu/reschedule",
        headers=headers,
        json={
            "on_date": "2026-10-01",
            "new_date": "2026-10-08",
            "new_start_time": "12:00",
            "new_end_time": "13:00",
            "reason": "Department event",
        },
    )
    assert rescheduled.status_code == 200
    assert rescheduled.json()["status"] == "rescheduled"
    moved = client.get("/schedule/?date=2026-10-08", headers=headers).json()
    assert moved[0]["status"] == "rescheduled"
    assert moved[0]["original_date"] == "2026-10-01"


# 4. Courses and lecturer ownership

def test_courses_are_lecturer_scoped(http_client):
    client, _ = http_client
    h1 = login(client, "sharma@university.edu", "sharma-pass")
    h2 = login(client, "verma@university.edu", "verma-pass")

    c1 = client.get("/courses/", headers=h1)
    assert c1.status_code == 200
    assert {c["id"] for c in c1.json()} == {"dbms", "ai"}
    assert client.get("/courses/os", headers=h1).status_code == 404

    c2 = client.get("/courses/", headers=h2)
    assert {c["id"] for c in c2.json()} == {"os"}


# 5. Memory ownership and course isolation

def test_memory_and_course_ownership(http_client):
    client, _ = http_client
    h1 = login(client, "sharma@university.edu", "sharma-pass")
    h2 = login(client, "verma@university.edu", "verma-pass")

    created = client.post(
        "/memory/events",
        headers=h1,
        json={
            "lecturer_id": "lecturer_001",
            "course_id": "dbms",
            "event_type": "note",
            "title": "DBMS note",
            "summary": "Only Sharma should see this.",
        },
    )
    assert created.status_code == 200

    assert client.get("/memory/lecturer_001", headers=h2).status_code == 403
    assert client.get("/memory/lecturer_001?course_id=dbms", headers=h2).status_code == 403
    assert client.post(
        "/memory/events",
        headers=h2,
        json={
            "lecturer_id": "lecturer_002",
            "course_id": "dbms",
            "event_type": "note",
            "title": "Cross-course attempt",
            "summary": "Should be rejected.",
        },
    ).status_code == 403


# 6. Business scenario: week rollover and lecturer isolation

def test_business_week_rollover_and_two_lecturers(http_client):
    client, _ = http_client
    h1 = login(client, "sharma@university.edu", "sharma-pass")
    h2 = login(client, "verma@university.edu", "verma-pass")

    friday_next = client.get("/schedule/next?at=2026-10-02T10:30:00", headers=h1)
    assert friday_next.json()["id"] == "dbms-mon"
    assert friday_next.json()["date"] == "2026-10-05"

    os_next = client.get("/schedule/next?at=2026-10-02T10:30:00", headers=h2)
    assert os_next.json()["id"] == "os-fri"


# 7. Business scenario: cancellation skips the occurrence

def test_business_cancellation_skips_next_occurrence(http_client, monkeypatch):
    monkeypatch.setenv("PROFPILOT_FIXED_NOW", "2026-10-01T09:00:00")
    client, _ = http_client
    h1 = login(client, "sharma@university.edu", "sharma-pass")
    response = client.post(
        "/schedule/dbms-fri/cancel",
        headers=h1,
        json={"on_date": "2026-10-02"},
    )
    assert response.status_code == 200
    nxt = client.get("/schedule/next?at=2026-10-02T09:00:00", headers=h1)
    assert nxt.json()["id"] == "dbms-mon"


# 8. Business scenario: rescheduling is traceable and becomes the active occurrence

def test_business_reschedule_is_traceable(http_client, monkeypatch):
    monkeypatch.setenv("PROFPILOT_FIXED_NOW", "2026-10-01T09:00:00")
    client, _ = http_client
    h1 = login(client, "sharma@university.edu", "sharma-pass")
    response = client.post(
        "/schedule/dbms-fri/reschedule",
        headers=h1,
        json={
            "on_date": "2026-10-02",
            "new_date": "2026-10-05",
            "new_start_time": "14:00",
            "new_end_time": "15:00",
        },
    )
    assert response.status_code == 200
    moved = client.get("/schedule/?date=2026-10-05", headers=h1).json()
    assert any(x["id"] == "dbms-fri" and x["status"] == "rescheduled" for x in moved)


# 9. Business scenario: attendance threshold edges

def test_business_attendance_threshold_edges():
    from app.services.academic_rules import summarize_attendance

    assert summarize_attendance(7490, 10000).flagged  # 74.90%
    assert summarize_attendance(7499, 10000).flagged  # 74.99%
    assert not summarize_attendance(75, 100).flagged
    assert not summarize_attendance(751, 1000).flagged


def test_ai_query_uses_authenticated_lecturer_scope(http_client):
    client, _ = http_client
    h1 = login(client, "sharma@university.edu", "sharma-pass")
    h2 = login(client, "verma@university.edu", "verma-pass")

    ai = client.post("/ai/query", headers=h1, json={"message": "What is my next class?"})
    assert ai.status_code == 200
    assert ai.json()["data"]["lecturer_id"] == "lecturer_001"

    os_result = client.post("/ai/query", headers=h2, json={"message": "What is my next class?"})
    assert os_result.status_code == 200
    assert os_result.json()["data"]["lecturer_id"] == "lecturer_002"
    assert os_result.json()["data"]["course_id"] == "os"
