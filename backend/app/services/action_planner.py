from __future__ import annotations


def plan_action(
    intent: str | None,
    resolved_entities: dict,
) -> dict | None:
    """
    Convert an understood intent + resolved entities
    into a safe proposed action.

    IMPORTANT:
    This function NEVER changes the database.
    It only creates an action proposal.
    """

    if intent == "cancel_class":
        return plan_cancel_action(
            resolved_entities
        )

    if intent == "reschedule_class":
        return plan_reschedule_action(
            resolved_entities
        )

    if intent == "notify_batch":
        return plan_notify_action(
            resolved_entities
        )

    if intent == "log_lecture":
        return plan_log_lecture_action(
            resolved_entities
        )

    return None


def plan_cancel_action(
    entities: dict,
) -> dict:
    course_id = entities.get(
        "course_id"
    )

    date = entities.get(
        "resolved_date"
    )

    time = entities.get(
        "resolved_time"
    )

    batch = entities.get(
        "batch_text"
    )

    missing = []

    if not course_id:
        missing.append("course")

    if not date:
        missing.append("date")

    if missing:
        return {
            "action": "cancel_class",
            "status": "needs_clarification",
            "requires_confirmation": True,
            "missing": missing,
            "proposal": None,
        }

    return {
        "action": "cancel_class",
        "status": "proposed",
        "requires_confirmation": True,
        "missing": [],
        "proposal": {
            "course_id": course_id,
            "date": date,
            "time": time,
            "batch": batch,
        },
    }


def plan_reschedule_action(
    entities: dict,
) -> dict:
    course_id = entities.get(
        "course_id"
    )

    date = entities.get(
        "resolved_date"
    )

    new_date = entities.get(
        "resolved_new_date"
    )

    time = entities.get(
        "resolved_time"
    )

    new_time = entities.get(
        "resolved_new_time"
    )

    missing = []

    if not course_id:
        missing.append("course")

    if not date:
        missing.append("date")

    if not new_date and not new_time:
        missing.append(
            "new date or new time"
        )

    if missing:
        return {
            "action": "reschedule_class",
            "status": "needs_clarification",
            "requires_confirmation": True,
            "missing": missing,
            "proposal": None,
        }

    return {
        "action": "reschedule_class",
        "status": "proposed",
        "requires_confirmation": True,
        "missing": [],
        "proposal": {
            "course_id": course_id,
            "date": date,
            "time": time,
            "new_date": new_date,
            "new_time": new_time,
        },
    }


def plan_notify_action(
    entities: dict,
) -> dict:
    batch = entities.get(
        "batch_text"
    )

    course_id = entities.get(
        "course_id"
    )

    date = entities.get(
        "resolved_date"
    )

    missing = []

    if not batch:
        missing.append("batch")

    if not course_id:
        missing.append("course")

    if missing:
        return {
            "action": "notify_batch",
            "status": "needs_clarification",
            "requires_confirmation": True,
            "missing": missing,
            "proposal": None,
        }

    return {
        "action": "notify_batch",
        "status": "proposed",
        "requires_confirmation": True,
        "missing": [],
        "proposal": {
            "batch": batch,
            "course_id": course_id,
            "date": date,
        },
    }


def plan_log_lecture_action(
    entities: dict,
) -> dict:
    course_id = entities.get(
        "course_id"
    )

    topic = entities.get(
        "topic_text"
    )

    date = entities.get(
        "resolved_date"
    )

    duration = entities.get(
        "duration_text"
    )

    missing = []

    if not course_id:
        missing.append("course")

    if not topic:
        missing.append("topic")

    if missing:
        return {
            "action": "log_lecture",
            "status": "needs_clarification",
            "requires_confirmation": True,
            "missing": missing,
            "proposal": None,
        }

    return {
        "action": "log_lecture",
        "status": "proposed",
        "requires_confirmation": True,
        "missing": [],
        "proposal": {
            "course_id": course_id,
            "topic": topic,
            "date": date,
            "duration": duration,
        },
    }