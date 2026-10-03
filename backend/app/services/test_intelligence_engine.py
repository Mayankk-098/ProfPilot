from __future__ import annotations

import json

from app.database.db import SessionLocal
from app.services.intelligence_engine import build_course_intelligence


def main():
    db = SessionLocal()
    try:
        result = build_course_intelligence(db=db, course_id="dbms")
        assert result["status"] == "ok"
        assert result["summary"]["course_id"] == "dbms"
        assert "recommendation" in result
        assert "academic_state" in result["evidence"]
        assert "prediction" in result["evidence"]
        assert "drift" in result["evidence"]
        print(json.dumps(result, indent=2, ensure_ascii=False))
    finally:
        db.close()


if __name__ == "__main__":
    main()
