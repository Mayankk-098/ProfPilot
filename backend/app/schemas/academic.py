import datetime as dt

from pydantic import BaseModel, Field


class CourseSummary(BaseModel):
    id: str
    code: str
    name: str
    short_name: str
    section: str

    progress: float
    planned_progress: float

    current_pace: float
    required_pace: float

    predicted_completion: str
    planned_completion: str

    total_students: int
    present_today: int
    absent_today: int


class SyllabusTopicResponse(BaseModel):
    id: str
    name: str
    completed: bool
    planned_date: str | None


class SyllabusUnitResponse(BaseModel):
    id: str
    name: str
    progress: float
    topics: list[SyllabusTopicResponse]


class LectureResponse(BaseModel):
    id: str
    date: str
    duration: int
    description: str


class CourseDetailResponse(CourseSummary):
    department: str
    start_date: str | None = None
    planned_end_date: str | None = None
    syllabus: list[SyllabusUnitResponse]
    lectures: list[LectureResponse]


class CourseCreate(BaseModel):
    code: str = Field(min_length=1, max_length=30)
    name: str = Field(min_length=1, max_length=150)
    short_name: str = Field(min_length=1, max_length=30)
    section: str = Field(min_length=1, max_length=30)
    start_date: dt.date
    planned_end_date: dt.date


class CourseUpdate(BaseModel):
    code: str | None = Field(default=None, min_length=1, max_length=30)
    name: str | None = Field(default=None, min_length=1, max_length=150)
    short_name: str | None = Field(default=None, min_length=1, max_length=30)
    section: str | None = Field(default=None, min_length=1, max_length=30)
    start_date: dt.date | None = None
    planned_end_date: dt.date | None = None


class SyllabusUnitCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)


class SyllabusUnitUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)


class SyllabusTopicCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    planned_date: dt.date | None = None


class SyllabusTopicUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    planned_date: dt.date | None = None
    clear_planned_date: bool = False


class ReorderRequest(BaseModel):
    ids: list[str]


class AIQuery(BaseModel):
    message: str
    course_id: str | None = None


class AIActionExecute(BaseModel):
    confirmed: bool
    action_plan: dict


class ScheduleResponse(BaseModel):
    id: str
    subject: str
    code: str | None
    batch: str
    weekday: int
    start_time: str | None
    end_time: str | None
    room: str | None
    item_type: str
    lecturer_id: str | None
    course_id: str | None
    status: str
    date: str
    original_date: str | None
    time: str | None
    period: str | None
