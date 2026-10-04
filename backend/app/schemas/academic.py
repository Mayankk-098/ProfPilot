from pydantic import BaseModel


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
    syllabus: list[SyllabusUnitResponse]
    lectures: list[LectureResponse]


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
