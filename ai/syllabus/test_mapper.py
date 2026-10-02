from __future__ import annotations

import sys

from app.database.db import SessionLocal

from ai.syllabus.mapper import map_and_format


def main():
    if len(sys.argv) < 3:
        print(
            'Usage:\n'
            'python -m ai.syllabus.test_mapper '
            '"course_id" "lecture description"'
        )
        raise SystemExit(1)

    course_id = sys.argv[1]

    lecture_description = " ".join(
        sys.argv[2:]
    ).strip()

    db = SessionLocal()

    try:
        result = map_and_format(
            db=db,
            course_id=course_id,
            lecture_description=lecture_description,
            top_k=5,
        )

        print()
        print("ProfPilot Lecture → Syllabus Mapper")
        print("=" * 55)

        print(
            f"Course: {result['course_id']}"
        )

        print(
            f"Lecture: {result['lecture_description']}"
        )

        print("\nMatches:")

        if not result["matches"]:
            print(
                "  No sufficiently similar "
                "syllabus topics found."
            )
            return

        for match in result["matches"]:
            print(
                f"  {match['score']:.4f}  "
                f"{match['topic']} "
                f"({match['unit']})"
            )

    finally:
        db.close()


if __name__ == "__main__":
    main()