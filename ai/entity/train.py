from __future__ import annotations

import json
import re
from pathlib import Path

import joblib
from sklearn.feature_extraction import DictVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
from sklearn.pipeline import Pipeline


ROOT = Path(__file__).resolve().parents[2]

DATASET_PATH = ROOT / "data" / "intent" / "examples.jsonl"

MODEL_DIR = ROOT / "ai" / "entity" / "models"
MODEL_PATH = MODEL_DIR / "entity_token_classifier.joblib"


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


def load_examples():
    examples = []

    with DATASET_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        for line in file:
            line = line.strip()

            if line:
                examples.append(json.loads(line))

    return examples


def tokenize(text: str):
    """
    Return tokens with character offsets.

    Example:
        "cancel DBMS class"

    ->
        ("cancel", 0, 6)
        ("DBMS", 7, 11)
        ("class", 12, 17)
    """
    return [
        (
            match.group(),
            match.start(),
            match.end(),
        )
        for match in TOKEN_PATTERN.finditer(text)
    ]


def entity_label_for_span(
    token_start: int,
    token_end: int,
    entities: list[dict],
):
    """
    Convert character-span entities into BIO labels.
    """
    for entity in entities:
        entity_start = entity["start"]
        entity_end = entity["end"]
        entity_type = entity["label"]

        # No overlap.
        if token_end <= entity_start or token_start >= entity_end:
            continue

        # Token is inside this entity.
        if token_start == entity_start:
            return f"B-{entity_type}"

        return f"I-{entity_type}"

    return "O"


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


def build_token_dataset(examples):
    X = []
    y = []

    for example in examples:
        tokens = tokenize(example["text"])

        entities = example.get(
            "entities",
            [],
        )

        for index, (_, start, end) in enumerate(tokens):
            features = token_features(
                tokens,
                index,
            )

            label = entity_label_for_span(
                start,
                end,
                entities,
            )

            X.append(features)
            y.append(label)

    return X, y


def split_token_dataset(examples):
    result = {
        "train": [],
        "dev": [],
        "test": [],
    }

    for example in examples:
        split = example["split"]

        if split in result:
            result[split].append(example)

    return result


def build_model() -> Pipeline:
    return Pipeline(
        [
            (
                "vectorizer",
                DictVectorizer(
                    sparse=True,
                ),
            ),
            (
                "classifier",
                LogisticRegression(
                    max_iter=3000,
                    class_weight="balanced",
                    random_state=42,
                ),
            ),
        ]
    )


def evaluate(
    model,
    examples,
    split_name: str,
):
    X, y = build_token_dataset(examples)

    predictions = model.predict(X)

    print()
    print("=" * 60)
    print(f"{split_name.upper()} ENTITY RESULTS")
    print("=" * 60)

    print(
        classification_report(
            y,
            predictions,
            zero_division=0,
        )
    )


def main():
    print("Loading entity dataset...")

    examples = load_examples()

    print(
        f"Total examples: {len(examples)}"
    )

    splits = split_token_dataset(
        examples
    )

    print(
        f"Train examples: {len(splits['train'])}"
    )

    print(
        f"Dev examples:   {len(splits['dev'])}"
    )

    print(
        f"Test examples:  {len(splits['test'])}"
    )

    X_train, y_train = build_token_dataset(
        splits["train"]
    )

    print(
        f"Training tokens: {len(X_train)}"
    )

    model = build_model()

    print(
        "\nTraining token-level entity classifier..."
    )

    model.fit(
        X_train,
        y_train,
    )

    MODEL_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    joblib.dump(
        model,
        MODEL_PATH,
    )

    print(
        f"\nModel saved to:\n{MODEL_PATH}"
    )

    evaluate(
        model,
        splits["dev"],
        "dev",
    )

    evaluate(
        model,
        splits["test"],
        "test",
    )


if __name__ == "__main__":
    main()