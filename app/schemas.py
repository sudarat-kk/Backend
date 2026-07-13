# app/schemas.py
from pydantic import BaseModel
from typing import List, Dict, Any
from pydantic import BaseModel
from typing import Optional

class SubjectItem(BaseModel):
    name: str

class MenuGroup(BaseModel):
    groupId: str
    totalCredits: float
    subjects: List[SubjectItem]

class DefaultResponse(BaseModel):
    status: str
    message: str

class TestReadResponse(DefaultResponse):
    columns: List[str]
    total_rows: int
    preview: List[Dict[str, Any]]

class TestWriteResponse(DefaultResponse):
    row_added: list

class SubjectItem(BaseModel):
    ladub: int
    name: str
    sent: bool


class SubjectGroup(BaseModel):
    groupId: str
    totalCredits: float
    subjects: list[SubjectItem]


class CourseSubjectsResponse(BaseModel):
    status: str
    course: str
    batch: int
    groups: list[SubjectGroup]
    totalCredit: float