from __future__ import annotations

import json

from app.database.db import SessionLocal
from app.services.prediction_engine import (
    predict_course_completion,
)


def main():
    db = SessionLocal()

    try:
        result = predict_course_completion(
            db=db,
            course_id="dbms",
        )

        print(
            json.dumps(
                result,
                indent=2,
                ensure_ascii=False,
            )
        )

    finally:
        db.close()


if __name__ == "__main__":
    main()