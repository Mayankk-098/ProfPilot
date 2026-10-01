import re
from datetime import datetime
from typing import Iterable

from sqlalchemy.orm import Session

from app.models.memory import AcademicEvent
from app.services.memory_service import get_memories


STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "am",
    "be",
    "been",
    "but",
    "by",
    "can",
    "could",
    "did",
    "do",
    "does",
    "for",
    "from",
    "get",
    "had",
    "has",
    "have",
    "how",
    "i",
    "in",
    "is",
    "it",
    "me",
    "my",
    "of",
    "on",
    "or",
    "should",
    "the",
    "this",
    "to",
    "was",
    "what",
    "when",
    "why",
    "will",
    "with",
    "would",
    "you",
    "your",
}


EVENT_KEYWORDS = {
    "lecture": {
        "lecture",
        "taught",
        "teach",
        "covered",
        "topic",
        "class",
    },
    "class_cancelled": {
        "cancel",
        "cancelled",
        "cancellation",
        "missed",
        "delay",
    },
    "syllabus": {
        "syllabus",
        "progress",
        "topic",
        "completed",
        "completion",
        "behind",
        "pace",
    },
    "schedule_change": {
        "schedule",
        "reschedule",
        "rescheduled",
        "time",
        "class",
    },
    "attendance": {
        "attendance",
        "absent",
        "present",
        "student",
        "students",
        "percentage",
    },
}


def tokenize(text: str) -> set[str]:
    """
    Convert text into a normalized set of meaningful words.
    """
    words = re.findall(r"[a-zA-Z0-9]+", text.lower())

    return {
        word
        for word in words
        if word not in STOP_WORDS and len(word) > 1
    }


def lexical_overlap(
    query_tokens: set[str],
    memory_text: str,
) -> float:
    """
    Returns a value between 0 and 1 representing
    how much the memory overlaps with the user's question.
    """
    if not query_tokens:
        return 0.0

    memory_tokens = tokenize(memory_text)

    if not memory_tokens:
        return 0.0

    overlap = query_tokens.intersection(memory_tokens)

    return len(overlap) / len(query_tokens)


def event_type_relevance(
    query_tokens: set[str],
    event_type: str,
) -> float:
    """
    Gives a small boost when the type of academic event
    matches the language of the user's question.
    """
    keywords = EVENT_KEYWORDS.get(event_type, set())

    if not keywords:
        return 0.0

    matches = query_tokens.intersection(keywords)

    if matches:
        return min(1.0, len(matches) / 2)

    return 0.0


def recency_score(occurred_at: datetime) -> float:
    """
    Recent memories receive a higher score.

    This is deliberately a gentle decay so an older
    important academic event can still remain relevant.
    """
    now = datetime.now()

    # Current database stores naive datetimes.
    if occurred_at.tzinfo is not None:
        occurred_at = occurred_at.replace(tzinfo=None)

    age_days = max(0, (now - occurred_at).days)

    # Approximately:
    # today       -> 1.00
    # 7 days ago  -> ~0.70
    # 30 days ago -> ~0.25
    # 90+ days    -> ~0.00
    return max(0.0, 1.0 - (age_days / 90.0))


def score_memory(
    memory: AcademicEvent,
    query: str,
    course_id: str | None = None,
) -> float:
    """
    Calculate a relevance score between 0 and 1.

    Components:
    - keyword overlap
    - course match
    - event-type relevance
    - recency
    """
    query_tokens = tokenize(query)

    searchable_text = " ".join(
        [
            memory.title or "",
            memory.summary or "",
            memory.event_type or "",
        ]
    )

    lexical_score = lexical_overlap(
        query_tokens,
        searchable_text,
    )

    type_score = event_type_relevance(
        query_tokens,
        memory.event_type,
    )

    if course_id and memory.course_id == course_id:
        course_score = 1.0
    elif course_id and memory.course_id is None:
        # Institution/faculty-level memories can still
        # be relevant to the selected course.
        course_score = 0.45
    else:
        course_score = 0.0

    recent_score = recency_score(memory.occurred_at)

    # Weighted relevance model.
    score = (
        (lexical_score * 0.55)
        + (course_score * 0.25)
        + (type_score * 0.10)
        + (recent_score * 0.10)
    )

    return round(score, 4)


def get_relevant_memories(
    db: Session,
    query: str,
    lecturer_id: str,
    course_id: str | None = None,
    limit: int = 5,
    candidate_limit: int = 50,
) -> list[AcademicEvent]:
    """
    Retrieve candidate memories and return the most relevant ones.
    """
    candidates = get_memories(
        db=db,
        lecturer_id=lecturer_id,
        course_id=None,
        limit=candidate_limit,
    )

    scored_memories: list[tuple[AcademicEvent, float]] = []

    for memory in candidates:
        score = score_memory(
            memory=memory,
            query=query,
            course_id=course_id,
        )

        scored_memories.append(
            (memory, score)
        )

    scored_memories.sort(
        key=lambda item: item[1],
        reverse=True,
    )

    # Remove completely irrelevant memories.
    relevant = [
        memory
        for memory, score in scored_memories
        if score >= 0.10
    ]

    return relevant[:limit]