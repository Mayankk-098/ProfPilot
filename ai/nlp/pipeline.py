from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

from ai.intent.predict import (
    load_model as load_intent_model,
    predict as predict_intent,
)

from ai.entity.predict import (
    load_model as load_entity_model,
    tokenize,
    token_features,
    reconstruct_entities,
)


# -------------------------------------------------
# PROJECT ROOT
# -------------------------------------------------


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


# -------------------------------------------------
# MODEL LOADING
# -------------------------------------------------


@lru_cache(maxsize=1)
def load_models():
    """
    Load both trained models once and reuse them.

    This prevents joblib model loading on every query.
    """

    intent_model = load_intent_model()
    entity_model = load_entity_model()

    return intent_model, entity_model


# -------------------------------------------------
# STRUCTURED ENTITY PATTERNS
# -------------------------------------------------

PERCENT_PATTERN = re.compile(
    r"\b\d+(?:\.\d+)?\s*(?:%|percent|percentage)\b",
    re.IGNORECASE,
)

DURATION_PATTERN = re.compile(
    r"\b\d+(?:\.\d+)?\s*"
    r"(?:m|min|mins|minute|minutes|"
    r"h|hr|hrs|hour|hours)\b",
    re.IGNORECASE,
)

TIME_PATTERN = re.compile(
    r"\b"
    r"(?:"
    r"\d{1,2}(?::\d{2})?\s*(?:AM|PM)"
    r"|"
    r"\d{1,2}(?::\d{2})?\s*baje"
    r")"
    r"\b",
    re.IGNORECASE,
)

DATE_PATTERN = re.compile(
    r"\b(?:"
    r"today|tomorrow|yesterday|"
    r"aaj|kal|"
    r"monday|tuesday|wednesday|"
    r"thursday|friday|saturday|sunday"
    r")\b",
    re.IGNORECASE,
)

ISO_DATE_PATTERN = re.compile(
    r"\b\d{4}-\d{2}-\d{2}\b"
)


# -------------------------------------------------
# ENTITY HELPERS
# -------------------------------------------------


def _make_entity(
    text: str,
    label: str,
    start: int,
    end: int,
) -> dict:
    return {
        "text": text[start:end],
        "label": label,
        "start": start,
        "end": end,
    }


def _extract_structured_entities(
    text: str,
) -> list[dict]:
    """
    Extract entities whose structure is deterministic.

    These values should not depend entirely on the
    token-level ML classifier.

    Supported:
        THRESHOLD
        DURATION
        TIME
        DATE
    """

    entities = []

    # ---------------------------------------------
    # THRESHOLDS
    # ---------------------------------------------

    for match in PERCENT_PATTERN.finditer(text):
        entities.append(
            _make_entity(
                text=text,
                label="THRESHOLD",
                start=match.start(),
                end=match.end(),
            )
        )

    # ---------------------------------------------
    # DURATIONS
    # ---------------------------------------------

    for match in DURATION_PATTERN.finditer(text):
        entities.append(
            _make_entity(
                text=text,
                label="DURATION",
                start=match.start(),
                end=match.end(),
            )
        )

    # ---------------------------------------------
    # TIMES
    # ---------------------------------------------

    for match in TIME_PATTERN.finditer(text):
        entities.append(
            _make_entity(
                text=text,
                label="TIME",
                start=match.start(),
                end=match.end(),
            )
        )

    # ---------------------------------------------
    # NATURAL-LANGUAGE DATES
    # ---------------------------------------------

    for match in DATE_PATTERN.finditer(text):
        entities.append(
            _make_entity(
                text=text,
                label="DATE",
                start=match.start(),
                end=match.end(),
            )
        )

    # ---------------------------------------------
    # ISO DATES
    # ---------------------------------------------

    for match in ISO_DATE_PATTERN.finditer(text):
        entities.append(
            _make_entity(
                text=text,
                label="DATE",
                start=match.start(),
                end=match.end(),
            )
        )

    return entities


def _ranges_overlap(
    first_start: int,
    first_end: int,
    second_start: int,
    second_end: int,
) -> bool:
    return (
        first_start < second_end
        and first_end > second_start
    )


def _trim_semantic_entities(
    entities: list[dict],
    structured_entities: list[dict],
) -> list[dict]:
    """
    Prevent semantic entities such as COURSE/TOPIC
    from absorbing deterministic entities.

    Example:

        Raw ML result:
            COURSE = "DBMS today"

        Structured result:
            DATE = "today"

        Final:
            COURSE = "DBMS"
            DATE   = "today"
    """

    semantic_labels = {
        "COURSE",
        "TOPIC",
        "BATCH",
        "ROOM",
    }

    result = []

    for entity in entities:
        label = entity.get("label")

        if label not in semantic_labels:
            continue

        start = int(entity["start"])
        end = int(entity["end"])

        overlapping = [
            structured
            for structured in structured_entities
            if _ranges_overlap(
                start,
                end,
                structured["start"],
                structured["end"],
            )
        ]

        if overlapping:
            # Prefer trimming the semantic span around
            # structured entities.
            for structured in sorted(
                overlapping,
                key=lambda item: (
                    item["start"],
                    item["end"],
                ),
            ):
                structured_start = structured[
                    "start"
                ]
                structured_end = structured[
                    "end"
                ]

                if (
                    structured_start > start
                    and structured_start < end
                ):
                    end = structured_start

                elif (
                    structured_end > start
                    and structured_end < end
                ):
                    start = structured_end

            if start >= end:
                continue

            entity = {
                **entity,
                "text": entity.get(
                    "text",
                    "",
                ),
            }

            # Recover the exact text from the
            # original query after trimming.
            #
            # We cannot access the original string
            # here, so use the original entity text
            # only when no trimming occurred.
            #
            # Reconstructed below by the caller.
            entity["_trimmed_start"] = start
            entity["_trimmed_end"] = end

        result.append(entity)

    return result


def _deduplicate_entities(
    entities: list[dict],
) -> list[dict]:
    """
    Remove exact duplicate entities.
    """

    seen = set()
    result = []

    for entity in entities:
        key = (
            entity.get("label"),
            entity.get("start"),
            entity.get("end"),
            entity.get("text"),
        )

        if key in seen:
            continue

        seen.add(key)
        result.append(entity)

    return result


def _apply_reschedule_temporal_roles(
    text: str,
    entities: list[dict],
    intent: str | None,
) -> list[dict]:
    """
    Assign original-vs-target roles to deterministic temporal
    entities for reschedule requests.

    The deterministic extractor intentionally emits weekday names
    as DATE and clock times as TIME. For reschedule_class:
        - first date remains DATE; later dates become NEW_DATE
        - first time remains TIME; later times become NEW_TIME
        - a lone time is NEW_TIME when it is clearly introduced as
          the destination or appears after a target date
    """

    if intent != "reschedule_class":
        return entities

    result = [dict(entity) for entity in entities]

    dates = [
        entity
        for entity in result
        if entity.get("label") == "DATE"
    ]

    if len(dates) >= 2:
        for entity in dates[1:]:
            entity["label"] = "NEW_DATE"

    times = [
        entity
        for entity in result
        if entity.get("label") == "TIME"
    ]

    if len(times) >= 2:
        for entity in times[1:]:
            entity["label"] = "NEW_TIME"

    elif len(times) == 1:
        time_entity = times[0]
        time_start = int(time_entity["start"])

        # A single time is normally the destination when introduced
        # by a target cue such as "to 11 PM" or "for 11 PM".
        prefix = text[max(0, time_start - 16):time_start]
        target_cue = re.search(
            r"\b(?:to|for|at|until|around)\s*$",
            prefix,
            flags=re.IGNORECASE,
        )

        # In phrases such as "Tuesday to Friday 11 PM", the only
        # clock time occurs after the target date, so it is a target
        # time even without an explicit "at" before it.
        target_date_positions = [
            int(entity["end"])
            for entity in result
            if entity.get("label") == "NEW_DATE"
        ]

        if target_cue or (
            target_date_positions
            and time_start > max(target_date_positions)
        ):
            time_entity["label"] = "NEW_TIME"

    return result


def _normalize_entities(
    text: str,
    predicted_entities: list[dict],
    intent: str | None = None,
) -> list[dict]:
    """
    Combine ML NER with deterministic extraction.

    Structured entities replace ML predictions for:

        DATE
        TIME
        DURATION
        THRESHOLD

    Semantic entities such as COURSE and TOPIC remain
    model-driven, but are trimmed when they overlap
    with a structured entity.
    """

    structured_entities = (
        _extract_structured_entities(
            text
        )
    )

    structured_labels = {
        "DATE",
        "TIME",
        "DURATION",
        "THRESHOLD",
    }

    semantic_entities = [
        entity
        for entity in predicted_entities
        if entity.get("label")
        not in structured_labels
    ]

    semantic_entities = (
        _trim_semantic_entities(
            semantic_entities,
            structured_entities,
        )
    )

    final_entities = []

    # ---------------------------------------------
    # REBUILD SEMANTIC ENTITY TEXT
    # ---------------------------------------------

    for entity in semantic_entities:
        start = entity.get(
            "_trimmed_start"
        )
        end = entity.get(
            "_trimmed_end"
        )

        if (
            start is not None
            and end is not None
        ):
            start = int(start)
            end = int(end)

            if start >= end:
                continue

            final_entities.append(
                {
                    "text": text[
                        start:end
                    ],
                    "label": entity[
                        "label"
                    ],
                    "start": start,
                    "end": end,
                }
            )

        else:
            final_entities.append(
                {
                    "text": entity[
                        "text"
                    ],
                    "label": entity[
                        "label"
                    ],
                    "start": int(
                        entity["start"]
                    ),
                    "end": int(
                        entity["end"]
                    ),
                }
            )

    # ---------------------------------------------
    # ADD DETERMINISTIC ENTITIES
    # ---------------------------------------------

    final_entities.extend(
        structured_entities
    )

    # ---------------------------------------------
    # SORT + DEDUPLICATE
    # ---------------------------------------------

    final_entities = (
        _deduplicate_entities(
            final_entities
        )
    )

    final_entities.sort(
        key=lambda entity: (
            entity["start"],
            entity["end"],
        )
    )

    return final_entities


# -------------------------------------------------
# NER
# -------------------------------------------------


def extract_entities(
    text: str,
    entity_model,
    intent: str | None = None,
):
    tokens = tokenize(text)

    if not tokens:
        return []

    features = [
        token_features(
            tokens,
            index,
        )
        for index in range(
            len(tokens)
        )
    ]

    labels = entity_model.predict(
        features
    )

    predicted_entities = reconstruct_entities(
        text,
        tokens,
        labels,
    )

    return _normalize_entities(
        text=text,
        predicted_entities=predicted_entities,
        intent=intent,
    )


# -------------------------------------------------
# COMPLETE NLP PIPELINE
# -------------------------------------------------


def analyze_query(text: str) -> dict:
    """
    Run the complete ProfPilot NLP pipeline.

    Output contains:
        - predicted intent
        - top intent score
        - ranked intent predictions
        - normalized entities
    """

    text = text.strip()

    if not text:
        raise ValueError(
            "Query cannot be empty."
        )

    intent_model, entity_model = (
        load_models()
    )

    intent, ranked_intents = (
        predict_intent(
            intent_model,
            text,
        )
    )

    entities = extract_entities(
        text,
        entity_model,
        intent=intent,
    )

    return {
        "text": text,
        "intent": intent,
        "intent_score": round(
            float(ranked_intents[0][1]),
            4,
        ),
        "top_intents": [
            {
                "intent": label,
                "score": round(
                    float(score),
                    4,
                ),
            }
            for label, score
            in ranked_intents[:5]
        ],
        "entities": entities,
    }


# -------------------------------------------------
# CLI
# -------------------------------------------------


def main():
    import sys

    if len(sys.argv) < 2:
        print(
            'Usage:\n'
            'python ai/nlp/pipeline.py '
            '"your query here"'
        )
        raise SystemExit(1)

    query = " ".join(
        sys.argv[1:]
    ).strip()

    result = analyze_query(
        query
    )

    print()
    print(
        "ProfPilot NLP Pipeline"
    )
    print("=" * 50)

    print(
        f"Query  : {result['text']}"
    )

    print(
        f"Intent : {result['intent']}"
    )

    print(
        f"Score  : "
        f"{result['intent_score']:.4f}"
    )

    print("\nTop intents:")

    for prediction in (
        result["top_intents"]
    ):
        print(
            f"  "
            f"{prediction['intent']:<30}"
            f"{prediction['score']:.4f}"
        )

    print("\nEntities:")

    if not result["entities"]:
        print("  None")
    else:
        for entity in result[
            "entities"
        ]:
            print(
                f"  "
                f"{entity['label']:<12}"
                f"{entity['text']!r} "
                f"[{entity['start']}:"
                f"{entity['end']}]"
            )


if __name__ == "__main__":
    main()