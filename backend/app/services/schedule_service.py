from datetime import date as Date, datetime, time, timedelta

from sqlalchemy.orm import Session

from app.models.academic import Course, ScheduleItem, ScheduleChange
from app.services import clock
from app.services.ids import new_id


def _time_str(value: time | None) -> str | None:
    return value.strftime("%H:%M") if value else None


def _time_12h(value: time | None) -> str | None:
    if value is None:
        return None
    return value.strftime("%I:%M")


def _period(value: time | None) -> str | None:
    if value is None:
        return None
    return value.strftime("%p")


def _duration(start: time, end: time) -> timedelta:
    start_dt = datetime.combine(Date.min, start)
    end_dt = datetime.combine(Date.min, end)

    if end_dt <= start_dt:
        end_dt += timedelta(days=1)

    return end_dt - start_dt


def _get_item(
    db: Session,
    item_id: str,
    lecturer_id: str | None = None,
):
    query = db.query(ScheduleItem).filter(
        ScheduleItem.id == item_id
    )

    if lecturer_id is not None:
        query = query.filter(
            ScheduleItem.lecturer_id == lecturer_id
        )

    item = query.first()

    if item is None:
        raise LookupError("Schedule item not found")

    return item


def _load(
    db: Session,
    lecturer_id: str | None = None,
):
    query = db.query(ScheduleItem)

    if lecturer_id is not None:
        query = query.filter(
            ScheduleItem.lecturer_id == lecturer_id
        )

    return query.all()


def _change_for_date(
    db: Session,
    item_id: str,
    on_date: Date,
):
    return (
        db.query(ScheduleChange)
        .filter(
            ScheduleChange.item_id == item_id,
            ScheduleChange.on_date == on_date,
        )
        .first()
    )


def _all_changes(
    db: Session,
    item_ids: list[str],
):
    if not item_ids:
        return []

    return (
        db.query(ScheduleChange)
        .filter(
            ScheduleChange.item_id.in_(item_ids)
        )
        .all()
    )


def _change_map(
    db: Session,
    item_ids: list[str],
):
    changes = _all_changes(db, item_ids)

    return {
        (change.item_id, change.on_date): change
        for change in changes
    }


def _is_valid_original_date(
    item: ScheduleItem,
    on_date: Date,
) -> bool:
    return on_date.weekday() == item.weekday


def _serialize_item(
    item: ScheduleItem,
    occurrence_date: Date,
    status: str = "scheduled",
    *,
    start_time: time | None = None,
    end_time: time | None = None,
    room: str | None = None,
    original_date: Date | None = None,
):
    start = start_time or item.start_time
    end = end_time or item.end_time
    actual_date = occurrence_date

    return {
        "id": item.id,
        "subject": item.subject,
        "code": item.code,
        "batch": item.batch,
        "weekday": actual_date.weekday(),
        "start_time": _time_str(start),
        "end_time": _time_str(end),
        "room": room if room is not None else item.room,
        "item_type": item.item_type,
        "lecturer_id": item.lecturer_id,
        "course_id": item.course_id,
        "status": status,
        "date": actual_date.isoformat(),
        "original_date": (
            original_date.isoformat()
            if original_date is not None
            else None
        ),
        "time": _time_12h(start),
        "period": _period(start),
    }


def _occurrence_for_date(
    db: Session,
    item: ScheduleItem,
    occurrence_date: Date,
    *,
    include_cancelled: bool = False,
):
    """
    Resolve one recurring ScheduleItem into its actual occurrence
    on a particular calendar date.

    ScheduleChange is applied to the original occurrence date.
    """

    if occurrence_date.weekday() != item.weekday:
        return None

    change = _change_for_date(
        db,
        item.id,
        occurrence_date,
    )

    incoming_reschedule = (
        db.query(ScheduleChange)
        .filter(
            ScheduleChange.item_id == item.id,
            ScheduleChange.status == "rescheduled",
            ScheduleChange.new_date == occurrence_date,
        )
        .first()
    )
    if incoming_reschedule is not None:
        return None

    if change is None:
        return _serialize_item(
            item,
            occurrence_date,
            "scheduled",
        )

    if change.status == "cancelled":
        if not include_cancelled:
            return None

        return _serialize_item(
            item,
            occurrence_date,
            "cancelled",
        )

    if change.status == "rescheduled":
        if change.new_date is None:
            return None

        # The original occurrence disappears from its original date.
        return None

    return _serialize_item(
        item,
        occurrence_date,
        "scheduled",
    )


def _rescheduled_occurrences_for_date(
    db: Session,
    items: list[ScheduleItem],
    occurrence_date: Date,
    *,
    include_cancelled: bool = False,
):
    """
    Find classes whose original occurrence was rescheduled TO
    occurrence_date.
    """

    results = []

    item_ids = [item.id for item in items]
    changes = _all_changes(db, item_ids)

    item_map = {
        item.id: item
        for item in items
    }

    for change in changes:
        if (
            change.status != "rescheduled"
            or change.new_date != occurrence_date
        ):
            continue

        item = item_map.get(change.item_id)

        if item is None:
            continue

        start = (
            change.new_start_time
            if change.new_start_time is not None
            else item.start_time
        )

        end = (
            change.new_end_time
            if change.new_end_time is not None
            else item.end_time
        )

        room = (
            change.new_room
            if change.new_room is not None
            else item.room
        )

        results.append(
            _serialize_item(
                item,
                occurrence_date,
                "rescheduled",
                start_time=start,
                end_time=end,
                room=room,
                original_date=change.on_date,
            )
        )

    return results


def item_to_slot(item):
    """
    Backwards-compatible helper for callers that expect start/end
    attributes on a ScheduleItem.
    """
    item.start = item.start_time
    item.end = item.end_time
    return item


def load_changes(db, item_ids):
    return _all_changes(db, item_ids)


def day_schedule(
    db,
    day,
    lecturer_id=None,
    include_cancelled=False,
):
    """
    Return the actual schedule for one calendar date.

    Recurring items are resolved using their weekday and any
    ScheduleChange affecting that date.
    """

    items = _load(
        db,
        lecturer_id=lecturer_id,
    )

    results = []

    for item in items:
        occurrence = _occurrence_for_date(
            db,
            item,
            day,
            include_cancelled=include_cancelled,
        )

        if occurrence is not None:
            results.append(occurrence)

    # Add items that were rescheduled TO this date.
    results.extend(
        _rescheduled_occurrences_for_date(
            db,
            items,
            day,
            include_cancelled=include_cancelled,
        )
    )

    results.sort(
        key=lambda item: (
            item["start_time"] or "",
            item["end_time"] or "",
            item["id"],
        )
    )

    return results


def upcoming(
    db,
    at,
    days=7,
    lecturer_id=None,
    include_cancelled=False,
):
    """
    Return actual calendar occurrences beginning at `at`.

    IMPORTANT:
    Results are sorted by actual date/time, not weekday number.
    This correctly handles:
        Sunday -> Monday
        Thursday -> Friday
        Friday -> Monday
    """

    if isinstance(at, Date) and not isinstance(at, datetime):
        at = datetime.combine(at, time.min)

    results = []

    for offset in range(days):
        current_date = (
            at + timedelta(days=offset)
        ).date()

        daily = day_schedule(
            db,
            current_date,
            lecturer_id=lecturer_id,
            include_cancelled=include_cancelled,
        )

        for item in daily:
            start = item["start_time"]

            if (
                offset == 0
                and start is not None
            ):
                start_value = datetime.strptime(
                    start,
                    "%H:%M",
                ).time()

                if start_value <= at.time():
                    continue

            results.append(item)

    results.sort(
        key=lambda item: (
            item["date"],
            item["start_time"] or "",
            item["end_time"] or "",
            item["id"],
        )
    )

    return results


def next_class(
    db,
    at,
    lecturer_id=None,
):
    """
    Return the next actual CLASS occurrence for the lecturer.

    Meetings and other non-class schedule items are excluded.
    """

    items = upcoming(
        db,
        at,
        days=14,
        lecturer_id=lecturer_id,
        include_cancelled=False,
    )

    classes = [
        item
        for item in items
        if item.get("item_type") == "class"
    ]

    if not classes:
        return None

    return classes[0]


def _validate_change_date(
    item: ScheduleItem,
    on_date: Date,
    today: Date,
):
    if not _is_valid_original_date(item, on_date):
        raise ValueError(
            f"{on_date.isoformat()} is not a scheduled "
            f"occurrence date for {item.id}"
        )

    if on_date < today:
        raise ValueError(
            "Cannot modify a schedule occurrence in the past"
        )


def _validate_no_duplicate_change(
    db: Session,
    item: ScheduleItem,
    on_date: Date,
):
    existing = _change_for_date(
        db,
        item.id,
        on_date,
    )

    if existing is not None:
        raise ValueError(
            "A schedule change already exists for this date"
        )


def cancel_class(
    db,
    item_id,
    on_date,
    reason=None,
    lecturer_id=None,
    today=None,
):
    if today is None:
        today = clock.today()

    item = _get_item(
        db,
        item_id,
        lecturer_id=lecturer_id,
    )

    _validate_change_date(
        item,
        on_date,
        today,
    )

    _validate_no_duplicate_change(
        db,
        item,
        on_date,
    )

    change = ScheduleChange(
        item_id=item.id,
        on_date=on_date,
        status="cancelled",
        new_date=None,
        new_start_time=None,
        new_end_time=None,
        new_room=None,
        reason=reason,
    )

    db.add(change)
    db.commit()
    db.refresh(change)

    return change


def _has_conflict(
    db,
    items,
    source_item,
    source_date,
    new_date,
    new_start_time,
    new_end_time,
):
    """Check conflicts against actual occurrences on the destination date."""
    for other in items:
        if other.id == source_item.id or other.item_type != "class":
            continue

        change = _change_for_date(db, other.id, new_date)

        if change is not None and change.status == "cancelled":
            continue

        if change is not None and change.status == "rescheduled":
            # This original occurrence was moved elsewhere. It only conflicts
            # if another reschedule explicitly moves it onto new_date.
            if change.new_date != new_date:
                continue
            other_start = change.new_start_time or other.start_time
            other_end = change.new_end_time or other.end_time
        else:
            # A normal recurring slot only exists on its configured weekday.
            if other.weekday != new_date.weekday():
                continue
            other_start = other.start_time
            other_end = other.end_time

        if other_start < new_end_time and new_start_time < other_end:
            return True

    # A change stored against another original date can move an occurrence
    # onto the destination date even though that slot's normal weekday differs.
    changes = _all_changes(db, [item.id for item in items])
    for change in changes:
        if (
            change.status != "rescheduled"
            or change.new_date != new_date
            or change.item_id == source_item.id
            or change.on_date == new_date
        ):
            continue

        other = next((item for item in items if item.id == change.item_id), None)
        if other is None or other.item_type != "class":
            continue

        other_start = change.new_start_time or other.start_time
        other_end = change.new_end_time or other.end_time
        if other_start < new_end_time and new_start_time < other_end:
            return True

    return False


def reschedule_class(
    db,
    item_id,
    on_date,
    new_date,
    new_start_time,
    new_end_time=None,
    new_room=None,
    reason=None,
    lecturer_id=None,
    today=None,
):
    if today is None:
        today = clock.today()

    item = _get_item(
        db,
        item_id,
        lecturer_id=lecturer_id,
    )

    _validate_change_date(
        item,
        on_date,
        today,
    )

    if new_date < today:
        raise ValueError(
            "Cannot reschedule to a date in the past"
        )

    _validate_no_duplicate_change(
        db,
        item,
        on_date,
    )

    if new_end_time is None:
        duration = _duration(
            item.start_time,
            item.end_time,
        )

        new_end_time = (
            datetime.combine(
                new_date,
                new_start_time,
            )
            + duration
        ).time()

    if new_end_time <= new_start_time:
        raise ValueError(
            "End time must be after start time"
        )

    items = _load(
        db,
        lecturer_id=item.lecturer_id,
    )

    if _has_conflict(
        db,
        items,
        item,
        on_date,
        new_date,
        new_start_time,
        new_end_time,
    ):
        raise ValueError(
            "Lecturer has another class at the requested time"
        )

    change = ScheduleChange(
        item_id=item.id,
        on_date=on_date,
        status="rescheduled",
        new_date=new_date,
        new_start_time=new_start_time,
        new_end_time=new_end_time,
        new_room=new_room,
        reason=reason,
    )

    db.add(change)
    db.commit()
    db.refresh(change)

    return change


def restore_class(
    db,
    item_id,
    on_date,
    lecturer_id=None,
):
    item = _get_item(
        db,
        item_id,
        lecturer_id=lecturer_id,
    )

    change = _change_for_date(
        db,
        item.id,
        on_date,
    )

    if change is None:
        raise LookupError(
            "Schedule change not found"
        )

    db.delete(change)
    db.commit()


def _serialize_template(item: ScheduleItem) -> dict:
    return {
        "id": item.id,
        "subject": item.subject,
        "code": item.code,
        "batch": item.batch,
        "weekday": item.weekday,
        "start_time": _time_str(item.start_time),
        "end_time": _time_str(item.end_time),
        "room": item.room,
        "item_type": item.item_type,
        "lecturer_id": item.lecturer_id,
        "course_id": item.course_id,
    }


def list_items(db, lecturer_id: str) -> list[dict]:
    items = (
        db.query(ScheduleItem)
        .filter(ScheduleItem.lecturer_id == lecturer_id)
        .order_by(
            ScheduleItem.weekday,
            ScheduleItem.start_time,
            ScheduleItem.id,
        )
        .all()
    )
    return [_serialize_template(item) for item in items]


def _template_conflict(
    db,
    lecturer_id: str,
    weekday: int,
    start_time: time,
    end_time: time,
    exclude_id: str | None = None,
) -> bool:
    query = db.query(ScheduleItem).filter(
        ScheduleItem.lecturer_id == lecturer_id,
        ScheduleItem.weekday == weekday,
    )
    if exclude_id is not None:
        query = query.filter(ScheduleItem.id != exclude_id)

    for other in query.all():
        if other.start_time < end_time and start_time < other.end_time:
            return True
    return False


def create_item(
    db,
    lecturer_id: str,
    *,
    weekday: int,
    start_time: time,
    end_time: time,
    room: str,
    item_type: str = "class",
    course_id: str | None = None,
    subject: str | None = None,
    code: str | None = None,
    batch: str | None = None,
) -> dict:
    from app.models.academic import Course

    if weekday < 0 or weekday > 6:
        raise ValueError("weekday must be between 0 (Monday) and 6 (Sunday)")
    if end_time <= start_time:
        raise ValueError("End time must be after start time")
    if item_type not in {"class", "meeting"}:
        raise ValueError("item_type must be class or meeting")

    course = None
    if course_id is not None:
        course = (
            db.query(Course)
            .filter(
                Course.id == course_id,
                Course.lecturer_id == lecturer_id,
            )
            .first()
        )
        if course is None:
            raise LookupError("Course not found")

    resolved_subject = (subject or (course.short_name if course else "") or "").strip()
    if not resolved_subject:
        raise ValueError("subject is required when no course is linked")

    resolved_code = code if code is not None else (course.code if course else None)
    resolved_batch = (batch or (course.section if course else "") or "").strip()
    if not resolved_batch:
        raise ValueError("batch is required when no course is linked")

    if _template_conflict(db, lecturer_id, weekday, start_time, end_time):
        raise ValueError("This slot overlaps another timetable entry")

    from app.services.ids import new_id

    item = ScheduleItem(
        id=new_id("sch"),
        subject=resolved_subject,
        code=resolved_code,
        batch=resolved_batch,
        weekday=weekday,
        start_time=start_time,
        end_time=end_time,
        room=room.strip(),
        item_type=item_type,
        lecturer_id=lecturer_id,
        course_id=course.id if course else None,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return _serialize_template(item)


def update_item(
    db,
    item_id: str,
    lecturer_id: str,
    **fields,
) -> dict:
    from app.models.academic import Course

    item = _get_item(db, item_id, lecturer_id=lecturer_id)

    if "course_id" in fields:
        course_id = fields["course_id"]
        if course_id is None:
            item.course_id = None
        else:
            course = (
                db.query(Course)
                .filter(
                    Course.id == course_id,
                    Course.lecturer_id == lecturer_id,
                )
                .first()
            )
            if course is None:
                raise LookupError("Course not found")
            item.course_id = course.id
            if fields.get("subject") is None:
                item.subject = course.short_name
            if fields.get("code") is None:
                item.code = course.code
            if fields.get("batch") is None:
                item.batch = course.section

    for key in ("subject", "code", "batch", "room"):
        if key in fields and fields[key] is not None:
            value = fields[key]
            setattr(item, key, value.strip() if isinstance(value, str) else value)

    if fields.get("weekday") is not None:
        weekday = fields["weekday"]
        if weekday < 0 or weekday > 6:
            raise ValueError("weekday must be between 0 (Monday) and 6 (Sunday)")
        item.weekday = weekday
    if fields.get("start_time") is not None:
        item.start_time = fields["start_time"]
    if fields.get("end_time") is not None:
        item.end_time = fields["end_time"]
    if item.end_time <= item.start_time:
        raise ValueError("End time must be after start time")
    if fields.get("item_type") is not None:
        if fields["item_type"] not in {"class", "meeting"}:
            raise ValueError("item_type must be class or meeting")
        item.item_type = fields["item_type"]

    if _template_conflict(
        db,
        lecturer_id,
        item.weekday,
        item.start_time,
        item.end_time,
        exclude_id=item.id,
    ):
        raise ValueError("This slot overlaps another timetable entry")

    db.commit()
    db.refresh(item)
    return _serialize_template(item)


def delete_item(db, item_id: str, lecturer_id: str) -> None:
    item = _get_item(db, item_id, lecturer_id=lecturer_id)
    db.delete(item)
    db.commit()