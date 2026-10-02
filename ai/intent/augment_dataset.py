from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

DATASET_PATH = ROOT / "data" / "intent" / "examples_marked.tsv"
BACKUP_PATH = ROOT / "data" / "intent" / "examples_marked.before_augmentation.tsv"


# -------------------------------------------------------------------
# Each template is:
#   (language, marked_text)
#
# Every generated example gets:
#   split   = train
#   source  = synthetic
#   group   = unique augmentation group
# -------------------------------------------------------------------

AUGMENTATIONS = {
    "query_course_completion": [
        ("en", "what is the expected completion date for [[DBMS|COURSE]]"),
        ("en", "when do you think I will be done with [[AI|COURSE]]"),
        ("en", "how many classes until I finish [[DBMS|COURSE]]"),
        ("en", "when should the [[Computer Networks|COURSE]] syllabus be completed"),
        ("en", "can I finish [[AI|COURSE]] within the planned schedule"),
        ("en", "how much of the timeline is left for [[DBMS|COURSE]]"),
        ("en", "what is the estimated date for completing [[AI|COURSE]]"),
        ("hinglish", "[[DBMS|COURSE]] kab tak pura ho jayega"),
        ("hinglish", "[[AI|COURSE]] kitne din mein complete hoga"),
        ("hinglish", "mera [[DBMS|COURSE]] kab tak khatam hoga"),
    ],

    "what_if_schedule_change": [
        ("en", "what happens if I cancel tomorrow's [[DBMS|COURSE]] lecture"),
        ("en", "how will missing a class affect my [[AI|COURSE]] timeline"),
        ("en", "what if I postpone the next [[DBMS|COURSE]] class"),
        ("en", "how much will my syllabus slip if I miss [[Monday|DATE]]'s class"),
        ("en", "what if I take one additional [[AI|COURSE]] lecture this week"),
        ("en", "what happens to my completion date if I skip [[Friday|DATE]]"),
        ("en", "how would cancelling two lectures affect my course progress"),
        ("hinglish", "agar [[Monday|DATE]] ki class miss karu to kya hoga"),
        ("hinglish", "agar [[AI|COURSE]] ki ek extra class lu to syllabus par kya effect hoga"),
        ("hinglish", "kal class cancel karne se [[DBMS|COURSE]] kitna delay hoga"),
    ],

    "query_next_class": [
        ("en", "what lecture am I teaching next"),
        ("en", "tell me the next class on my timetable"),
        ("en", "which lecture is scheduled after this one"),
        ("en", "what is the next class I need to attend"),
        ("en", "when is my upcoming lecture"),
        ("en", "show me my next teaching slot"),
        ("en", "which course do I teach next"),
        ("hinglish", "meri agli class kab hai"),
        ("hinglish", "ab meri next lecture kaunsi hai"),
        ("hinglish", "agli baar kya padhana hai"),
    ],

    "query_last_lecture": [
        ("en", "what did I teach during my previous lecture"),
        ("en", "which topic did I cover most recently"),
        ("en", "tell me what happened in my last [[DBMS|COURSE]] class"),
        ("en", "what was the subject of my latest [[AI|COURSE]] lecture"),
        ("en", "what did I explain in the previous class"),
        ("en", "which topic was taught in my last lecture"),
        ("en", "what did I cover in the class before this one"),
        ("hinglish", "meri last class mein kya padhaya tha"),
        ("hinglish", "pichli [[DBMS|COURSE]] lecture mein kya cover kiya"),
        ("hinglish", "last lecture mein kaunsa topic padha tha"),
    ],

    "query_course_status": [
        ("en", "what is the progress of [[DBMS|COURSE]] right now"),
        ("en", "show me how [[AI|COURSE]] is doing"),
        ("en", "is [[DBMS|COURSE]] keeping up with the plan"),
        ("en", "how much of the [[AI|COURSE]] syllabus is complete"),
        ("en", "what is my current teaching progress in [[DBMS|COURSE]]"),
        ("en", "is my [[Computer Networks|COURSE]] on schedule"),
        ("en", "give me the latest status of [[AI|COURSE]]"),
        ("hinglish", "[[DBMS|COURSE]] abhi kitna complete hua hai"),
        ("hinglish", "[[AI|COURSE]] ki current progress kya hai"),
        ("hinglish", "mera [[DBMS|COURSE]] plan ke according chal raha hai kya"),
    ],

    "query_attendance_low": [
        ("en", "show students whose attendance is below [[75%|THRESHOLD]]"),
        ("en", "which students are under the attendance limit"),
        ("en", "find the low attendance students in [[DBMS|COURSE]]"),
        ("en", "who is below the required attendance percentage"),
        ("en", "list students with attendance less than [[75%|THRESHOLD]]"),
        ("en", "which [[CSE-A|BATCH]] students have attendance shortage"),
        ("en", "tell me who needs to improve their attendance"),
        ("hinglish", "[[75%|THRESHOLD]] se neeche attendance kiski hai"),
        ("hinglish", "[[CSE-B|BATCH]] mein low attendance wale kaun hain"),
        ("hinglish", "kaunse students attendance mein short hain"),
    ],

    "query_memory_events": [
        ("en", "what academic events do you remember from [[DBMS|COURSE]]"),
        ("en", "show me recent things recorded for [[AI|COURSE]]"),
        ("en", "what do you remember about my recent classes"),
        ("en", "have there been any recent events in [[DBMS|COURSE]]"),
        ("en", "tell me what I recently recorded"),
        ("en", "show the latest academic memories for this course"),
        ("en", "what recent changes do you remember about [[AI|COURSE]]"),
        ("hinglish", "[[DBMS|COURSE]] ke recent events yaad hain kya"),
        ("hinglish", "recent classes mein kya hua tha"),
        ("hinglish", "ProfPilot ko meri recent teaching ke baare mein kya yaad hai"),
    ],

    "explain_delay": [
        ("en", "why has [[DBMS|COURSE]] fallen behind the plan"),
        ("en", "what is causing my syllabus to be delayed"),
        ("en", "why is my current course pace too slow"),
        ("en", "what caused the delay in [[AI|COURSE]]"),
        ("en", "why am I not keeping up with the teaching plan"),
        ("en", "what has made my syllabus progress slower"),
        ("en", "why is [[Computer Networks|COURSE]] behind schedule"),
        ("hinglish", "[[DBMS|COURSE]] plan se piche kyun hai"),
        ("hinglish", "syllabus mein delay kis wajah se hua"),
        ("hinglish", "meri course ki speed slow kyun ho gayi"),
    ],

    "cancel_class": [
        ("en", "please cancel tomorrow's [[DBMS|COURSE]] lecture"),
        ("en", "remove the [[AI|COURSE]] class scheduled for [[Friday|DATE]]"),
        ("en", "I need to call off the [[10:00 AM|TIME]] lecture"),
        ("en", "cancel the lecture for [[CSE-A|BATCH]]"),
        ("en", "please take tomorrow's class off my timetable"),
        ("en", "I cannot take the [[DBMS|COURSE]] lecture on [[Monday|DATE]]"),
        ("en", "call off today's [[AI|COURSE]] class"),
        ("hinglish", "[[DBMS|COURSE]] ki kal wali class cancel kar do"),
        ("hinglish", "[[Friday|DATE]] ki lecture hata do"),
        ("hinglish", "aaj ki [[AI|COURSE]] class cancel karni hai"),
    ],

    "reschedule_class": [
        ("en", "move the [[DBMS|COURSE]] class to [[2:00 PM|NEW_TIME]]"),
        ("en", "shift [[Monday|DATE]]'s lecture to [[Tuesday|NEW_DATE]]"),
        ("en", "change the [[10:00 AM|TIME]] class to [[1:00 PM|NEW_TIME]]"),
        ("en", "move the [[AI|COURSE]] lecture to [[Friday|NEW_DATE]]"),
        ("en", "reschedule the [[CSE-A|BATCH]] lecture for [[4:00 PM|NEW_TIME]]"),
        ("en", "can you shift tomorrow's [[DBMS|COURSE]] class to [[3:00 PM|NEW_TIME]]"),
        ("en", "move the lecture from [[Wednesday|DATE]] to [[Thursday|NEW_DATE]]"),
        ("hinglish", "[[DBMS|COURSE]] ki class [[2:00 PM|NEW_TIME]] par shift kar do"),
        ("hinglish", "[[Monday|DATE]] wali class [[Wednesday|NEW_DATE]] kar do"),
        ("hinglish", "[[AI|COURSE]] ka lecture [[Friday|NEW_DATE]] ko shift karo"),
    ],

    "notify_batch": [
        ("en", "send [[CSE-A|BATCH]] a message about tomorrow's class"),
        ("en", "notify [[CSE-B|BATCH]] about the lecture cancellation"),
        ("en", "tell the [[DBMS|COURSE]] students about the room change"),
        ("en", "send a reminder to [[CSE-A|BATCH]] for the quiz"),
        ("en", "inform [[CSE-B|BATCH]] about [[Friday|DATE]]'s lecture"),
        ("en", "announce the schedule change to the [[AI|COURSE]] students"),
        ("en", "let [[CSE-A|BATCH]] know that today's class is cancelled"),
        ("hinglish", "[[CSE-B|BATCH]] ko kal ki class ke baare mein message bhejo"),
        ("hinglish", "[[DBMS|COURSE]] ke students ko schedule change batao"),
        ("hinglish", "[[CSE-A|BATCH]] ko quiz ka reminder bhej do"),
    ],

    "log_lecture": [
        ("en", "log today's [[DBMS|COURSE]] lecture on [[Normalization|TOPIC]]"),
        ("en", "record that I taught [[Indexing|TOPIC]] in [[DBMS|COURSE]]"),
        ("en", "add a [[60 minutes|DURATION]] lecture for [[AI|COURSE]]"),
        ("en", "save today's lecture on [[Neural Networks|TOPIC]]"),
        ("en", "record [[45 minutes|DURATION]] for today's [[DBMS|COURSE]] class"),
        ("en", "mark [[Normalization|TOPIC]] as covered in [[DBMS|COURSE]]"),
        ("en", "add a lecture covering [[B+ Trees|TOPIC]]"),
        ("hinglish", "aaj [[DBMS|COURSE]] mein [[Normalization|TOPIC]] padhaya"),
        ("hinglish", "[[AI|COURSE]] ki [[60 minutes|DURATION]] class log karo"),
        ("hinglish", "[[Indexing|TOPIC]] wali lecture ko record kar do"),
    ],

    "out_of_scope": [
        ("en", "what is the capital of France"),
        ("en", "tell me a funny story"),
        ("en", "help me order a pizza"),
        ("en", "what is the weather in Mumbai"),
        ("en", "write me a poem about space"),
        ("en", "who won the football match last night"),
        ("en", "book a hotel for me"),
        ("hinglish", "mujhe ek joke suna do"),
        ("hinglish", "Delhi mein weather kaisa hai"),
        ("hinglish", "mere liye pizza order kar do"),
    ],
}


def load_existing_groups() -> set[str]:
    """Read existing group IDs to make augmentation rerun-safe."""
    groups: set[str] = set()

    with DATASET_PATH.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as file:
        reader = csv.reader(file, delimiter="\t")

        for row in reader:
            if not row or row[0].startswith("#"):
                continue

            if len(row) >= 2:
                groups.add(row[1])

    return groups


def validate_generated_row(row: list[str]) -> None:
    """Make sure every row has exactly six TSV columns."""
    if len(row) != 6:
        raise ValueError(
            f"Generated row has {len(row)} columns instead of 6:\n{row}"
        )

    split, group, source, lang, intent, marked_text = row

    if not all(
        [
            split,
            group,
            source,
            lang,
            intent,
            marked_text,
        ]
    ):
        raise ValueError(
            f"Generated row contains an empty field:\n{row}"
        )


def build_rows() -> list[list[str]]:
    """Build all new synthetic training rows."""
    rows: list[list[str]] = []

    for intent, templates in AUGMENTATIONS.items():
        for index, (lang, marked_text) in enumerate(
            templates,
            start=1,
        ):
            group = f"aug_{intent}_{index:02d}"

            row = [
                "train",
                group,
                "synthetic",
                lang,
                intent,
                marked_text,
            ]

            validate_generated_row(row)

            rows.append(row)

    return rows


def append_rows(rows: list[list[str]]) -> None:
    """
    Append generated rows while preserving the original TSV.

    A backup is created on the first run.
    """
    if not DATASET_PATH.exists():
        raise FileNotFoundError(
            f"Dataset not found: {DATASET_PATH}"
        )

    original_text = DATASET_PATH.read_text(
        encoding="utf-8"
    )

    if not BACKUP_PATH.exists():
        BACKUP_PATH.write_text(
            original_text,
            encoding="utf-8",
        )

    with DATASET_PATH.open(
        "a",
        encoding="utf-8",
        newline="",
    ) as file:
        writer = csv.writer(
            file,
            delimiter="\t",
            lineterminator="\n",
        )

        if not original_text.endswith("\n"):
            file.write("\n")

        writer.writerows(rows)


def main() -> None:
    existing_groups = load_existing_groups()

    all_rows = build_rows()

    rows_to_add = [
        row
        for row in all_rows
        if row[1] not in existing_groups
    ]

    if not rows_to_add:
        print("No new examples needed.")
        return

    append_rows(rows_to_add)

    print(
        f"Added {len(rows_to_add)} synthetic training examples."
    )

    print(
        f"Dataset backup created at:\n{BACKUP_PATH}"
    )


if __name__ == "__main__":
    main()