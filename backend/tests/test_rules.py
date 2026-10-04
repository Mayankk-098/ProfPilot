"""Pure-logic tests (no DB, no FastAPI). Run from backend/:  pytest tests/test_rules.py"""
from datetime import date, datetime, time

import pytest

from app.services.academic_rules import (
    Slot, SlotChange, current_pace, fmt_date, next_class, occurrences, percent,
    planned_progress, predict_completion, required_pace, summarize_attendance,
    times_overlap,
)


# ---------------- attendance ----------------
def test_exactly_75_not_flagged():
    for a, t in [(3, 4), (30, 40), (6, 8), (75, 100)]:
        s = summarize_attendance(a, t)
        assert not s.flagged and s.classes_needed_to_recover == 0 and s.percentage == 75.0


def test_below_75_flagged():
    assert summarize_attendance(5, 8).flagged          # 62.5%
    assert summarize_attendance(74, 100).flagged


def test_recovery_example():
    s = summarize_attendance(5, 8)                     # need 4 -> 9/12 = 75%
    assert s.classes_needed_to_recover == 4


def test_recovery_is_minimal_bruteforce():
    for t in range(1, 60):
        for a in range(t + 1):
            n = summarize_attendance(a, t).classes_needed_to_recover
            assert (a + n) * 4 >= (t + n) * 3
            if n:
                assert (a + n - 1) * 4 < (t + n - 1) * 3


def test_zero_classes_not_flagged():
    s = summarize_attendance(0, 0)
    assert s.percentage is None and not s.flagged and s.classes_needed_to_recover == 0


def test_invalid_counts():
    with pytest.raises(ValueError):
        summarize_attendance(5, 4)


# ---------------- schedule ----------------
MON = date(2026, 10, 5)  # a Monday
SLOTS = [
    Slot("late", "c1", "L1", 0, time(14), time(15)),    # inserted first on purpose
    Slot("early", "c2", "L1", 0, time(9), time(10)),
    Slot("tue", "c3", "L2", 1, time(9), time(10)),      # other lecturer
]


def test_ordered_by_time_not_row_order():
    assert next_class(SLOTS, [], datetime(2026, 10, 5, 8, 0)).slot_id == "early"
    assert [o.slot_id for o in occurrences(SLOTS, [], MON, 1)] == ["early", "late"]


def test_rolls_to_next_day_then_next_week():
    assert next_class(SLOTS, [], datetime(2026, 10, 5, 16, 0)).slot_id == "tue"
    n = next_class(SLOTS, [], datetime(2026, 10, 6, 10, 0), lecturer_id="L1")
    assert n.slot_id == "early" and n.start.date() == date(2026, 10, 12)


def test_class_in_progress_is_not_next():
    assert next_class(SLOTS, [], datetime(2026, 10, 5, 9, 30)).slot_id == "late"


def test_cancellation():
    ch = [SlotChange("early", MON, cancelled=True)]
    assert next_class(SLOTS, ch, datetime(2026, 10, 5, 8, 0)).slot_id == "late"
    occ = occurrences(SLOTS, ch, MON, 1, include_cancelled=True)
    assert [(o.slot_id, o.status) for o in occ] == [("early", "cancelled"), ("late", "scheduled")]


def test_reschedule_same_day_and_other_day():
    ch = [SlotChange("early", MON, new_date=MON, new_start=time(17), new_end=time(18), new_room="X")]
    occ = occurrences(SLOTS, ch, MON, 1)
    assert [o.slot_id for o in occ] == ["late", "early"]
    assert occ[1].status == "rescheduled" and occ[1].room == "X" and occ[1].original_date == MON

    ch = [SlotChange("early", MON, new_date=date(2026, 10, 7), new_start=time(11), new_end=time(12))]
    assert [o.slot_id for o in occurrences(SLOTS, ch, MON, 1)] == ["late"]
    wed = occurrences(SLOTS, ch, date(2026, 10, 7), 1)
    assert len(wed) == 1 and wed[0].start == datetime(2026, 10, 7, 11, 0)


def test_reschedule_into_window_from_before_window():
    ch = [SlotChange("early", date(2026, 9, 28), new_date=MON, new_start=time(8), new_end=time(9))]
    assert occurrences([SLOTS[1]], ch, MON, 1)[0].original_date == date(2026, 9, 28)


def test_lecturer_filter_and_empty():
    assert next_class(SLOTS, [], datetime(2026, 10, 5, 8, 0), lecturer_id="L2").slot_id == "tue"
    assert next_class([], [], datetime(2026, 10, 5, 8, 0)) is None


def test_overlap():
    a = (datetime(2026, 10, 5, 9), datetime(2026, 10, 5, 10))
    assert times_overlap(*a, datetime(2026, 10, 5, 9, 30), datetime(2026, 10, 5, 10, 30))
    assert not times_overlap(*a, datetime(2026, 10, 5, 10), datetime(2026, 10, 5, 11))


# ---------------- syllabus / pace ----------------
def test_progress_and_pace():
    assert percent(7, 32) == 21.9 and percent(0, 0) == 0.0
    assert current_pace(7, 8) == 0.88 and current_pace(0, 0) == 0.0
    assert required_pace(25, 27) == 0.93
    assert required_pace(0, 10) == 0.0 and required_pace(3, 0) == 3.0


def test_planned_progress():
    today = date(2026, 10, 1)
    ds = [date(2026, 9, 1), date(2026, 10, 1), date(2026, 10, 2), None]
    assert planned_progress(ds, today) == 50.0


def test_predict_completion():
    dates = [date(2026, 10, d) for d in range(1, 21)]
    assert predict_completion(4, 1.0, dates) == dates[3]
    assert predict_completion(5, 2.0, dates) == dates[2]       # ceil(2.5)=3
    assert predict_completion(4, 0.0, dates) is None
    assert predict_completion(100, 1.0, dates) is None
    assert predict_completion(0, 1.0, dates) is None


def test_fmt_date_matches_ai_parser():
    d = date(2026, 12, 7)
    assert fmt_date(d) == "7 December 2026"
    assert datetime.strptime(fmt_date(d), "%d %B %Y").date() == d


def test_threshold_edges_include_74_9_and_74_99():
    assert summarize_attendance(7490, 10000).flagged
    assert summarize_attendance(7499, 10000).flagged
    assert not summarize_attendance(75, 100).flagged
    assert not summarize_attendance(751, 1000).flagged
