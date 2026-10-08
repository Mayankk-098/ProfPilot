import datetime as dt

from pydantic import BaseModel, Field


class StudentResponse(BaseModel):
    id: str
    roll_no: str
    name: str
    section: str
    email: str | None = None
    lecturer_id: str


class StudentCreate(BaseModel):
    roll_no: str = Field(min_length=1, max_length=30)
    name: str = Field(min_length=1, max_length=120)
    section: str | None = Field(default=None, max_length=30)
    email: str | None = Field(default=None, max_length=254)


class StudentUpdate(BaseModel):
    roll_no: str | None = Field(default=None, min_length=1, max_length=30)
    name: str | None = Field(default=None, min_length=1, max_length=120)
    section: str | None = Field(default=None, max_length=30)
    email: str | None = Field(default=None, max_length=254)


class StudentImportContent(BaseModel):
    content: str = Field(min_length=1)


class StudentImportRow(BaseModel):
    roll_no: str = Field(min_length=1, max_length=30)
    name: str = Field(min_length=1, max_length=120)
    section: str | None = Field(default=None, max_length=30)
    email: str | None = Field(default=None, max_length=254)


class StudentImportConfirm(BaseModel):
    students: list[StudentImportRow] = Field(min_length=1)


class StudentImportRowPreview(BaseModel):
    line: int
    roll_no: str
    name: str
    section: str
    status: str
    message: str


class StudentImportPreviewResponse(BaseModel):
    course_id: str
    valid_count: int
    error_count: int
    rows: list[StudentImportRowPreview]


class StudentImportResult(BaseModel):
    created: int
    enrolled: int
