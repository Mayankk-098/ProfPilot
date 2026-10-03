from __future__ import annotations

import json

from app.database.db import SessionLocal
from app.services.academic_state import (
    build_course_state,
)


def main():
    db = SessionLocal()

    try:
        state = build_course_state(
            db=db,
            course_id="dbms",
        )

        print(
            json.dumps(
                state,
                indent=2,
                ensure_ascii=False,
            )
        )

    finally:
        db.close()


if __name__ == "__main__":
    main()