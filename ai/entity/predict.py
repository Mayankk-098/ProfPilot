from __future__ import annotations

import re
import sys
from pathlib import Path

import joblib


ROOT = Path(__file__).resolve().parents[2]

MODEL_PATH = (
    ROOT
    / "ai"
    / "entity"
    / "models"
    / "entity_token_classifier.joblib"
)

TOKEN_PATTERN = re.compile(
    r"""
    \d+(?::\d+)?(?:\s?[APMapm]{2})?
    |
    \d+(?:\.\d+)?%
    |
    \d+(?:\.\d+)?
    |
    [A-Za-z]+
    """,
    re.VERBOSE,
)


def tokenize(text: str):
    return [
        (
            match.group(),
            match.start(),
            match.end(),
        )
        for match in TOKEN_PATTERN.finditer(text)
    ]


def token_features(
    tokens,
    index: int,
):
    token = tokens[index][0]

    previous = (
        tokens[index - 1][0]
        if index > 0
        else "<START>"
    )

    next_token = (
        tokens[index + 1][0]
        if index + 1 < len(tokens)
        else "<END>"
    )

    return {
        "token.lower": token.lower(),
        "token.is_upper": token.isupper(),
        "token.is_title": token.istitle(),
        "token.is_digit": token.isdigit(),
        "token.has_digit": any(
            character.isdigit()
            for character in token
        ),
        "token.has_percent": "%" in token,
        "token.has_colon": ":" in token,
        "token.prefix2": token[:2].lower(),
        "token.prefix3": token[:3].lower(),
        "token.suffix2": token[-2:].lower(),
        "token.suffix3": token[-3:].lower(),
        "prev.lower": previous.lower(),
        "next.lower": next_token.lower(),
    }


def load_model():
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            "Entity model not found. "
            "Run train.py first."
        )

    return joblib.load(
        MODEL_PATH
    )


def reconstruct_entities(
    text: str,
    tokens,
    labels,
):
    entities = []

    current_label = None
    current_start = None
    current_end = None

    for token_data, label in zip(
        tokens,
        labels,
    ):
        token, start, end = token_data

        if label == "O":
            if current_label is not None:
                entities.append(
                    {
                        "text": text[
                            current_start:current_end
                        ],
                        "label": current_label,
                        "start": current_start,
                        "end": current_end,
                    }
                )

                current_label = None
                current_start = None
                current_end = None

            continue

        prefix, entity_type = label.split(
            "-",
            1,
        )

        if (
            prefix == "B"
            or current_label != entity_type
        ):
            if current_label is not None:
                entities.append(
                    {
                        "text": text[
                            current_start:current_end
                        ],
                        "label": current_label,
                        "start": current_start,
                        "end": current_end,
                    }
                )

            current_label = entity_type
            current_start = start
            current_end = end

        else:
            current_end = end

    if current_label is not None:
        entities.append(
            {
                "text": text[
                    current_start:current_end
                ],
                "label": current_label,
                "start": current_start,
                "end": current_end,
            }
        )

    return entities


def predict(text: str):
    model = load_model()

    tokens = tokenize(text)

    features = [
        token_features(
            tokens,
            index,
        )
        for index in range(
            len(tokens)
        )
    ]

    labels = model.predict(
        features
    )

    return reconstruct_entities(
        text,
        tokens,
        labels,
    )


def main():
    if len(sys.argv) < 2:
        print(
            'Usage:\n'
            'python ai/entity/predict.py '
            '"your sentence here"'
        )
        raise SystemExit(1)

    text = " ".join(
        sys.argv[1:]
    ).strip()

    if not text:
        raise SystemExit(
            "Empty input."
        )

    entities = predict(text)

    print()
    print("ProfPilot Entity Prediction")
    print("=" * 40)
    print(f"Input: {text}")
    print()

    if not entities:
        print("No entities detected.")
        return

    for entity in entities:
        print(
            f"{entity['label']:<12} "
            f"{entity['text']!r} "
            f"[{entity['start']}:{entity['end']}]"
        )


if __name__ == "__main__":
    main()