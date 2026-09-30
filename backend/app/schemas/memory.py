from datetime import datetime

from pydantic import BaseModel, ConfigDict


class MemoryCreate(BaseModel):
    lecturer_id: str
    course_id: str | None = None
    event_type: str
    title: str
    summary: str
    occurred_at: datetime | None = None


class MemoryResponse(BaseModel):
    id: int
    lecturer_id: str
    course_id: str | None
    event_type: str
    title: str
    summary: str
    occurred_at: datetime

    model_config = ConfigDict(from_attributes=True)