"""
One-time migration for an older ProfPilot SQLite database.

Purpose:
- Preserve existing academic data.
- Normalize legacy date fields to ISO dates.
- Ensure syllabus ordering fields exist and are deterministic.
- Convert legacy syllabus completion into covered_in_lecture_id.
- Ensure schedule fields are populated from legacy time/period data.
- Preserve Student, Enrollment, AttendanceRecord, ScheduleChange and User data.
- Validate relationships and uniqueness before committing.

This migration is for an EXISTING older database.
Do not run it against a freshly seeded database.

Limitations: this is a one-time in-place transformation, not a general schema
migration framework. It requires the legacy domain tables listed by
`require_tables`; it does not reconstruct missing students, enrollments,
attendance, schedule changes, users, lecturers, or memory rows. It preserves
legacy course metric columns as extra SQLite columns because SQLite cannot
safely remove them in place; the current ORM simply ignores those columns.
A copy of the legacy database should always be migrated first and compared
before replacing the original.
"""

import argparse
import os
import sqlite3
from datetime import datetime, date, time, timedelta
from pathlib import Path


DEFAULT_DB = Path(__file__).resolve().with_name("profpilot.db")


def parse_date(value):
    """Convert supported legacy date formats into YYYY-MM-DD."""
    if value is None:
        return None

    if isinstance(value, date):
        return value.isoformat()

    value = str(value).strip()

    formats = (
        "%Y-%m-%d",
        "%d %B %Y",
        "%d %b %Y",
        "%Y/%m/%d",
    )

    for fmt in formats:
        try:
            return datetime.strptime(value, fmt).date().isoformat()
        except ValueError:
            pass

    raise RuntimeError(f"Unsupported date value: {value!r}")


def parse_time(value):
    """Convert legacy time values into HH:MM:SS."""
    if value is None:
        return None

    if isinstance(value, time):
        return value.strftime("%H:%M:%S")

    value = str(value).strip()

    formats = (
        "%H:%M:%S",
        "%H:%M",
        "%I:%M %p",
        "%I:%M%p",
    )

    for fmt in formats:
        try:
            return datetime.strptime(value, fmt).time().strftime("%H:%M:%S")
        except ValueError:
            pass

    raise RuntimeError(f"Unsupported time value: {value!r}")


def columns(conn, table):
    return {
        row[1]
        for row in conn.execute(f"PRAGMA table_info({table})").fetchall()
    }


def require_tables(conn):
    required = {
        "academic_events",
        "attendance_records",
        "courses",
        "enrollments",
        "lecture_logs",
        "lecturers",
        "schedule_changes",
        "schedule_items",
        "students",
        "syllabus_topics",
        "syllabus_units",
        "users",
    }

    actual = {
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type='table'"
        ).fetchall()
    }

    missing = required - actual

    if missing:
        raise RuntimeError(
            f"Required tables are missing: {sorted(missing)}"
        )


def ensure_column(conn, table, column, sql_type):
    if column not in columns(conn, table):
        conn.execute(
            f"ALTER TABLE {table} "
            f"ADD COLUMN {column} {sql_type}"
        )


def migrate_lecture_dates(conn):
    print("Migrating lecture dates...")

    lecture_columns = columns(conn, "lecture_logs")

    if "lecture_date" not in lecture_columns:
        if "date" not in lecture_columns:
            raise RuntimeError(
                "lecture_logs has neither lecture_date nor legacy date column"
            )

        conn.execute(
            "ALTER TABLE lecture_logs "
            "RENAME COLUMN date TO lecture_date"
        )

    rows = conn.execute(
        "SELECT id, lecture_date FROM lecture_logs"
    ).fetchall()

    for lecture_id, value in rows:
        converted = parse_date(value)

        if converted is None:
            raise RuntimeError(
                f"Lecture {lecture_id} has no lecture date"
            )

        conn.execute(
            "UPDATE lecture_logs "
            "SET lecture_date=? "
            "WHERE id=?",
            (converted, lecture_id),
        )


def migrate_syllabus_positions(conn):
    print("Migrating syllabus positions...")

    ensure_column(
        conn,
        "syllabus_units",
        "position",
        "INTEGER NOT NULL DEFAULT 0",
    )

    ensure_column(
        conn,
        "syllabus_topics",
        "position",
        "INTEGER NOT NULL DEFAULT 0",
    )

    # Preserve existing meaningful positions.
    # If multiple legacy rows have the same/default position,
    # deterministically assign positions by row order.
    courses = conn.execute(
        "SELECT id FROM courses ORDER BY id"
    ).fetchall()

    for (course_id,) in courses:
        units = conn.execute(
            """
            SELECT id
            FROM syllabus_units
            WHERE course_id=?
            ORDER BY position, rowid
            """,
            (course_id,),
        ).fetchall()

        for position, (unit_id,) in enumerate(units):
            conn.execute(
                """
                UPDATE syllabus_units
                SET position=?
                WHERE id=?
                """,
                (position, unit_id),
            )

    units = conn.execute(
        "SELECT id FROM syllabus_units ORDER BY id"
    ).fetchall()

    for (unit_id,) in units:
        topics = conn.execute(
            """
            SELECT id
            FROM syllabus_topics
            WHERE unit_id=?
            ORDER BY position, rowid
            """,
            (unit_id,),
        ).fetchall()

        for position, (topic_id,) in enumerate(topics):
            conn.execute(
                """
                UPDATE syllabus_topics
                SET position=?
                WHERE id=?
                """,
                (position, topic_id),
            )


def migrate_syllabus_dates_and_completion(conn):
    print("Migrating syllabus dates and completion...")

    topic_columns = columns(conn, "syllabus_topics")

    ensure_column(
        conn,
        "syllabus_topics",
        "covered_in_lecture_id",
        "VARCHAR(50)",
    )

    # Preserve legacy completion independently from lecture linkage.
    # Older ProfPilot versions stored `completed` directly on syllabus_topics.
    ensure_column(
        conn,
        "syllabus_topics",
        "legacy_completed",
        "INTEGER NOT NULL DEFAULT 0",
    )

    topic_columns = columns(conn, "syllabus_topics")

    if "completed" in topic_columns:
        conn.execute(
            """
            UPDATE syllabus_topics
            SET legacy_completed = CASE
                WHEN completed = 1 THEN 1
                ELSE 0
            END
            """
        )

    if "planned_date" in topic_columns:
        rows = conn.execute(
            "SELECT id, planned_date FROM syllabus_topics"
        ).fetchall()

        for topic_id, value in rows:
            if value is None:
                continue

            converted = parse_date(value)

            conn.execute(
                """
                UPDATE syllabus_topics
                SET planned_date=?
                WHERE id=?
                """,
                (converted, topic_id),
            )

    # Legacy completion is preserved in legacy_completed.
    #
    # We intentionally do NOT reconstruct lecture links for old completed
    # topics. The legacy database may contain completion history without
    # corresponding lecture records, and inventing those relationships would
    # corrupt academic history.

    # Ensure every covered_in_lecture_id points to a real lecture.
    invalid = conn.execute(
        """
        SELECT st.id, st.covered_in_lecture_id
        FROM syllabus_topics st
        LEFT JOIN lecture_logs ll
          ON ll.id=st.covered_in_lecture_id
        WHERE st.covered_in_lecture_id IS NOT NULL
          AND ll.id IS NULL
        """
    ).fetchall()

    if invalid:
        raise RuntimeError(
            "Invalid covered_in_lecture_id values found: "
            f"{invalid}"
        )


def migrate_schedule(conn):
    print("Migrating schedule fields...")

    ensure_column(
        conn,
        "schedule_items",
        "weekday",
        "INTEGER",
    )

    ensure_column(
        conn,
        "schedule_items",
        "start_time",
        "TIME",
    )

    ensure_column(
        conn,
        "schedule_items",
        "end_time",
        "TIME",
    )

    ensure_column(
        conn,
        "schedule_items",
        "lecturer_id",
        "VARCHAR(50)",
    )

    rows = conn.execute(
        """
        SELECT id, subject, weekday, time, period,
               start_time, end_time, lecturer_id
        FROM schedule_items
        ORDER BY id
        """
    ).fetchall()

    for (
        item_id,
        subject,
        weekday,
        legacy_time,
        legacy_period,
        start_time,
        end_time,
        lecturer_id,
    ) in rows:

        if weekday is None:
            raise RuntimeError(
                f"Schedule item {item_id} has no weekday"
            )

        # Convert legacy start time if necessary.
        if start_time is None:
            if legacy_time is None:
                raise RuntimeError(
                    f"Schedule item {item_id} has no start time"
                )

            legacy = str(legacy_time).strip()

            if legacy_period:
                start_value = f"{legacy} {legacy_period}"
            else:
                start_value = legacy

            start_time = parse_time(start_value)
        else:
            start_time = parse_time(start_time)

        if end_time is None:
            # The legacy database does not have a reliable end-time
            # column in its old format. For the existing legacy rows,
            # derive it from the known one-hour schedule interval.
            parsed_start = datetime.strptime(start_time, "%H:%M:%S")
            end_time = (parsed_start + timedelta(hours=1)).time().strftime("%H:%M:%S")
        else:
            end_time = parse_time(end_time)

        if lecturer_id is None:
            lecturer = conn.execute(
                """
                SELECT id
                FROM lecturers
                ORDER BY id
                LIMIT 1
                """
            ).fetchone()

            if lecturer is None:
                raise RuntimeError(
                    f"Schedule item {item_id} has no lecturer "
                    "and no lecturer exists"
                )

            lecturer_id = lecturer[0]

        lecturer_exists = conn.execute(
            """
            SELECT 1
            FROM lecturers
            WHERE id=?
            """,
            (lecturer_id,),
        ).fetchone()

        if lecturer_exists is None:
            raise RuntimeError(
                f"Schedule item {item_id} references "
                f"unknown lecturer {lecturer_id}"
            )

        conn.execute(
            """
            UPDATE schedule_items
            SET start_time=?,
                end_time=?,
                lecturer_id=?
            WHERE id=?
            """,
            (
                start_time,
                end_time,
                lecturer_id,
                item_id,
            ),
        )


def validate_attendance(conn):
    print("Validating attendance...")

    duplicate_rows = conn.execute(
        """
        SELECT student_id, course_id, class_date, COUNT(*)
        FROM attendance_records
        GROUP BY student_id, course_id, class_date
        HAVING COUNT(*) > 1
        """
    ).fetchall()

    if duplicate_rows:
        raise RuntimeError(
            "Duplicate attendance records found: "
            f"{duplicate_rows}"
        )

    invalid_students = conn.execute(
        """
        SELECT DISTINCT ar.student_id
        FROM attendance_records ar
        LEFT JOIN students s
          ON s.id=ar.student_id
        WHERE s.id IS NULL
        """
    ).fetchall()

    if invalid_students:
        raise RuntimeError(
            "Attendance references unknown students: "
            f"{invalid_students}"
        )

    invalid_courses = conn.execute(
        """
        SELECT DISTINCT ar.course_id
        FROM attendance_records ar
        LEFT JOIN courses c
          ON c.id=ar.course_id
        WHERE c.id IS NULL
        """
    ).fetchall()

    if invalid_courses:
        raise RuntimeError(
            "Attendance references unknown courses: "
            f"{invalid_courses}"
        )

    invalid_status = conn.execute(
        """
        SELECT DISTINCT status
        FROM attendance_records
        WHERE status NOT IN ('present', 'absent', 'excused')
        """
    ).fetchall()

    if invalid_status:
        raise RuntimeError(
            "Invalid attendance statuses found: "
            f"{invalid_status}"
        )


def validate_enrollments(conn):
    print("Validating enrollments...")

    invalid_students = conn.execute(
        """
        SELECT DISTINCT e.student_id
        FROM enrollments e
        LEFT JOIN students s
          ON s.id=e.student_id
        WHERE s.id IS NULL
        """
    ).fetchall()

    if invalid_students:
        raise RuntimeError(
            "Enrollments reference unknown students: "
            f"{invalid_students}"
        )

    invalid_courses = conn.execute(
        """
        SELECT DISTINCT e.course_id
        FROM enrollments e
        LEFT JOIN courses c
          ON c.id=e.course_id
        WHERE c.id IS NULL
        """
    ).fetchall()

    if invalid_courses:
        raise RuntimeError(
            "Enrollments reference unknown courses: "
            f"{invalid_courses}"
        )


def validate_schedule_changes(conn):
    print("Validating schedule changes...")

    invalid_items = conn.execute(
        """
        SELECT DISTINCT sc.item_id
        FROM schedule_changes sc
        LEFT JOIN schedule_items si
          ON si.id=sc.item_id
        WHERE si.id IS NULL
        """
    ).fetchall()

    if invalid_items:
        raise RuntimeError(
            "Schedule changes reference unknown items: "
            f"{invalid_items}"
        )

    duplicate_changes = conn.execute(
        """
        SELECT item_id, on_date, COUNT(*)
        FROM schedule_changes
        GROUP BY item_id, on_date
        HAVING COUNT(*) > 1
        """
    ).fetchall()

    if duplicate_changes:
        raise RuntimeError(
            "Duplicate schedule changes found: "
            f"{duplicate_changes}"
        )

    invalid_status = conn.execute(
        """
        SELECT DISTINCT status
        FROM schedule_changes
        WHERE status NOT IN ('cancelled', 'rescheduled')
        """
    ).fetchall()

    if invalid_status:
        raise RuntimeError(
            "Invalid schedule change status values: "
            f"{invalid_status}"
        )


def validate_courses_and_lecturers(conn):
    print("Validating courses and lecturers...")

    invalid_courses = conn.execute(
        """
        SELECT DISTINCT c.lecturer_id
        FROM courses c
        LEFT JOIN lecturers l
          ON l.id=c.lecturer_id
        WHERE l.id IS NULL
        """
    ).fetchall()

    if invalid_courses:
        raise RuntimeError(
            "Courses reference unknown lecturers: "
            f"{invalid_courses}"
        )

    invalid_schedule_courses = conn.execute(
        """
        SELECT DISTINCT si.course_id
        FROM schedule_items si
        LEFT JOIN courses c
          ON c.id=si.course_id
        WHERE si.course_id IS NOT NULL
          AND c.id IS NULL
        """
    ).fetchall()

    if invalid_schedule_courses:
        raise RuntimeError(
            "Schedule items reference unknown courses: "
            f"{invalid_schedule_courses}"
        )


def validate_syllabus(conn):
    print("Validating syllabus...")

    invalid_units = conn.execute(
        """
        SELECT DISTINCT su.course_id
        FROM syllabus_units su
        LEFT JOIN courses c
          ON c.id=su.course_id
        WHERE c.id IS NULL
        """
    ).fetchall()

    if invalid_units:
        raise RuntimeError(
            "Syllabus units reference unknown courses: "
            f"{invalid_units}"
        )

    invalid_topics = conn.execute(
        """
        SELECT DISTINCT st.unit_id
        FROM syllabus_topics st
        LEFT JOIN syllabus_units su
          ON su.id=st.unit_id
        WHERE su.id IS NULL
        """
    ).fetchall()

    if invalid_topics:
        raise RuntimeError(
            "Syllabus topics reference unknown units: "
            f"{invalid_topics}"
        )


def validate_users(conn):
    print("Validating users...")

    invalid_users = conn.execute(
        """
        SELECT u.id, u.lecturer_id
        FROM users u
        LEFT JOIN lecturers l
          ON l.id=u.lecturer_id
        WHERE l.id IS NULL
        """
    ).fetchall()

    if invalid_users:
        raise RuntimeError(
            "Users reference unknown lecturers: "
            f"{invalid_users}"
        )


def main(db_path: str | Path | None = None):
    selected = db_path or os.getenv("PROFPILOT_DB_PATH") or DEFAULT_DB
    db = Path(selected).expanduser().resolve()

    if not db.exists():
        raise SystemExit(f"Database not found: {db}")

    print(f"Migrating: {db}")

    conn = sqlite3.connect(db)
    conn.execute("PRAGMA foreign_keys=OFF")

    try:
        require_tables(conn)

        conn.execute("BEGIN")

        migrate_lecture_dates(conn)
        migrate_syllabus_positions(conn)
        migrate_syllabus_dates_and_completion(conn)
        migrate_schedule(conn)

        validate_courses_and_lecturers(conn)
        validate_syllabus(conn)
        validate_enrollments(conn)
        validate_attendance(conn)
        validate_schedule_changes(conn)
        validate_users(conn)

        conn.commit()

        print()
        print("Migration completed successfully.")
        print("Existing academic, attendance, schedule and user data was preserved.")

    except Exception:
        conn.rollback()
        print()
        print("Migration FAILED.")
        print("All migration changes were rolled back.")
        raise

    finally:
        conn.execute("PRAGMA foreign_keys=ON")
        conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Migrate an existing ProfPilot legacy SQLite database in place."
    )
    parser.add_argument(
        "--db",
        dest="db_path",
        help="Path to the legacy SQLite database to migrate. Overrides PROFPILOT_DB_PATH.",
    )
    args = parser.parse_args()
    main(args.db_path)
