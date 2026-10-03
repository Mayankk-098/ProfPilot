from __future__ import annotations

import json

from app.database.db import SessionLocal
from app.services.what_if_engine import (
    simulate_schedule_change,
)


def main():
    db = SessionLocal()

    try:
        cancel_result = (
            simulate_schedule_change(
                db=db,
                course_id="dbms",
                message=(
                    "What if I cancel one DBMS class?"
                ),
            )
        )

        extra_result = (
            simulate_schedule_change(
                db=db,
                course_id="dbms",
                message=(
                    "What if I add one extra DBMS class?"
                ),
            )
        )

        print(
            "=== CANCEL SCENARIO ==="
        )
        print(
            json.dumps(
                cancel_result,
                indent=2,
                ensure_ascii=False,
            )
        )

        print(
            "\n=== EXTRA CLASS SCENARIO ==="
        )
        print(
            json.dumps(
                extra_result,
                indent=2,
                ensure_ascii=False,
            )
        )

    finally:
        db.close()


if __name__ == "__main__":
    main()