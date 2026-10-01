from __future__ import annotations

import json
from pathlib import Path

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
)
from sklearn.pipeline import Pipeline


ROOT = Path(__file__).resolve().parents[2]

DATASET_PATH = ROOT / "data" / "intent" / "examples.jsonl"

MODEL_DIR = ROOT / "ai" / "intent" / "models"
MODEL_PATH = MODEL_DIR / "intent_tfidf_logreg.joblib"


def load_examples():
    if not DATASET_PATH.exists():
        raise FileNotFoundError(
            f"Dataset not found: {DATASET_PATH}"
        )

    examples = []

    with DATASET_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        for line_number, line in enumerate(file, start=1):
            line = line.strip()

            if not line:
                continue

            try:
                example = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"Invalid JSON on line {line_number}: {exc}"
                ) from exc

            required_fields = {
                "text",
                "intent",
                "split",
            }

            missing = required_fields - example.keys()

            if missing:
                raise ValueError(
                    f"Line {line_number} is missing fields: {missing}"
                )

            examples.append(example)

    return examples


def split_examples(examples):
    train = [
        example
        for example in examples
        if example["split"] == "train"
    ]

    dev = [
        example
        for example in examples
        if example["split"] == "dev"
    ]

    test = [
        example
        for example in examples
        if example["split"] == "test"
    ]

    return train, dev, test


def build_model() -> Pipeline:
    """
    Transparent baseline:

    TF-IDF word n-grams
        +
    Logistic Regression
    """
    return Pipeline(
        [
            (
                "tfidf",
                TfidfVectorizer(
                    lowercase=True,
                    strip_accents="unicode",
                    ngram_range=(1, 2),
                    sublinear_tf=True,
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


def evaluate(model, examples, split_name: str):
    if not examples:
        print(f"\n[{split_name}] No examples found.")
        return

    texts = [example["text"] for example in examples]
    labels = [example["intent"] for example in examples]

    predictions = model.predict(texts)

    accuracy = accuracy_score(
        labels,
        predictions,
    )

    macro_f1 = f1_score(
        labels,
        predictions,
        average="macro",
        zero_division=0,
    )

    print(f"\n{'=' * 60}")
    print(f"{split_name.upper()} RESULTS")
    print(f"{'=' * 60}")

    print(f"Examples : {len(examples)}")
    print(f"Accuracy : {accuracy:.4f}")
    print(f"Macro F1 : {macro_f1:.4f}")

    print("\nClassification report:")
    print(
        classification_report(
            labels,
            predictions,
            zero_division=0,
        )
    )

    labels_sorted = sorted(set(labels) | set(predictions))

    matrix = confusion_matrix(
        labels,
        predictions,
        labels=labels_sorted,
    )

    print("Confusion matrix labels:")
    print(labels_sorted)

    print(matrix)


def main():
    print("Loading dataset...")
    examples = load_examples()

    print(f"Total examples: {len(examples)}")

    train, dev, test = split_examples(examples)

    print(f"Train examples: {len(train)}")
    print(f"Dev examples:   {len(dev)}")
    print(f"Test examples:  {len(test)}")

    X_train = [
        example["text"]
        for example in train
    ]

    y_train = [
        example["intent"]
        for example in train
    ]

    print("\nTraining TF-IDF + Logistic Regression...")

    model = build_model()

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

    print(f"\nModel saved to:")
    print(MODEL_PATH)

    evaluate(
        model,
        dev,
        "dev",
    )

    evaluate(
        model,
        test,
        "test",
    )


if __name__ == "__main__":
    main()