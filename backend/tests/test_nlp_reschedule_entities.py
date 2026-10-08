"""Regression tests for temporal entity roles in reschedule requests."""

from ai.nlp.pipeline import (
    _apply_reschedule_temporal_roles,
    _extract_structured_entities,
)
from app.services.temporal_resolver import resolve_temporal_entities


def test_reschedule_assigns_second_date_and_lone_destination_time():
    text = "reschedule my DBMS class Tuesday to Friday 11 PM"

    entities = _extract_structured_entities(text)
    entities = _apply_reschedule_temporal_roles(
        text=text,
        entities=entities,
        intent="reschedule_class",
    )

    labels = {
        (entity["text"].lower(), entity["label"])
        for entity in entities
    }

    assert ("tuesday", "DATE") in labels
    assert ("friday", "NEW_DATE") in labels
    assert ("11 PM".lower(), "NEW_TIME") in labels

    resolved = resolve_temporal_entities(
        {
            "intent": "reschedule_class",
            "entities": entities,
        },
        reference_date=None,
    )

    assert resolved["date"] is not None
    assert resolved["new_date"] is not None
    assert resolved["time"] is None
    assert resolved["new_time"] == "23:00"


def test_reschedule_keeps_original_time_when_it_precedes_target_date():
    text = "reschedule the 9 AM DBMS class to Friday"

    entities = _extract_structured_entities(text)
    entities = _apply_reschedule_temporal_roles(
        text=text,
        entities=entities,
        intent="reschedule_class",
    )

    labels = {
        (entity["text"].lower(), entity["label"])
        for entity in entities
    }

    assert ("9 am", "TIME") in labels
    assert ("friday", "DATE") in labels


def test_non_reschedule_temporal_roles_are_unchanged():
    text = "cancel my DBMS class Friday at 11 PM"

    entities = _extract_structured_entities(text)
    entities = _apply_reschedule_temporal_roles(
        text=text,
        entities=entities,
        intent="cancel_class",
    )

    labels = {
        (entity["text"].lower(), entity["label"])
        for entity in entities
    }

    assert ("friday", "DATE") in labels
    assert ("11 pm", "TIME") in labels
