from __future__ import annotations

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


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


@lru_cache(maxsize=1)
def load_models():
    """
    Load both trained models once and reuse them.

    This prevents joblib model loading on every query.
    """
    intent_model = load_intent_model()
    entity_model = load_entity_model()

    return intent_model, entity_model


def extract_entities(
    text: str,
    entity_model,
):
    tokens = tokenize(text)

    if not tokens:
        return []

    features = [
        token_features(
            tokens,
            index,
        )
        for index in range(len(tokens))
    ]

    labels = entity_model.predict(features)

    return reconstruct_entities(
        text,
        tokens,
        labels,
    )


def analyze_query(text: str) -> dict:
    """
    Run the complete ProfPilot NLP pipeline.

    Output contains:
    - predicted intent
    - top intent score
    - ranked intent predictions
    - extracted entities
    """
    text = text.strip()

    if not text:
        raise ValueError(
            "Query cannot be empty."
        )

    intent_model, entity_model = load_models()

    intent, ranked_intents = predict_intent(
        intent_model,
        text,
    )

    entities = extract_entities(
        text,
        entity_model,
    )

    return {
        "text": text,
        "intent": intent,
        "intent_score": round(
            ranked_intents[0][1],
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
            for label, score in ranked_intents[:5]
        ],
        "entities": entities,
    }


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

    result = analyze_query(query)

    print()
    print("ProfPilot NLP Pipeline")
    print("=" * 50)

    print(
        f"Query  : {result['text']}"
    )

    print(
        f"Intent : {result['intent']}"
    )

    print(
        f"Score  : {result['intent_score']:.4f}"
    )

    print("\nTop intents:")

    for prediction in result["top_intents"]:
        print(
            f"  {prediction['intent']:<30}"
            f"{prediction['score']:.4f}"
        )

    print("\nEntities:")

    if not result["entities"]:
        print("  None")
    else:
        for entity in result["entities"]:
            print(
                f"  {entity['label']:<12}"
                f"{entity['text']!r} "
                f"[{entity['start']}:{entity['end']}]"
            )


if __name__ == "__main__":
    main()