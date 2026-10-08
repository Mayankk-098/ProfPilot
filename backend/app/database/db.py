from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

BASE_DIR = Path(__file__).resolve().parents[2]
DATABASE_PATH = BASE_DIR / "profpilot.db"

DATABASE_URL = f"sqlite:///{DATABASE_PATH.as_posix()}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


class Base(DeclarativeBase):
    pass


def ensure_schema(bind=None) -> None:
    """Additive SQLite patches for existing local prototype databases."""
    target = bind or engine
    if target.dialect.name != "sqlite":
        return

    with target.begin() as conn:
        tables = {
            row[0]
            for row in conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table'")
            )
        }
        if "students" not in tables:
            return

        columns = {
            row[1]
            for row in conn.execute(text("PRAGMA table_info(students)"))
        }
        if "lecturer_id" not in columns:
            conn.execute(
                text("ALTER TABLE students ADD COLUMN lecturer_id VARCHAR(50)")
            )
            conn.execute(
                text(
                    """
                    UPDATE students
                    SET lecturer_id = (
                        SELECT courses.lecturer_id
                        FROM enrollments
                        JOIN courses ON courses.id = enrollments.course_id
                        WHERE enrollments.student_id = students.id
                        LIMIT 1
                    )
                    WHERE lecturer_id IS NULL
                    """
                )
            )

        if "email" not in columns:
            conn.execute(
                text("ALTER TABLE students ADD COLUMN email VARCHAR(254)")
            )


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()