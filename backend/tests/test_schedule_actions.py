"""Tests for confirmed schedule actions and class notifications."""

from datetime import date

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import models  # noqa: F401
from app.database.db import Base
from app.services.action_executor import execute_action
from app.services.action_planner import plan_action
from seed.seed_demo import populate


def make_db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, autoflush=False)()
    populate(session, today=date(2026, 10, 8))
    return session


def test_cancel_action_plans_from_real_schedule():
    db = make_db()
    try:
        plan = plan_action(
            "cancel_class",
            {
                "lecturer_id": "lecturer_001",
                "course_id": "dbms",
                "resolved_date": "2026-10-09",
                "resolved_time": None,
                "batch_text": None,
            },
            db=db,
        )

        assert plan["status"] == "proposed"
        assert plan["proposal"]["item_id"] == "dbms-fri"
        assert plan["proposal"]["notify_students"] is True
    finally:
        db.close()


def test_cancel_executes_and_reports_missing_email_provider(monkeypatch):
    monkeypatch.delenv("RESEND_API_KEY", raising=False)
    monkeypatch.delenv("RESEND_FROM_EMAIL", raising=False)

    db = make_db()
    try:
        plan = {
            "action": "cancel_class",
            "status": "proposed",
            "requires_confirmation": True,
            "proposal": {
                "course_id": "dbms",
                "item_id": "dbms-fri",
                "date": "2026-10-09",
                "notify_students": True,
            },
        }

        result = execute_action(
            plan,
            db=db,
            lecturer_id="lecturer_001",
        )

        assert result["status"] == "executed"
        assert result["change"]["status"] == "cancelled"
        assert result["notification"]["status"] == "not_configured"
    finally:
        db.close()


def test_reschedule_executes_without_mail_provider(monkeypatch):
    monkeypatch.delenv("RESEND_API_KEY", raising=False)
    monkeypatch.delenv("RESEND_FROM_EMAIL", raising=False)

    db = make_db()
    try:
        plan = {
            "action": "reschedule_class",
            "status": "proposed",
            "requires_confirmation": True,
            "proposal": {
                "course_id": "dbms",
                "item_id": "dbms-fri",
                "date": "2026-10-09",
                "new_date": "2026-10-12",
                "new_time": "14:00",
                "notify_students": True,
            },
        }

        result = execute_action(
            plan,
            db=db,
            lecturer_id="lecturer_001",
        )

        assert result["status"] == "executed"
        assert result["change"]["status"] == "rescheduled"
        assert result["change"]["new_date"] == "2026-10-12"
        assert result["change"]["new_start_time"] == "14:00"
        assert result["notification"]["status"] == "not_configured"
    finally:
        db.close()
