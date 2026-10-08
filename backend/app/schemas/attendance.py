import datetime as dt
from typing import Literal

from pydantic import BaseModel


class AttendanceStudent(BaseModel):
    student_id: str
    roll_no: str
    name: str
    attended: int
    total: int
    percentage: float | None          # null until at least one class is counted
    flagged: bool                     # percentage strictly below threshold_pct
    classes_needed_to_recover: int    # consecutive classes to attend to reach 75%


class AttendanceSessionSummary(BaseModel):
    class_date: str
    present: int
    absent: int
    excused: int
    total_records: int


class AttendanceStudentHistoryRow(BaseModel):
    class_date: str
    status: Literal["present", "absent", "excused"]


class AttendanceStudentDetailResponse(BaseModel):
    course_id: str
    course_code: str
    threshold_pct: int
    student_id: str
    roll_no: str
    name: str
    section: str
    attended: int
    total: int
    percentage: float | None
    flagged: bool
    classes_needed_to_recover: int
    history: list[AttendanceStudentHistoryRow]


class AttendanceCourseResponse(BaseModel):
    course_id: str
    course_code: str
    short_name: str
    section: str
    threshold_pct: int
    classes_held: int
    last_class_date: str | None
    total_students: int
    class_average_pct: float | None
    present_last_class: int
    absent_last_class: int
    flagged_count: int
    students: list[AttendanceStudent]


class AttendanceMark(BaseModel):
    student_id: str
    status: Literal["present", "absent", "excused"]


class AttendanceSubmit(BaseModel):
    class_date: dt.date
    records: list[AttendanceMark]


class AttendanceSessionRecord(BaseModel):
    student_id: str
    status: Literal["present", "absent", "excused"]


class AttendanceSessionResponse(BaseModel):
    course_id: str
    class_date: str
    recorded: bool
    records: list[AttendanceSessionRecord]


class AttendanceSubmitResult(BaseModel):
    course_id: str
    class_date: str
    created: int
    updated: int
