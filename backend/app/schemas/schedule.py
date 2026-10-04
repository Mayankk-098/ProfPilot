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
