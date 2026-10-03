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
    time: str
    period: str
    room: str
    item_type: str
    course_id: str | None
