from __future__ import annotations

from sqlalchemy.orm import Session

from ai.syllabus.mapper import map_and_format
SUPPORTED_EXECUTABLE_ACTIONS = {
    "log_lecture",
}

def plan_action(
    intent: str | None,
    resolved_entities: dict,
    db: Session | None = None,
) -> dict | None:
    """
    Convert an understood intent + resolved entities
    into an action proposal.

    The planner distinguishes between:
    - executable actions
    - understood but currently unsupported actions

    IMPORTANT:
    This function never changes the database.
    """

    action_by_intent = {
        "cancel_class": "cancel_class",
        "reschedule_class": "reschedule_class",
        "notify_batch": "notify_batch",
        "log_lecture": "log_lecture",
    }

    action = action_by_intent.get(intent)

    if action is None:
        return None

    # -----------------------------------------
    # CAPABILITY GATE
    # -----------------------------------------
    #
    # Do not create a confirmation proposal for
    # an action that the executor cannot perform.
    # -----------------------------------------

    if action not in SUPPORTED_EXECUTABLE_ACTIONS:
        return {
            "action": action,
            "status": "unsupported",
            "requires_confirmation": False,
            "missing": [],
            "proposal": None,
        }

    if action == "log_lecture":
        return plan_log_lecture_action(
            resolved_entities,
            db=db,
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
    db: Session | None = None,
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

    # -------------------------------------------------
    # LECTURE → SYLLABUS MAPPING
    # -------------------------------------------------

    syllabus_matches = []
    mapping_status = "not_run"
    mapping_error = None

    if db is not None:
        try:
            mapping_result = map_and_format(
                db=db,
                course_id=course_id,
                lecture_description=topic,
                top_k=5,
            )

            syllabus_matches = mapping_result.get(
                "matches",
                []
            )

            if syllabus_matches:
                mapping_status = "matched"
            else:
                mapping_status = "no_match"

        except Exception as exc:
            # Mapping should not prevent the lecturer
            # from preparing a lecture record.
            mapping_status = "error"
            mapping_error = str(exc)

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

            # New AI intelligence information
            "syllabus_matches": syllabus_matches,
            "mapping_status": mapping_status,
            "mapping_error": mapping_error,
        },
    }