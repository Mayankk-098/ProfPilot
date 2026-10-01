from __future__ import annotations

import sys
from pathlib import Path

import joblib


ROOT = Path(__file__).resolve().parents[2]

MODEL_PATH = (
    ROOT
    / "ai"
    / "intent"
    / "models"
    / "intent_tfidf_logreg.joblib"
)


def load_model():
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            "Intent model not found. "
            "Run train.py first."
        )

    return joblib.load(MODEL_PATH)


def predict(model, text: str):
    predicted_intent = model.predict([text])[0]

    probabilities = model.predict_proba([text])[0]

    classes = model.classes_

    ranked = sorted(
        zip(classes, probabilities),
        key=lambda item: item[1],
        reverse=True,
    )

    return predicted_intent, ranked


def main():
    if len(sys.argv) < 2:
        print(
            'Usage:\n'
            '  python ai/intent/predict.py '
            '"your question here"'
        )
        raise SystemExit(1)

    text = " ".join(sys.argv[1:]).strip()

    if not text:
        print("Please provide a non-empty query.")
        raise SystemExit(1)

    model = load_model()

    intent, ranked = predict(
        model,
        text,
    )

    print("\nProfPilot Intent Prediction")
    print("=" * 40)

    print(f"Input : {text}")
    print(f"Intent: {intent}")

    print("\nTop predictions:")

    for label, probability in ranked[:5]:
        print(
            f"  {label:<30} "
            f"{probability:.4f}"
        )


if __name__ == "__main__":
    main()