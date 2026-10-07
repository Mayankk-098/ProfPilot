"""ProfPilot demo seed.

Uses real date/time fields and derived academic state while preserving
the project's original DBMS + AI syllabus definitions.

Run from backend:
    python -m seed.seed_demo
"""

import random
from datetime import date, datetime, time, timedelta

from sqlalchemy import inspect

from app import models  # noqa: F401
from app.database.db import Base, SessionLocal, engine
from app.models.academic import (
    Course,
    LectureLog,
    Lecturer,
    ScheduleItem,
    SyllabusTopic,
    SyllabusUnit,
    User,
)
from app.models.attendance import AttendanceRecord, Enrollment, Student


FIRST_NAMES = [
    "Aarav", "Vivaan", "Aditya", "Ishaan", "Rohan",
    "Kabir", "Arjun", "Dev", "Ananya", "Diya",
    "Isha", "Kavya", "Meera", "Nisha", "Priya",
    "Riya", "Saanvi", "Tanvi", "Neha", "Pooja",
]

LAST_NAMES = [
    "Sharma", "Verma", "Gupta", "Singh", "Mehta",
    "Jain", "Kapoor", "Reddy", "Nair", "Iyer",
    "Das", "Bose", "Khan", "Malhotra", "Chopra",
]


def last_class_dates(
    weekdays: set[int],
    count: int,
    before: date,
) -> list[date]:
    """Return the latest class dates, oldest first."""
    result = []
    current = before - timedelta(days=1)

    while len(result) < count:
        if current.weekday() in weekdays:
            result.append(current)
        current -= timedelta(days=1)

    return sorted(result)


def make_students(
    db,
    prefix: str,
    section: str,
    count: int,
    lecturer_id: str,
) -> list[Student]:
    students = []

    for i in range(1, count + 1):
        roll = f"{prefix}{i:03d}"

        students.append(
            Student(
                id=f"stu_{roll}",
                roll_no=roll,
                name=(
                    f"{FIRST_NAMES[(i * 7) % len(FIRST_NAMES)]} "
                    f"{LAST_NAMES[(i * 11) % len(LAST_NAMES)]}"
                ),
                section=section,
                lecturer_id=lecturer_id,
            )
        )

    db.add_all(students)
    return students


def seed_course(
    db,
    *,
    today: date,
    course_id: str,
    code: str,
    name: str,
    short_name: str,
    section: str,
    lecturer_id: str,
    weekdays: set[int],
    class_time: time,
    room: str,
    units: list[tuple[str, list[str]]],
    lectures: list[tuple[str, int, list[int]]],
    students: list[Student],
    planned_weeks_left: int,
    absences: dict[str, list[int]],
    excused: dict[str, list[int]] | None = None,
    rng: random.Random,
):
    """Create one course with lectures, syllabus, schedule and attendance."""

    excused = excused or {}

    lecture_dates = last_class_dates(
        weekdays,
        len(lectures),
        today,
    )

    start_date = lecture_dates[0]
    planned_end = today + timedelta(weeks=planned_weeks_left)

    course = Course(
        id=course_id,
        code=code,
        name=name,
        short_name=short_name,
        section=section,
        start_date=start_date,
        planned_end_date=planned_end,
        lecturer_id=lecturer_id,
    )

    db.add(course)
    db.flush()

    # ------------------------------------------------------------
    # Lecture history
    # ------------------------------------------------------------

    lecture_ids = []

    for index, ((description, duration, _), lecture_date) in enumerate(
        zip(lectures, lecture_dates),
        start=1,
    ):
        lecture_id = f"{course_id}-lecture-{index:03d}"

        lecture_ids.append(lecture_id)

        db.add(
            LectureLog(
                id=lecture_id,
                lecture_date=lecture_date,
                duration=duration,
                description=description,
                course_id=course_id,
            )
        )

    db.flush()

    # ------------------------------------------------------------
    # Syllabus
    # ------------------------------------------------------------

    # Mapping: topic index -> lecture ID
    covered_by = {}

    for lecture_index, (_, _, topic_indexes) in enumerate(lectures):
        for topic_index in topic_indexes:
            covered_by[topic_index] = lecture_ids[lecture_index]

    total_topics = sum(
        len(topic_names)
        for _, topic_names in units
    )

    plan_span = max(
        1,
        (planned_end - timedelta(days=7) - start_date).days,
    )

    topic_index = 0

    for unit_position, (unit_name, topic_names) in enumerate(
        units,
        start=1,
    ):
        unit_id = f"{course_id}-u{unit_position}"

        db.add(
            SyllabusUnit(
                id=unit_id,
                name=unit_name,
                position=unit_position,
                course_id=course_id,
            )
        )

        db.flush()

        for topic_position, topic_name in enumerate(
            topic_names,
            start=1,
        ):
            planned_date = (
                start_date
                + timedelta(
                    days=round(
                        topic_index * plan_span / total_topics
                    )
                )
            )

            db.add(
                SyllabusTopic(
                    id=f"{course_id}-t{topic_index + 1}",
                    name=topic_name,
                    position=topic_position,
                    planned_date=planned_date,
                    covered_in_lecture_id=covered_by.get(
                        topic_index
                    ),
                    unit_id=unit_id,
                )
            )

            topic_index += 1

    db.flush()

    # ------------------------------------------------------------
    # Enrollment + attendance
    # ------------------------------------------------------------

    session_count = len(lecture_dates)

    for student in students:
        db.add(
            Enrollment(
                student_id=student.id,
                course_id=course_id,
            )
        )

        if student.roll_no in absences:
            absent_indexes = set(
                absences[student.roll_no]
            )
        else:
            # Keep ordinary students at >= 75%.
            max_absences = session_count // 4

            if max_absences == 0:
                absent_indexes = set()
            else:
                possible_counts = list(
                    range(max_absences + 1)
                )

                weights = [
                    55,
                    30,
                    15,
                ][: len(possible_counts)]

                absence_count = rng.choices(
                    possible_counts,
                    weights=weights,
                    k=1,
                )[0]

                absent_indexes = set(
                    rng.sample(
                        range(session_count),
                        absence_count,
                    )
                )

        excused_indexes = set(
            excused.get(student.roll_no, [])
        )

        for session_index, class_date in enumerate(
            lecture_dates
        ):
            if session_index in excused_indexes:
                status = "excused"
            elif session_index in absent_indexes:
                status = "absent"
            else:
                status = "present"

            db.add(
                AttendanceRecord(
                    student_id=student.id,
                    course_id=course_id,
                    class_date=class_date,
                    status=status,
                )
            )

    # ------------------------------------------------------------
    # Weekly timetable
    # ------------------------------------------------------------

    day_names = {
        0: "mon",
        1: "tue",
        2: "wed",
        3: "thu",
        4: "fri",
        5: "sat",
        6: "sun",
    }

    end_time = (
        datetime.combine(
            date.min,
            class_time,
        )
        + timedelta(hours=1)
    ).time()

    for weekday in sorted(weekdays):
        db.add(
            ScheduleItem(
                id=f"{course_id}-{day_names[weekday]}",
                subject=name,
                code=code,
                batch=section,
                weekday=weekday,
                start_time=class_time,
                end_time=end_time,
                room=room,
                item_type="class",
                lecturer_id=lecturer_id,
                course_id=course_id,
            )
        )

    db.flush()


def populate(
    db,
    today: date | None = None,
) -> None:
    """Populate the complete deterministic ProfPilot demo state."""

    today = today or date.today()

    rng = random.Random(42)

    # ------------------------------------------------------------
    # Lecturers
    # ------------------------------------------------------------

    db.add_all(
        [
            Lecturer(
                id="lecturer_001",
                name="Dr. Sharma",
                initials="DS",
                title="Assistant Professor",
                department="Computer Science & Engineering",
                email="sharma@university.edu",
                experience=8,
            ),
            Lecturer(
                id="lecturer_002",
                name="Dr. Verma",
                initials="DV",
                title="Associate Professor",
                department="Computer Science & Engineering",
                email="verma@university.edu",
                experience=12,
            ),
        ]
    )

    db.flush()

    # ------------------------------------------------------------
    # Students
    # ------------------------------------------------------------

    dbms_students = make_students(
        db,
        "24BCS",
        "CSE-B",
        62,
        "lecturer_001",
    )

    ai_students = make_students(
        db,
        "24ACS",
        "CSE-A",
        58,
        "lecturer_001",
    )

    os_students = make_students(
        db,
        "24OCS",
        "CSE-C",
        10,
        "lecturer_002",
    )

    db.flush()

    # ============================================================
    # DBMS
    # ============================================================

    seed_course(
        db,
        today=today,
        rng=rng,
        course_id="dbms",
        code="CSE-302",
        name="Database Management Systems",
        short_name="DBMS",
        section="CSE-B",
        lecturer_id="lecturer_001",
        weekdays={0, 2, 4},
        class_time=time(10, 0),
        room="Block C · Room 204",
        units=[
            (
                "Unit 1 — Database Fundamentals",
                [
                    "ER Model",
                    "Relational Model",
                    "SQL",
                ],
            ),
            (
                "Unit 2 — Database Design",
                [
                    "Functional Dependencies",
                    "Normalization",
                    "2NF",
                    "3NF",
                    "BCNF",
                ],
            ),
            (
                "Unit 3 — Indexing & Storage",
                [
                    "Indexing",
                    "B Trees",
                    "B+ Trees",
                ],
            ),
        ],
        lectures=[
            (
                "Covered ER model and ER diagrams.",
                52,
                [0],
            ),
            (
                "Introduced relational models and schemas.",
                55,
                [1],
            ),
            (
                "Covered SQL fundamentals and queries.",
                50,
                [2],
            ),
            (
                "Covered functional dependencies.",
                54,
                [3],
            ),
            (
                "Covered normalization.",
                51,
                [4],
            ),
            (
                "Covered 2NF.",
                52,
                [5],
            ),
            (
                "Covered 3NF.",
                54,
                [6],
            ),
            (
                "Revision of normalization and database design.",
                50,
                [],
            ),
        ],
        students=dbms_students,
        planned_weeks_left=9,
        absences={
            # 4/7 = flagged
            "24BCS018": [1, 4, 6],
            # 3/7 = flagged
            "24BCS031": [0, 2, 3],
            # 75% exactly when 4/??; this student is 5/7 here
            "24BCS047": [2, 5],
            "24BCS052": [3],
            "24BCS009": [],
        },
        excused={
            "24BCS009": [4],
        },
    )

    # ============================================================
    # AI
    # ============================================================

    seed_course(
        db,
        today=today,
        rng=rng,
        course_id="ai",
        code="CSE-304",
        name="Artificial Intelligence",
        short_name="AI",
        section="CSE-A",
        lecturer_id="lecturer_001",
        weekdays={0, 2, 3},
        class_time=time(12, 0),
        room="Block B · Room 108",
        units=[
            (
                "Unit 1 — AI Fundamentals",
                [
                    "Introduction to Artificial Intelligence",
                    "Intelligent Agents",
                    "Problem Formulation",
                ],
            ),
            (
                "Unit 2 — Search & Problem Solving",
                [
                    "Uninformed Search",
                    "Breadth First Search",
                    "Depth First Search",
                    "Heuristic Search",
                    "A* Search",
                ],
            ),
            (
                "Unit 3 — Knowledge & Reasoning",
                [
                    "Knowledge Representation",
                    "Propositional Logic",
                    "Predicate Logic",
                    "Inference",
                    "Resolution",
                    "Planning",
                    "Uncertainty in AI",
                ],
            ),
        ],
        lectures=[
            (
                "Introduction to AI and intelligent agents.",
                50,
                [0, 1],
            ),
            (
                "Problem formulation and search basics.",
                52,
                [2, 3],
            ),
            (
                "Breadth first and depth first search.",
                48,
                [4, 5],
            ),
            (
                "Heuristic search and A*.",
                51,
                [6, 7],
            ),
            (
                "Knowledge representation and logic.",
                53,
                [8, 9],
            ),
        ],
        students=ai_students,
        planned_weeks_left=8,
        absences={
            "24ACS007": [0, 1, 4],
            "24ACS022": [2, 3, 4],
        },
    )

    # ============================================================
    # Operating Systems — second lecturer
    # ============================================================

    seed_course(
        db,
        today=today,
        rng=rng,
        course_id="os",
        code="CSE-306",
        name="Operating Systems",
        short_name="OS",
        section="CSE-C",
        lecturer_id="lecturer_002",
        weekdays={1, 4},
        class_time=time(11, 0),
        room="Block A · Room 301",
        units=[
            (
                "Unit 1 — Processes",
                [
                    "Processes",
                    "Threads",
                    "Scheduling",
                    "Synchronization",
                ],
            ),
        ],
        lectures=[
            (
                "Process model.",
                50,
                [0],
            ),
            (
                "Threads and concurrency.",
                50,
                [1],
            ),
        ],
        students=os_students,
        planned_weeks_left=8,
        absences={},
    )

    # ============================================================
    # Faculty meeting
    # ============================================================

    db.add(
        ScheduleItem(
            id="meeting-faculty-fri",
            subject="Faculty Meeting",
            code=None,
            batch="Faculty",
            weekday=4,
            start_time=time(15, 0),
            end_time=time(16, 0),
            room="Admin Block",
            item_type="meeting",
            lecturer_id="lecturer_001",
            course_id=None,
        )
    )

    db.commit()


def main() -> None:
    """Recreate demo academic data while preserving memory and users."""

    preserved_users = []

    inspector = inspect(engine)

    if inspector.has_table("users"):
        existing = SessionLocal()

        try:
            preserved_users = [
                (
                    user.email,
                    user.password_hash,
                    user.lecturer_id,
                )
                for user in existing.query(User).all()
            ]
        finally:
            existing.close()

    # AI memory should survive reseeding.
    keep_tables = {"academic_events"}

    drop_tables = [
        table
        for table in reversed(Base.metadata.sorted_tables)
        if table.name not in keep_tables
    ]

    Base.metadata.drop_all(
        bind=engine,
        tables=drop_tables,
    )

    Base.metadata.create_all(
        bind=engine,
    )

    db = SessionLocal()

    try:
        populate(db)

        for email, password_hash, lecturer_id in preserved_users:
            lecturer = (
                db.query(Lecturer)
                .filter(
                    Lecturer.id == lecturer_id
                )
                .first()
            )

            if lecturer is not None:
                db.add(
                    User(
                        email=email,
                        password_hash=password_hash,
                        lecturer_id=lecturer_id,
                    )
                )

        db.commit()

    finally:
        db.close()

    print(
        "ProfPilot demo database created successfully."
    )


if __name__ == "__main__":
    main()
