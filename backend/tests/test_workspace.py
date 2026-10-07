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


def test_syllabus_crud_reorder_and_isolation():
    client, db, engine = make_client()

    try:
        lecturer_a = _register(
            client,
            email="syllabus-a@university.edu",
            name="Syllabus A",
        )
        lecturer_b = _register(
            client,
            email="syllabus-b@university.edu",
            name="Syllabus B",
        )

        created_course = client.post(
            "/courses/",
            headers=lecturer_a,
            json={
                "code": "CSE-SYL-1",
                "name": "Software Architecture",
                "short_name": "SWA",
                "section": "CSE-A",
                "start_date": "2026-10-01",
                "planned_end_date": "2026-12-01",
            },
        )
        assert created_course.status_code == 201, created_course.text
        course_id = created_course.json()["id"]

        first_unit = client.post(
            f"/courses/{course_id}/units",
            headers=lecturer_a,
            json={"name": "Foundations"},
        )
        assert first_unit.status_code == 201, first_unit.text
        unit_id = first_unit.json()["id"]
        assert unit_id.startswith("unit_")

        second_unit = client.post(
            f"/courses/{course_id}/units",
            headers=lecturer_a,
            json={"name": "Advanced Topics"},
        )
        assert second_unit.status_code == 201, second_unit.text
        second_unit_id = second_unit.json()["id"]

        topic_a = client.post(
            f"/courses/{course_id}/units/{unit_id}/topics",
            headers=lecturer_a,
            json={
                "name": "Architecture Styles",
                "planned_date": "2026-10-10",
            },
        )
        assert topic_a.status_code == 201, topic_a.text
        topic_a_body = topic_a.json()
        topic_a_id = topic_a_body["id"]
        assert topic_a_body["planned_date"] == "2026-10-10"
        assert topic_a_body["completed"] is False

        topic_b = client.post(
            f"/courses/{course_id}/units/{unit_id}/topics",
            headers=lecturer_a,
            json={"name": "Design Principles"},
        )
        assert topic_b.status_code == 201, topic_b.text
        topic_b_id = topic_b.json()["id"]

        listed = client.get(
            f"/courses/{course_id}",
            headers=lecturer_a,
        )
        assert listed.status_code == 200
        body = listed.json()
        assert [unit["name"] for unit in body["syllabus"]] == [
            "Foundations",
            "Advanced Topics",
        ]
        assert [topic["name"] for topic in body["syllabus"][0]["topics"]] == [
            "Architecture Styles",
            "Design Principles",
        ]

        updated_topic = client.patch(
            f"/courses/{course_id}/units/{unit_id}/topics/{topic_a_id}",
            headers=lecturer_a,
            json={
                "name": "Architectural Styles",
                "planned_date": "2026-10-12",
            },
        )
        assert updated_topic.status_code == 200, updated_topic.text
        assert updated_topic.json()["id"] == topic_a_id
        assert updated_topic.json()["name"] == "Architectural Styles"
        assert updated_topic.json()["planned_date"] == "2026-10-12"

        updated_unit = client.patch(
            f"/courses/{course_id}/units/{unit_id}",
            headers=lecturer_a,
            json={"name": "Core Foundations"},
        )
        assert updated_unit.status_code == 200, updated_unit.text
        assert updated_unit.json()["id"] == unit_id
        assert updated_unit.json()["name"] == "Core Foundations"

        reversed_topics = client.put(
            f"/courses/{course_id}/units/{unit_id}/topics/reorder",
            headers=lecturer_a,
            json={"ids": [topic_b_id, topic_a_id]},
        )
        assert reversed_topics.status_code == 200, reversed_topics.text
        assert [topic["id"] for topic in reversed_topics.json()] == [
            topic_b_id,
            topic_a_id,
        ]

        reversed_units = client.put(
            f"/courses/{course_id}/units/reorder",
            headers=lecturer_a,
            json={"ids": [second_unit_id, unit_id]},
        )
        assert reversed_units.status_code == 200, reversed_units.text
        assert [unit["id"] for unit in reversed_units.json()] == [
            second_unit_id,
            unit_id,
        ]

        invalid_reorder = client.put(
            f"/courses/{course_id}/units/reorder",
            headers=lecturer_a,
            json={"ids": [unit_id, unit_id]},
        )
        assert invalid_reorder.status_code == 422

        # Lecturer B must not be able to read or mutate A's syllabus.
        assert client.post(
            f"/courses/{course_id}/units",
            headers=lecturer_b,
            json={"name": "Unauthorized Unit"},
        ).status_code == 404

        assert client.patch(
            f"/courses/{course_id}/units/{unit_id}",
            headers=lecturer_b,
            json={"name": "Hijacked"},
        ).status_code == 404

        assert client.patch(
            f"/courses/{course_id}/units/{unit_id}/topics/{topic_a_id}",
            headers=lecturer_b,
            json={"name": "Hijacked Topic"},
        ).status_code == 404

        assert client.delete(
            f"/courses/{course_id}/units/{unit_id}/topics/{topic_a_id}",
            headers=lecturer_b,
        ).status_code == 404

        deleted_topic = client.delete(
            f"/courses/{course_id}/units/{unit_id}/topics/{topic_a_id}",
            headers=lecturer_a,
        )
        assert deleted_topic.status_code == 204

        remaining_topic = client.get(
            f"/courses/{course_id}",
            headers=lecturer_a,
        ).json()["syllabus"][1]["topics"]
        assert [topic["id"] for topic in remaining_topic] == [
            topic_b_id
        ]

        deleted_unit = client.delete(
            f"/courses/{course_id}/units/{second_unit_id}",
            headers=lecturer_a,
        )
        assert deleted_unit.status_code == 204

        final_syllabus = client.get(
            f"/courses/{course_id}",
            headers=lecturer_a,
        ).json()["syllabus"]
        assert [unit["id"] for unit in final_syllabus] == [unit_id]
        assert final_syllabus[0]["name"] == "Core Foundations"
    finally:
        app.dependency_overrides.clear()
        db.close()
        engine.dispose()


def test_timetable_template_crud_and_isolation():
    client, db, engine = make_client()

    try:
        lecturer_a = _register(
            client,
            email="schedule-a@university.edu",
            name="Schedule A",
        )
        lecturer_b = _register(
            client,
            email="schedule-b@university.edu",
            name="Schedule B",
        )

        course = client.post(
            "/courses/",
            headers=lecturer_a,
            json={
                "code": "CSE-TT-1",
                "name": "Computer Networks",
                "short_name": "CN",
                "section": "CSE-A",
                "start_date": "2026-10-01",
                "planned_end_date": "2026-12-01",
            },
        )
        assert course.status_code == 201, course.text
        course_id = course.json()["id"]

        created = client.post(
            "/schedule/templates",
            headers=lecturer_a,
            json={
                "weekday": 0,
                "start_time": "09:00",
                "end_time": "10:00",
                "room": "LT-1",
                "course_id": course_id,
            },
        )
        assert created.status_code == 201, created.text
        body = created.json()
        item_id = body["id"]
        assert item_id.startswith("sch_")
        assert body["subject"] == "CN"
        assert body["code"] == "CSE-TT-1"
        assert body["batch"] == "CSE-A"
        assert body["weekday"] == 0
        assert body["start_time"] == "09:00"
        assert body["end_time"] == "10:00"
        assert body["room"] == "LT-1"
        assert body["item_type"] == "class"
        assert body["lecturer_id"] == lecturer_a["Authorization"] is not None

        listed = client.get(
            "/schedule/templates",
            headers=lecturer_a,
        )
        assert listed.status_code == 200
        assert [item["id"] for item in listed.json()] == [item_id]

        assert client.get(
            "/schedule/templates",
            headers=lecturer_b,
        ).json() == []

        detail = client.get(
            f"/schedule/templates/{item_id}",
            headers=lecturer_a,
        )
        assert detail.status_code == 200
        assert detail.json()["id"] == item_id

        overlap = client.post(
            "/schedule/templates",
            headers=lecturer_a,
            json={
                "weekday": 0,
                "start_time": "09:30",
                "end_time": "10:30",
                "room": "LT-2",
                "course_id": course_id,
            },
        )
        assert overlap.status_code == 422

        updated = client.patch(
            f"/schedule/templates/{item_id}",
            headers=lecturer_a,
            json={
                "weekday": 2,
                "start_time": "11:00",
                "end_time": "12:30",
                "room": "LAB-2",
                "batch": "CSE-B",
            },
        )
        assert updated.status_code == 200, updated.text
        updated_body = updated.json()
        assert updated_body["id"] == item_id
        assert updated_body["weekday"] == 2
        assert updated_body["start_time"] == "11:00"
        assert updated_body["end_time"] == "12:30"
        assert updated_body["room"] == "LAB-2"
        assert updated_body["batch"] == "CSE-B"

        assert client.patch(
            f"/schedule/templates/{item_id}",
            headers=lecturer_b,
            json={"room": "HIJACKED"},
        ).status_code == 404

        assert client.get(
            f"/schedule/templates/{item_id}",
            headers=lecturer_b,
        ).status_code == 404

        assert client.delete(
            f"/schedule/templates/{item_id}",
            headers=lecturer_b,
        ).status_code == 404

        deleted = client.delete(
            f"/schedule/templates/{item_id}",
            headers=lecturer_a,
        )
        assert deleted.status_code == 204

        assert client.get(
            f"/schedule/templates/{item_id}",
            headers=lecturer_a,
        ).status_code == 404
        assert client.get(
            "/schedule/templates",
            headers=lecturer_a,
        ).json() == []
    finally:
        app.dependency_overrides.clear()
        db.close()
        engine.dispose()
