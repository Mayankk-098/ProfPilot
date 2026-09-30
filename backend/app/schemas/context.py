from pydantic import BaseModel


class ContextLecturer(BaseModel):
    id: str
    name: str
    title: str
    department: str


class ContextScheduleItem(BaseModel):
    id: str
    subject: str
    code: str | None
    batch: str
    time: str
    period: str
    room: str
    item_type: str
    course_id: str | None


class ContextCourse(BaseModel):
    id: str
    code: str
    name: str
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


class ContextLecture(BaseModel):
    id: str
    date: str
    duration: int
    description: str


class AcademicContextResponse(BaseModel):
    current_date: str

    lecturer: ContextLecturer

    selected_course: ContextCourse | None

    next_class: ContextScheduleItem | None

    today_schedule: list[ContextScheduleItem]

    courses: list[ContextCourse]

    recent_lectures: list[ContextLecture]

    alerts: list[str]

    summary: dict