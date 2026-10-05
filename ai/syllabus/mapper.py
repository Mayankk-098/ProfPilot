from __future__ import annotations

import re
from dataclasses import dataclass

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy.orm import Session

from app.models.academic import SyllabusTopic


DEFAULT_MIN_SCORE = 0.15


@dataclass
class TopicMatch:
    topic_id: str
    topic_name: str
    unit_name: str
    score: float


def _normalize_tokens(text: str | None) -> set[str]:
    """
    Convert text into a small normalized token set.

    This is intentionally lightweight because this mapper
    is a V1 lexical baseline, not a semantic language model.
    """

    if not text:
        return set()

    text = str(text).lower()

    # Treat punctuation such as B+ or B-tree as separators
    # for the general lexical gate.
    text = re.sub(
        r"[^a-z0-9]+",
        " ",
        text,
    )

    tokens = {
        token
        for token in text.split()
        if len(token) > 1
    }

    # Remove very generic words that should not drive
    # syllabus matching.
    stop_words = {
        "the",
        "and",
        "for",
        "with",
        "from",
        "into",
        "about",
        "this",
        "that",
        "were",
        "was",
        "are",
        "is",
        "of",
        "to",
        "in",
        "on",
        "an",
        "a",
        "be",
        "been",
        "covered",
        "cover",
        "covers",
        "introduced",
        "introduction",
        "revision",
        "revised",
        "discussion",
        "discussed",
        "lecture",
        "class",
        "topic",
        "topics",
    }

    return {
        token
        for token in tokens
        if token not in stop_words
    }


def _normalize_phrase(text: str | None) -> str:
    """
    Normalize text for exact topic-phrase matching.

    Unlike _normalize_tokens(), this intentionally preserves
    '+' because it is meaningful in syllabus names such as
    'B+ Trees'.
    """

    if not text:
        return ""

    text = str(text).lower()

    text = re.sub(
        r"[^a-z0-9+]+",
        " ",
        text,
    )

    return " ".join(
        text.split()
    )


def _phrase_in_text(
    phrase: str,
    text: str,
) -> bool:
    """
    Check whether a complete normalized phrase occurs
    inside normalized text.
    """

    if not phrase or not text:
        return False

    return (
        f" {phrase} " in
        f" {text} "
    )


def _build_topic_text(
    topic: SyllabusTopic,
) -> str:
    """
    Build the searchable representation of a topic.

    Important:

    The unit name is NOT injected into the searchable text.

    Example:

        Unit:
            Unit 2 — Database Design

        Topic:
            Functional Dependencies

    Search text becomes:

        Functional Dependencies

    rather than:

        Unit 2 Database Design Functional Dependencies

    This prevents generic unit wording from creating
    false-positive matches.
    """

    return (
        topic.name or ""
    ).strip()


def map_lecture_to_syllabus(
    db: Session,
    course_id: str,
    lecture_description: str,
    top_k: int = 3,
    min_score: float = DEFAULT_MIN_SCORE,
) -> list[TopicMatch]:
    """
    Find syllabus topics most similar to a lecture description.

    V1 strategy:

    1. Require a meaningful lexical overlap between the
       lecture description and the topic name.
    2. Prefer an exact syllabus topic phrase when one exists.
    3. Use TF-IDF cosine similarity to rank candidates.
    4. Discard weak similarity scores.
    5. Return at most top_k matches.

    This is intentionally conservative. A vague lecture
    description should produce no match rather than
    incorrectly completing several syllabus topics.
    """

    description = (
        lecture_description or ""
    ).strip()

    if not description:
        return []

    topics = (
        db.query(SyllabusTopic)
        .join(SyllabusTopic.unit)
        .filter(
            SyllabusTopic.unit.has(
                course_id=course_id
            )
        )
        .all()
    )

    if not topics:
        return []

    lecture_tokens = _normalize_tokens(
        description
    )

    if not lecture_tokens:
        return []

    candidate_topics = []

    for topic in topics:
        topic_text = _build_topic_text(
            topic
        )

        topic_tokens = _normalize_tokens(
            topic_text
        )

        # Conservative lexical gate:
        # at least one meaningful topic token must
        # appear in the lecture description.
        if not lecture_tokens.intersection(
            topic_tokens
        ):
            continue

        candidate_topics.append(
            (
                topic,
                topic_text,
            )
        )

    if not candidate_topics:
        return []

    # -------------------------------------------------
    # EXACT TOPIC PHRASE PREFERENCE
    # -------------------------------------------------
    #
    # This solves cases such as:
    #
    #   "B Trees"  vs  "B+ Trees"
    #
    # The general lexical gate intentionally treats "+"
    # as punctuation, which means both topics can become
    # "b trees" during token matching.
    #
    # Before running TF-IDF, prefer exact topic phrases
    # when one is explicitly present in the lecture text.
    # -------------------------------------------------

    lecture_phrase = _normalize_phrase(
        description
    )

    exact_candidates = []

    for topic, topic_text in candidate_topics:
        topic_phrase = _normalize_phrase(
            topic_text
        )

        if _phrase_in_text(
            topic_phrase,
            lecture_phrase,
        ):
            exact_candidates.append(
                (
                    topic,
                    topic_text,
                )
            )

    if exact_candidates:
        candidate_topics = exact_candidates

    topic_texts = [
        topic_text
        for _, topic_text in candidate_topics
    ]

    corpus = [
        description,
        *topic_texts,
    ]

    vectorizer = TfidfVectorizer(
        lowercase=True,
        strip_accents="unicode",
        ngram_range=(1, 2),
        sublinear_tf=True,
    )

    try:
        matrix = vectorizer.fit_transform(
            corpus
        )
    except ValueError:
        return []

    lecture_vector = matrix[0:1]

    topic_vectors = matrix[1:]

    similarities = cosine_similarity(
        lecture_vector,
        topic_vectors,
    )[0]

    matches: list[TopicMatch] = []

    for (topic, _), score in zip(
        candidate_topics,
        similarities,
    ):
        score = float(score)

        if score < min_score:
            continue

        unit_name = (
            topic.unit.name
            if topic.unit
            else ""
        )

        matches.append(
            TopicMatch(
                topic_id=topic.id,
                topic_name=topic.name,
                unit_name=unit_name,
                score=round(
                    score,
                    4,
                ),
            )
        )

    matches.sort(
        key=lambda match: (
            -match.score,
            match.topic_name.lower(),
        )
    )

    return matches[:top_k]


def map_and_format(
    db: Session,
    course_id: str,
    lecture_description: str,
    top_k: int = 3,
    min_score: float = DEFAULT_MIN_SCORE,
) -> dict:
    """
    API-friendly wrapper around the mapper.
    """

    matches = map_lecture_to_syllabus(
        db=db,
        course_id=course_id,
        lecture_description=lecture_description,
        top_k=top_k,
        min_score=min_score,
    )

    return {
        "course_id": course_id,
        "lecture_description": (
            lecture_description
        ),
        "matches": [
            {
                "topic_id": match.topic_id,
                "topic": match.topic_name,
                "unit": match.unit_name,
                "score": match.score,
            }
            for match in matches
        ],
    }