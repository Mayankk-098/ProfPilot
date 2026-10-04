from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from typing import Iterable, Optional


ATTENDANCE_THRESHOLD_PCT = 75


# ============================================================
# Attendance
# ============================================================

@dataclass(frozen=True)
class AttendanceSummary:
    attended: int
    total: int
    percentage: Optional[float]
    flagged: bool
    classes_needed_to_recover: int


def summarize_attendance(
    attended: int,
    total: int,
) -> AttendanceSummary:
    """total = present + absent.
    Excused classes are excluded by the caller.
    """

    if (
        total < 0
        or attended < 0
        or attended > total
    ):
        raise ValueError("invalid attendance counts")

    if total == 0:
        return AttendanceSummary(
            0,
            0,
            None,
            False,
            0,
        )

    # Strictly below 75%.
    flagged = (
        attended * 100
        < ATTENDANCE_THRESHOLD_PCT * total
    )

    # Smallest n such that:
    # (attended + n) / (total + n) >= 75%
    needed = max(
        0,
        3 * total - 4 * attended,
    )

    return AttendanceSummary(
        attended=attended,
        total=total,
        percentage=round(
            attended / total * 100,
            2,
        ),
        flagged=flagged,
        classes_needed_to_recover=needed,
    )


# ============================================================
# Schedule
# ============================================================

@dataclass(frozen=True)
class Slot:
    """Recurring weekly schedule slot."""

    id: str
    course_id: Optional[str]
    lecturer_id: str
    weekday: int
    start: time
    end: time


@dataclass(frozen=True)
class SlotChange:
    """One-off change to a recurring slot."""

    slot_id: str
    on_date: date
    cancelled: bool = False
    new_date: Optional[date] = None
    new_start: Optional[time] = None
    new_end: Optional[time] = None
    new_room: Optional[str] = None
    reason: Optional[str] = None


@dataclass(frozen=True)
class Occurrence:
    slot_id: str
    course_id: Optional[str]
    lecturer_id: str
    start: datetime
    end: datetime
    status: str = "scheduled"
    original_date: Optional[date] = None
    room: Optional[str] = None


def _normalise_slot(slot) -> Slot:
    """
    Convert either a pure Slot or the current ScheduleItem-shaped
    object into the pure Slot representation.
    """

    if isinstance(slot, Slot):
        return slot

    return Slot(
        id=slot.id,
        course_id=getattr(slot, "course_id", None),
        lecturer_id=slot.lecturer_id,
        weekday=slot.weekday,
        start=(
            getattr(slot, "start", None)
            or slot.start_time
        ),
        end=(
            getattr(slot, "end", None)
            or slot.end_time
        ),
    )


def _normalise_change(change) -> SlotChange:
    """
    Convert either a pure SlotChange or the current database
    ScheduleChange-shaped object into SlotChange.
    """

    if isinstance(change, SlotChange):
        return change

    return SlotChange(
        slot_id=change.item_id,
        on_date=change.on_date,
        cancelled=(
            change.status == "cancelled"
        ),
        new_date=change.new_date,
        new_start=getattr(
            change,
            "new_start_time",
            None,
        ),
        new_end=getattr(
            change,
            "new_end_time",
            None,
        ),
        new_room=getattr(
            change,
            "new_room",
            None,
        ),
        reason=getattr(
            change,
            "reason",
            None,
        ),
    )


def occurrences(
    slots: Iterable[Slot],
    changes: Iterable[SlotChange],
    from_date: date,
    days: int = 14,
    include_cancelled: bool = False,
) -> list[Occurrence]:
    """
    Expand recurring weekly slots into actual dated occurrences.

    Window:
        [from_date, from_date + days)

    Rules:
    - normal weekly occurrence -> scheduled
    - cancelled occurrence -> omitted unless include_cancelled=True
    - rescheduled occurrence -> removed from original date
    - rescheduled occurrence -> emitted on new date/time
    - results sorted by actual datetime
    """

    slots = [
        _normalise_slot(slot)
        for slot in slots
    ]

    changes = [
        _normalise_change(change)
        for change in changes
    ]

    by_id = {
        slot.id: slot
        for slot in slots
    }

    change_by_key = {
        (change.slot_id, change.on_date): change
        for change in changes
    }

    window_end = (
        from_date + timedelta(days=days)
    )

    out: list[Occurrence] = []

    # --------------------------------------------------------
    # Normal recurring occurrences
    # --------------------------------------------------------

    for i in range(days):
        current_date = (
            from_date + timedelta(days=i)
        )

        for slot in slots:
            if slot.weekday != current_date.weekday():
                continue

            change = change_by_key.get(
                (slot.id, current_date)
            )

            # Cancelled occurrence.
            if (
                change is not None
                and change.cancelled
            ):
                if include_cancelled:
                    out.append(
                        Occurrence(
                            slot.id,
                            slot.course_id,
                            slot.lecturer_id,
                            datetime.combine(
                                current_date,
                                slot.start,
                            ),
                            datetime.combine(
                                current_date,
                                slot.end,
                            ),
                            status="cancelled",
                            original_date=current_date,
                        )
                    )

                continue

            # Rescheduled away from original date.
            if (
                change is not None
                and change.new_date is not None
            ):
                continue

            out.append(
                Occurrence(
                    slot.id,
                    slot.course_id,
                    slot.lecturer_id,
                    datetime.combine(
                        current_date,
                        slot.start,
                    ),
                    datetime.combine(
                        current_date,
                        slot.end,
                    ),
                    status="scheduled",
                    original_date=None,
                )
            )

    # --------------------------------------------------------
    # Rescheduled occurrences
    # --------------------------------------------------------

    for (
        slot_id,
        original_date,
    ), change in change_by_key.items():

        if (
            change.cancelled
            or change.new_date is None
            or slot_id not in by_id
        ):
            continue

        if not (
            from_date
            <= change.new_date
            < window_end
        ):
            continue

        slot = by_id[slot_id]

        start_time = (
            change.new_start
            or slot.start
        )

        end_time = (
            change.new_end
            or slot.end
        )

        out.append(
            Occurrence(
                slot.id,
                slot.course_id,
                slot.lecturer_id,
                datetime.combine(
                    change.new_date,
                    start_time,
                ),
                datetime.combine(
                    change.new_date,
                    end_time,
                ),
                status="rescheduled",
                original_date=original_date,
                room=change.new_room,
            )
        )

    return sorted(
        out,
        key=lambda occurrence: (
            occurrence.start,
            occurrence.slot_id,
        ),
    )


def next_class(
    slots: Iterable[Slot],
    changes: Iterable[SlotChange],
    now: datetime,
    lecturer_id: Optional[str] = None,
    horizon_days: int = 60,
) -> Optional[Occurrence]:
    """
    Return the first non-cancelled occurrence after `now`.
    """

    slots = [
        _normalise_slot(slot)
        for slot in slots
    ]

    if lecturer_id is not None:
        slots = [
            slot
            for slot in slots
            if slot.lecturer_id == lecturer_id
        ]

    for occurrence in occurrences(
        slots,
        changes,
        now.date(),
        horizon_days,
    ):
        if occurrence.start > now:
            return occurrence

    return None


def times_overlap(
    a_start: datetime,
    a_end: datetime,
    b_start: datetime,
    b_end: datetime,
) -> bool:
    return (
        a_start < b_end
        and b_start < a_end
    )


# ============================================================
# Syllabus progress / pace
# ============================================================

def percent(
    done: int,
    total: int,
) -> float:
    return (
        round(done / total * 100, 1)
        if total
        else 0.0
    )


def planned_progress(
    planned_dates: list[Optional[date]],
    today: date,
) -> float:
    """
    Percentage of topics whose planned date has arrived.
    """

    done = sum(
        1
        for planned_date in planned_dates
        if (
            planned_date is not None
            and planned_date <= today
        )
    )

    return percent(
        done,
        len(planned_dates),
    )


def current_pace(
    completed_topics: int,
    lectures_held: int,
) -> float:
    """Topics completed per class held."""

    return (
        round(
            completed_topics / lectures_held,
            2,
        )
        if lectures_held
        else 0.0
    )


def required_pace(
    remaining_topics: int,
    remaining_classes: int,
) -> float:
    """
    Topics per class needed to finish by the
    planned end date.
    """

    if remaining_topics <= 0:
        return 0.0

    if remaining_classes <= 0:
        return float(remaining_topics)

    return round(
        remaining_topics / remaining_classes,
        2,
    )


def predict_completion(
    remaining_topics: int,
    pace: float,
    future_class_dates: list[date],
) -> Optional[date]:
    """
    Date of the class on which the syllabus finishes
    at the current pace.
    """

    if (
        remaining_topics <= 0
        or pace <= 0
    ):
        return None

    number_of_classes = math.ceil(
        remaining_topics / pace
    )

    if number_of_classes > len(
        future_class_dates
    ):
        return None

    return future_class_dates[
        number_of_classes - 1
    ]


def fmt_date(d: date) -> str:
    """Return e.g. '7 December 2026'."""

    return (
        f"{d.day} "
        f"{d.strftime('%B %Y')}"
    )