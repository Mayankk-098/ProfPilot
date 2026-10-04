from app.database.db import Base, SessionLocal, engine
from app.models.academic import (
    Lecturer,
    Course,
    SyllabusUnit,
    SyllabusTopic,
    LectureLog,
    ScheduleItem,
)


Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

db = SessionLocal()


# ============================
# LECTURER
# ============================

lecturer = Lecturer(
    id="lecturer_001",
    name="Dr. Sharma",
    initials="DS",
    title="Assistant Professor",
    department="Computer Science & Engineering",
    email="sharma@university.edu",
    experience=8,
)

db.add(lecturer)


# ============================
# DBMS
# ============================

dbms = Course(
    id="dbms",
    code="CSE-302",
    name="Database Management Systems",
    short_name="DBMS",
    section="CSE-B",

    # These are retained as seed/demo metadata.
    # Academic intelligence derives topic progress from
    # syllabus topics and lecture evidence.
    progress=68,
    planned_progress=74,

    current_pace=0.62,
    required_pace=0.71,

    predicted_completion="7 December 2026",
    planned_completion="3 December 2026",

    total_students=62,
    present_today=56,
    absent_today=6,

    lecturer_id="lecturer_001",
)

db.add(dbms)


unit1 = SyllabusUnit(
    id="dbms-u1",
    name="Unit 1 — Database Fundamentals",
    progress=100,
    course_id="dbms",
)

unit2 = SyllabusUnit(
    id="dbms-u2",
    name="Unit 2 — Database Design",
    progress=72,
    course_id="dbms",
)

unit3 = SyllabusUnit(
    id="dbms-u3",
    name="Unit 3 — Indexing & Storage",
    progress=0,
    course_id="dbms",
)

db.add_all([unit1, unit2, unit3])


topics = [
    SyllabusTopic(
        id="dbms-t1",
        name="ER Model",
        completed=True,
        unit_id="dbms-u1",
    ),
    SyllabusTopic(
        id="dbms-t2",
        name="Relational Model",
        completed=True,
        unit_id="dbms-u1",
    ),
    SyllabusTopic(
        id="dbms-t3",
        name="SQL",
        completed=True,
        unit_id="dbms-u1",
    ),
    SyllabusTopic(
        id="dbms-t4",
        name="Functional Dependencies",
        completed=True,
        unit_id="dbms-u2",
    ),
    SyllabusTopic(
        id="dbms-t5",
        name="Normalization",
        completed=True,
        unit_id="dbms-u2",
    ),
    SyllabusTopic(
        id="dbms-t6",
        name="2NF",
        completed=True,
        unit_id="dbms-u2",
    ),
    SyllabusTopic(
        id="dbms-t7",
        name="3NF",
        completed=True,
        unit_id="dbms-u2",
    ),
    SyllabusTopic(
        id="dbms-t8",
        name="BCNF",
        completed=False,
        unit_id="dbms-u2",
    ),
    SyllabusTopic(
        id="dbms-t9",
        name="Indexing",
        completed=False,
        unit_id="dbms-u3",
    ),
    SyllabusTopic(
        id="dbms-t10",
        name="B Trees",
        completed=False,
        unit_id="dbms-u3",
    ),
    SyllabusTopic(
        id="dbms-t11",
        name="B+ Trees",
        completed=False,
        unit_id="dbms-u3",
    ),
]

db.add_all(topics)


# ============================
# LECTURE HISTORY
# ============================
#
# Lecture dates use ISO-8601 date format:
# YYYY-MM-DD
#
# Keep this format consistent with lectures created
# by the action/AI layer.
# ============================

lectures = [
    LectureLog(
        id="lecture_001",
        date="2026-09-18",
        duration=52,
        description="Covered ER model and ER diagrams.",
        course_id="dbms",
    ),
    LectureLog(
        id="lecture_002",
        date="2026-09-20",
        duration=55,
        description="Introduced relational models and schemas.",
        course_id="dbms",
    ),
    LectureLog(
        id="lecture_003",
        date="2026-09-22",
        duration=50,
        description="Covered SQL fundamentals and queries.",
        course_id="dbms",
    ),
    LectureLog(
        id="lecture_004",
        date="2026-09-24",
        duration=54,
        description="Covered functional dependencies.",
        course_id="dbms",
    ),
    LectureLog(
        id="lecture_005",
        date="2026-09-26",
        duration=51,
        description="Covered normalization, 2NF and 3NF.",
        course_id="dbms",
    ),
]

db.add_all(lectures)


# ============================
# ARTIFICIAL INTELLIGENCE
# ============================

ai_course = Course(
    id="ai",
    code="CSE-304",
    name="Artificial Intelligence",
    short_name="AI",
    section="CSE-A",

    progress=73,
    planned_progress=71,

    current_pace=0.74,
    required_pace=0.68,

    predicted_completion="1 December 2026",
    planned_completion="4 December 2026",

    total_students=58,
    present_today=53,
    absent_today=5,

    lecturer_id="lecturer_001",
)

db.add(ai_course)
# ============================
# AI SYLLABUS
# ============================

ai_unit1 = SyllabusUnit(
    id="ai-u1",
    name="Unit 1 — AI Fundamentals",
    progress=100,
    course_id="ai",
)

ai_unit2 = SyllabusUnit(
    id="ai-u2",
    name="Unit 2 — Search & Problem Solving",
    progress=100,
    course_id="ai",
)

ai_unit3 = SyllabusUnit(
    id="ai-u3",
    name="Unit 3 — Knowledge & Reasoning",
    progress=60,
    course_id="ai",
)

db.add_all([
    ai_unit1,
    ai_unit2,
    ai_unit3,
])


ai_topics = [
    SyllabusTopic(
        id="ai-t1",
        name="Introduction to Artificial Intelligence",
        completed=True,
        unit_id="ai-u1",
    ),
    SyllabusTopic(
        id="ai-t2",
        name="Intelligent Agents",
        completed=True,
        unit_id="ai-u1",
    ),
    SyllabusTopic(
        id="ai-t3",
        name="Problem Formulation",
        completed=True,
        unit_id="ai-u1",
    ),
    SyllabusTopic(
        id="ai-t4",
        name="Uninformed Search",
        completed=True,
        unit_id="ai-u2",
    ),
    SyllabusTopic(
        id="ai-t5",
        name="Breadth First Search",
        completed=True,
        unit_id="ai-u2",
    ),
    SyllabusTopic(
        id="ai-t6",
        name="Depth First Search",
        completed=True,
        unit_id="ai-u2",
    ),
    SyllabusTopic(
        id="ai-t7",
        name="Heuristic Search",
        completed=True,
        unit_id="ai-u2",
    ),
    SyllabusTopic(
        id="ai-t8",
        name="A* Search",
        completed=True,
        unit_id="ai-u2",
    ),
    SyllabusTopic(
        id="ai-t9",
        name="Knowledge Representation",
        completed=True,
        unit_id="ai-u3",
    ),
    SyllabusTopic(
        id="ai-t10",
        name="Propositional Logic",
        completed=True,
        unit_id="ai-u3",
    ),
    SyllabusTopic(
        id="ai-t11",
        name="Predicate Logic",
        completed=True,
        unit_id="ai-u3",
    ),
    SyllabusTopic(
        id="ai-t12",
        name="Inference",
        completed=False,
        unit_id="ai-u3",
    ),
    SyllabusTopic(
        id="ai-t13",
        name="Resolution",
        completed=False,
        unit_id="ai-u3",
    ),
    SyllabusTopic(
        id="ai-t14",
        name="Planning",
        completed=False,
        unit_id="ai-u3",
    ),
    SyllabusTopic(
        id="ai-t15",
        name="Uncertainty in AI",
        completed=False,
        unit_id="ai-u3",
    ),
]

db.add_all(ai_topics)

# ============================
# TIMETABLE
# ============================

schedule = [
    ScheduleItem(
        id="class_001",
        subject="Database Management Systems",
        code="CSE-302",
        batch="CSE-B",
        time="10:00",
        period="AM",
        room="Block C · Room 204",
        item_type="class",
        course_id="dbms",
    ),
    ScheduleItem(
        id="class_002",
        subject="Artificial Intelligence",
        code="CSE-304",
        batch="CSE-A",
        time="12:00",
        period="PM",
        room="Block B · Room 108",
        item_type="class",
        course_id="ai",
    ),
    ScheduleItem(
        id="meeting_001",
        subject="Faculty Meeting",
        code=None,
        batch="Faculty",
        time="03:00",
        period="PM",
        room="Admin Block",
        item_type="meeting",
    ),
]

db.add_all(schedule)


db.commit()
db.close()

print("ProfPilot demo database created successfully.")
