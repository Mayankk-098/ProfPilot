"""Create or update one lecturer login from environment variables.

Required environment variables:
    PROFPILOT_USER_EMAIL
    PROFPILOT_USER_PASSWORD
    PROFPILOT_LECTURER_ID

Optional:
    PROFPILOT_DB_PATH (defaults to this script's profpilot.db, resolved absolutely)
"""
from __future__ import annotations

import os
import sqlite3
from pathlib import Path

import bcrypt
from dotenv import load_dotenv

load_dotenv()


def required(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise SystemExit(f"Missing required environment variable: {name}")
    return value


email = required("PROFPILOT_USER_EMAIL").strip().lower()
password = required("PROFPILOT_USER_PASSWORD")
lecturer_id = required("PROFPILOT_LECTURER_ID").strip()

db_path = Path(
    os.getenv("PROFPILOT_DB_PATH", Path(__file__).resolve().with_name("profpilot.db"))
).expanduser().resolve()

if not db_path.exists():
    raise SystemExit(f"Database not found: {db_path}")

password_hash = bcrypt.hashpw(
    password.encode("utf-8"),
    bcrypt.gensalt(),
).decode("utf-8")

with sqlite3.connect(db_path) as conn:
    lecturer = conn.execute(
        "SELECT 1 FROM lecturers WHERE id=?",
        (lecturer_id,),
    ).fetchone()
    if lecturer is None:
        raise SystemExit(f"Lecturer not found: {lecturer_id}")

    existing = conn.execute(
        "SELECT id, lecturer_id FROM users WHERE email=?",
        (email,),
    ).fetchone()

    if existing:
        if existing[1] != lecturer_id:
            raise SystemExit(
                f"User {email} already belongs to lecturer {existing[1]}; "
                f"refusing to move it to {lecturer_id}."
            )
        conn.execute(
            "UPDATE users SET password_hash=? WHERE id=?",
            (password_hash, existing[0]),
        )
        action = "updated"
    else:
        other = conn.execute(
            "SELECT email FROM users WHERE lecturer_id=?",
            (lecturer_id,),
        ).fetchone()
        if other:
            raise SystemExit(
                f"Lecturer {lecturer_id} already has user {other[0]}; "
                "refusing to create a second account."
            )
        conn.execute(
            "INSERT INTO users (email, password_hash, lecturer_id) VALUES (?, ?, ?)",
            (email, password_hash, lecturer_id),
        )
        action = "created"

print(f"User {action}: {email} -> {lecturer_id}")
print(f"Database: {db_path}")
