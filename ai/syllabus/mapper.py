from __future__ import annotations

from dataclasses import dataclass

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy.orm import Session

from app.models.academic import SyllabusTopic


@dataclass
class TopicMatch:
    topic_id: int
    topic_name: str
    unit_name: str
    score: float


def _build_topic_text(
    topic: SyllabusTopic,
) -> str:
    """
    Build the searchable representation of a syllabus topic.
    Including the unit gives the mapper more context.
    """
    unit_name = ""

    if topic.unit is not None:
        unit_name = topic.unit.name or ""

    return (
        f"{unit_name} "
        f"{topic.name}"
    ).strip()


def map_lecture_to_syllabus(
    db: Session,
    course_id: str,
    lecture_description: str,
    top_k: int = 3,
    min_score: float = 0.05,
) -> list[TopicMatch]:
    """
    Find the syllabus topics most similar to a lecture description.

    This is a V1 lexical/TF-IDF baseline.
    It is NOT the final semantic mapping model.
    """

    description = (
        lecture_description
        or ""
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

    topic_texts = [
        _build_topic_text(topic)
        for topic in topics
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

    matrix = vectorizer.fit_transform(
        corpus
    )

    lecture_vector = matrix[0:1]

    topic_vectors = matrix[1:]

    similarities = cosine_similarity(
        lecture_vector,
        topic_vectors,
    )[0]

    matches: list[TopicMatch] = []

    for topic, score in zip(
        topics,
        similarities,
    ):
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
                    float(score),
                    4,
                ),
            )
        )

    matches.sort(
        key=lambda item: item.score,
        reverse=True,
    )

    return matches[:top_k]


def map_and_format(
    db: Session,
    course_id: str,
    lecture_description: str,
    top_k: int = 3,
) -> dict:
    """
    API-friendly wrapper around the mapper.
    """

    matches = map_lecture_to_syllabus(
        db=db,
        course_id=course_id,
        lecture_description=lecture_description,
        top_k=top_k,
    )

    return {
        "course_id": course_id,
        "lecture_description": lecture_description,
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