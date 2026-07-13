from sqlalchemy import Column, Integer, String
from app.database import Base

class SheetMapping(Base):
    __tablename__ = "sheet_mappings"

    id = Column(Integer, primary_key=True, index=True)
    course = Column(String, index=True)
    batch = Column(Integer, index=True)
    spreadsheet_id = Column(String, unique=True, index=True)