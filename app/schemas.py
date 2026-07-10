# app/schemas.py
from pydantic import BaseModel
from typing import List, Dict, Any

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