"""Tests for real lecturer onboarding.

These tests intentionally use an empty in-memory database rather than the
demo seed so a newly registered lecturer's workspace starts empty.
"""
from __future__ import annotations

import os

os.environ.setdefault("SECRET_KEY", "workspace-test-secret")

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.db import Base, get_db
from app.main import app


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
        expire_on_commit=False,
    )
    db = session_local()

    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    return client, db, engine


def test_register_creates_lecturer_and_empty_workspace():
    client, db, engine = make_client()

    try:
        response = client.post(
            "/auth/register",
            json={
                "name": "Dr. Test User",
                "email": "test.user@university.edu",
                "password": "strong-pass-123",
                "department": "Computer Science & Engineering",
                "title": "Assistant Professor",
            },
        )

        assert response.status_code == 201
        payload = response.json()
        assert payload["token_type"] == "bearer"
        assert payload["access_token"]

        headers = {
            "Authorization": f"Bearer {payload['access_token']}"
        }

        me = client.get("/auth/me", headers=headers)
        assert me.status_code == 200
        me_body = me.json()
        assert me_body["email"] == "test.user@university.edu"
        assert me_body["name"] == "Dr. Test User"
        assert me_body["title"] == "Assistant Professor"
        assert me_body["department"] == "Computer Science & Engineering"
        assert me_body["lecturer_id"].startswith("lec_")

        courses = client.get("/courses/", headers=headers)
        assert courses.status_code == 200
        assert courses.json() == []

        schedule = client.get("/schedule/", headers=headers)
        assert schedule.status_code == 200
        assert schedule.json() == []
    finally:
        app.dependency_overrides.clear()
        db.close()
        engine.dispose()


def test_register_rejects_duplicate_email():
    client, db, engine = make_client()

    try:
        body = {
            "name": "First Lecturer",
            "email": "duplicate@university.edu",
            "password": "strong-pass-123",
            "department": "Computer Science",
            "title": "Lecturer",
        }

        first = client.post("/auth/register", json=body)
        assert first.status_code == 201

        second = client.post(
            "/auth/register",
            json={
                **body,
                "name": "Second Lecturer",
            },
        )
        assert second.status_code == 409
    finally:
        app.dependency_overrides.clear()
        db.close()
        engine.dispose()


def test_register_then_login():
    client, db, engine = make_client()

    try:
        register = client.post(
            "/auth/register",
            json={
                "name": "Login Lecturer",
                "email": "login@university.edu",
                "password": "strong-pass-123",
                "department": "Computer Science",
                "title": "Professor",
            },
        )
        assert register.status_code == 201

        login = client.post(
            "/auth/login",
            json={
                "email": "login@university.edu",
                "password": "strong-pass-123",
            },
        )
        assert login.status_code == 200
        assert login.json()["access_token"]
    finally:
        app.dependency_overrides.clear()
        db.close()
        engine.dispose()


def _register(client, *, email: str, name: str = "Test Lecturer") -> dict:
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


def test_course_crud_and_lecturer_isolation():
    client, db, engine = make_client()

    try:
        lecturer_a = _register(
            client,
            email="course-a@university.edu",
            name="Lecturer A",
        )
        lecturer_b = _register(
            client,
            email="course-b@university.edu",
            name="Lecturer B",
        )

        created = client.post(
            "/courses/",
            headers=lecturer_a,
            json={
                "code": "DBMS-501",
                "name": "Database Management Systems",
                "short_name": "DBMS",
                "section": "CSE-A",
                "start_date": "2026-10-01",
                "planned_end_date": "2026-12-01",
            },
        )
        assert created.status_code == 201, created.text

        course = created.json()
        course_id = course["id"]
        assert course_id.startswith("crs_")
        assert course["code"] == "DBMS-501"
        assert course["department"] == "Computer Science"

        listed = client.get("/courses/", headers=lecturer_a)
        assert listed.status_code == 200
        assert [item["id"] for item in listed.json()] == [course_id]

        detail = client.get(
            f"/courses/{course_id}",
            headers=lecturer_a,
        )
        assert detail.status_code == 200
        assert detail.json()["start_date"] == "2026-10-01"
        assert detail.json()["planned_end_date"] == "2026-12-01"

        updated = client.patch(
            f"/courses/{course_id}",
            headers=lecturer_a,
            json={
                "name": "Advanced Database Systems",
                "section": "CSE-B",
                "planned_end_date": "2026-12-10",
            },
        )
        assert updated.status_code == 200, updated.text
        assert updated.json()["name"] == "Advanced Database Systems"
        assert updated.json()["section"] == "CSE-B"
        assert updated.json()["planned_end_date"] == "2026-12-10"

        duplicate = client.post(
            "/courses/",
            headers=lecturer_a,
            json={
                "code": "DBMS-501",
                "name": "Another Course",
                "short_name": "OTHER",
                "section": "CSE-B",
                "start_date": "2026-10-01",
                "planned_end_date": "2026-12-01",
            },
        )
        assert duplicate.status_code == 409

        assert client.get(
            f"/courses/{course_id}",
            headers=lecturer_b,
        ).status_code == 404

        assert client.patch(
            f"/courses/{course_id}",
            headers=lecturer_b,
            json={"name": "Hijacked"},
        ).status_code == 404

        assert client.delete(
            f"/courses/{course_id}",
            headers=lecturer_b,
        ).status_code == 404

        deleted = client.delete(
            f"/courses/{course_id}",
            headers=lecturer_a,
        )
        assert deleted.status_code == 204

        assert client.get(
            f"/courses/{course_id}",
            headers=lecturer_a,
        ).status_code == 404
        assert client.get("/courses/", headers=lecturer_a).json() == []
    finally:
        app.dependency_overrides.clear()
        db.close()
        engine.dispose()
