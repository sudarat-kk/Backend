
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.models import SheetMapping
from app.schemas import CourseSubjectsResponse
from app.services import fetch_sheet_data, get_course_subjects_grouped, sync_sheet_registry ,gc

router = APIRouter(prefix="/api/sheets", tags=["Sheets Registry"])


class SheetCreate(BaseModel):
    course: str
    batch: int
    spreadsheet_id: str


@router.post("/")
def add_new_sheet(sheet: SheetCreate, db: Session = Depends(get_db)):
    existing = db.query(SheetMapping).filter(
        SheetMapping.course == sheet.course,
        SheetMapping.batch == sheet.batch
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="หลักสูตรและรุ่นนี้มีในระบบแล้ว")

    new_sheet = SheetMapping(
        course=sheet.course,
        batch=sheet.batch,
        spreadsheet_id=sheet.spreadsheet_id
    )
    db.add(new_sheet)
    db.commit()
    db.refresh(new_sheet)
    return {"message": "บันทึกข้อมูลสำเร็จ", "data": new_sheet}


@router.get("/list")
def list_all_mappings(db: Session = Depends(get_db)):
    all_mappings = db.query(SheetMapping).all()
    return [
        {"course": m.course, "batch": m.batch, "spreadsheet_id": m.spreadsheet_id}
        for m in all_mappings
    ]


@router.post("/sync")
def sync_registry(force: bool = False, db: Session = Depends(get_db)):
    """เรียก endpoint นี้เพื่อให้ระบบไปสแกน Drive แล้วอัปเดต mapping อัตโนมัติ"""
    result = sync_sheet_registry(db, force=force)
    return result


@router.get("/data")
def get_course_data(course: str, batch: int, tab: str = None, db: Session = Depends(get_db)):
    result = db.query(SheetMapping).filter(
        SheetMapping.course == course,
        SheetMapping.batch == batch,
    ).first()

    if not result:
        sync_sheet_registry(db, force=True)
        result = db.query(SheetMapping).filter(
            SheetMapping.course == course,
            SheetMapping.batch == batch,
        ).first()

    if not result:
        raise HTTPException(status_code=404, detail="ไม่พบข้อมูล Sheet ID ของหลักสูตรนี้")

    sheet_data = fetch_sheet_data(result.spreadsheet_id, tab_name=tab)

    return {
        "status": "success",
        "course": result.course,
        "batch": result.batch,
        "spreadsheet_id": result.spreadsheet_id,
        "data": sheet_data,
    }


@router.get("/subjects", response_model=CourseSubjectsResponse)
def get_subjects(course: str, batch: int, tab: str = "แถลงหลักสูตร", db: Session = Depends(get_db)):
    result = db.query(SheetMapping).filter(
        SheetMapping.course == course,
        SheetMapping.batch == batch,
    ).first()

    if not result:
        sync_sheet_registry(db, force=True)
        result = db.query(SheetMapping).filter(
            SheetMapping.course == course,
            SheetMapping.batch == batch,
        ).first()

    if not result:
        raise HTTPException(status_code=404, detail="ไม่พบข้อมูล Sheet ID ของหลักสูตรนี้")

    try:
        groups, total_credit = get_course_subjects_grouped(result.spreadsheet_id, tab_name=tab)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ดึงข้อมูลรายวิชาไม่สำเร็จ: {str(e)}")

    return {
        "status": "success",
        "course": result.course,
        "batch": result.batch,
        "groups": groups,
        "totalCredit": total_credit,
    }

@router.get("/debug-raw")
def debug_raw_values(course: str, batch: int, tab: str = "แถลงหลักสูตร", db: Session = Depends(get_db)):
    result = db.query(SheetMapping).filter(
        SheetMapping.course == course,
        SheetMapping.batch == batch,
    ).first()

    if not result:
        raise HTTPException(status_code=404, detail="ไม่พบข้อมูล")

    sheet = gc.open_by_key(result.spreadsheet_id)
    worksheet = sheet.worksheet(tab)
    values = worksheet.get_all_values()

    # ส่งแค่ 15 แถวแรกพอ ไม่ต้องส่งทั้งหมด
    return {"total_rows": len(values), "first_15_rows": values[:15]}