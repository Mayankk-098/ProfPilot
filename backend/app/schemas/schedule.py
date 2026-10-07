import datetime as dt

from pydantic import BaseModel


class CancelClassRequest(BaseModel):
    on_date: dt.date                       # the date of the class being cancelled
    reason: str | None = None


class RescheduleClassRequest(BaseModel):
    on_date: dt.date                       # original date of the class
    new_date: dt.date
    new_start_time: dt.time                # e.g. "14:00"
    new_end_time: dt.time | None = None    # default: same duration as original
    new_room: str | None = None
    reason: str | None = None


class ScheduleChangeResponse(BaseModel):
    item_id: str
    on_date: str
    status: str                            # cancelled | rescheduled
    new_date: str | None
    new_start_time: str | None             # "HH:MM"
    new_end_time: str | None
    new_room: str | None
    reason: str | None


class ScheduleTemplateResponse(BaseModel):
    id: str
    subject: str
    code: str | None
    batch: str
    weekday: int
    start_time: str
    end_time: str
    room: str
    item_type: str
    lecturer_id: str
    course_id: str | None


class ScheduleTemplateCreate(BaseModel):
    weekday: int
    start_time: dt.time
    end_time: dt.time
    room: str
    item_type: str = "class"
    course_id: str | None = None
    subject: str | None = None
    code: str | None = None
    batch: str | None = None


class ScheduleTemplateUpdate(BaseModel):
    weekday: int | None = None
    start_time: dt.time | None = None
    end_time: dt.time | None = None
    room: str | None = None
    item_type: str | None = None
    course_id: str | None = None
    subject: str | None = None
    code: str | None = None
    batch: str | None = None
