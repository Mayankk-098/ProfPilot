from __future__ import annotations

import json

from app.database.db import SessionLocal
from app.services.syllabus_drift_engine import (
    detect_syllabus_drift,
)


def main() -> None:
    db = SessionLocal()

    try:
        result = detect_syllabus_drift(
            db=db,
            course_id="dbms",
        )

        print(json.dumps(
            result,
            indent=2,
            default=str,
        ))

    finally:
        db.close()


if __name__ == "__main__":
    main()
