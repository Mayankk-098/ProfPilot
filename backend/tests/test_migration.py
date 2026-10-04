"""Migration regression test using a small legacy-schema database copy."""
from __future__ import annotations

import sqlite3
from pathlib import Path

from migrate_schema import main as migrate


def make_legacy_db(path: Path) -> None:
    conn = sqlite3.connect(path)
    conn.executescript(
        """
        CREATE TABLE academic_events (id INTEGER PRIMARY KEY, lecturer_id TEXT, course_id TEXT, event_type TEXT, title TEXT, summary TEXT, occurred_at TEXT);
        CREATE TABLE lecturers (id TEXT PRIMARY KEY, name TEXT, initials TEXT, title TEXT, department TEXT, email TEXT, experience INTEGER);
        CREATE TABLE users (id INTEGER PRIMARY KEY, email TEXT UNIQUE, password_hash TEXT, lecturer_id TEXT UNIQUE);
        CREATE TABLE courses (id TEXT PRIMARY KEY, code TEXT, name TEXT, short_name TEXT, section TEXT, start_date TEXT, planned_end_date TEXT, lecturer_id TEXT, progress REAL, planned_progress REAL, current_pace REAL, required_pace REAL, predicted_completion TEXT, planned_completion TEXT, total_students INTEGER, present_today INTEGER, absent_today INTEGER);
        CREATE TABLE lecture_logs (id TEXT PRIMARY KEY, date TEXT, duration INTEGER, description TEXT, course_id TEXT);
        CREATE TABLE syllabus_units (id TEXT PRIMARY KEY, name TEXT, progress REAL, course_id TEXT);
        CREATE TABLE syllabus_topics (id TEXT PRIMARY KEY, name TEXT, completed INTEGER, planned_date TEXT, unit_id TEXT);
        CREATE TABLE students (id TEXT PRIMARY KEY, roll_no TEXT UNIQUE, name TEXT, section TEXT);
        CREATE TABLE enrollments (student_id TEXT, course_id TEXT, PRIMARY KEY(student_id, course_id));
        CREATE TABLE attendance_records (id INTEGER PRIMARY KEY, student_id TEXT, course_id TEXT, class_date TEXT, status TEXT);
        CREATE TABLE schedule_items (id TEXT PRIMARY KEY, subject TEXT, code TEXT, batch TEXT, weekday INTEGER, time TEXT, period TEXT, room TEXT, item_type TEXT, course_id TEXT);
        CREATE TABLE schedule_changes (item_id TEXT, on_date TEXT, status TEXT, new_date TEXT, new_start_time TEXT, new_end_time TEXT, new_room TEXT, reason TEXT);
        INSERT INTO lecturers VALUES ('lecturer_001','Dr. Sharma','DS','Assistant Professor','CSE','sharma@university.edu',8);
        INSERT INTO users VALUES (1,'sharma@university.edu','hash','lecturer_001');
        INSERT INTO courses VALUES ('dbms','CSE-302','Database Management Systems','DBMS','CSE-B','2026-09-18','2026-12-03','lecturer_001',21.9,25.0,0.8,0.9,'7 December 2026','3 December 2026',1,1,0);
        INSERT INTO lecture_logs VALUES ('lecture_001','18 September 2026',50,'Legacy lecture','dbms');
        INSERT INTO syllabus_units VALUES ('u1','Unit 1',100.0,'dbms');
        INSERT INTO syllabus_topics VALUES ('t1','ER Model',1,'18 September 2026','u1');
        INSERT INTO students VALUES ('s1','24BCS001','Test Student','CSE-B');
        INSERT INTO enrollments VALUES ('s1','dbms');
        INSERT INTO attendance_records VALUES (1,'s1','dbms','18 September 2026','present');
        INSERT INTO schedule_items VALUES ('dbms-mon','DBMS','CSE-302','CSE-B',0,'10:00','AM','Room 1','class','dbms');
        INSERT INTO schedule_changes VALUES ('dbms-mon','2026-10-05','cancelled',NULL,NULL,NULL,NULL,'test');
        """
    )
    conn.commit()
    conn.close()


def test_migration_preserves_data_and_normalises_legacy_fields(tmp_path):
    db = tmp_path / "legacy.db"
    make_legacy_db(db)
    migrate(db)

    conn = sqlite3.connect(db)
    assert conn.execute("SELECT lecture_date FROM lecture_logs WHERE id='lecture_001'").fetchone()[0] == "2026-09-18"
    assert conn.execute("SELECT planned_date FROM syllabus_topics WHERE id='t1'").fetchone()[0] == "2026-09-18"
    assert conn.execute(
        "SELECT legacy_completed FROM syllabus_topics WHERE id='t1'"
    ).fetchone()[0] == 1

    assert conn.execute(
        "SELECT covered_in_lecture_id FROM syllabus_topics WHERE id='t1'"
    ).fetchone()[0] is None
    assert conn.execute("SELECT position FROM syllabus_units WHERE id='u1'").fetchone()[0] == 0
    assert conn.execute("SELECT position FROM syllabus_topics WHERE id='t1'").fetchone()[0] == 0
    start, end, lecturer = conn.execute(
        "SELECT start_time, end_time, lecturer_id FROM schedule_items WHERE id='dbms-mon'"
    ).fetchone()
    assert start == "10:00:00" and end == "11:00:00" and lecturer == "lecturer_001"
    assert conn.execute("SELECT COUNT(*) FROM attendance_records").fetchone()[0] == 1
    assert conn.execute("SELECT COUNT(*) FROM schedule_changes").fetchone()[0] == 1
    assert conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 1
    conn.close()
