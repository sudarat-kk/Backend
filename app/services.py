# app/services.py
import urllib.parse
import pandas as pd
import gspread
from typing import Any
from app.config import SPREADSHEET_ID

def get_public_sheet_dataframe(sheet_name: str) -> pd.DataFrame:
    sheet_param = urllib.parse.quote(sheet_name)
    url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/gviz/tq?tqx=out:csv&sheet={sheet_param}"
    try:
        df = pd.read_csv(url)
        return df.fillna('')
    except Exception as e:
        raise Exception(f"Failed to fetch data from Google Sheets: {str(e)}")

def format_credit(credit_value: Any) -> float:
    try:
        val = float(credit_value)
        return int(val) if val.is_integer() else val
    except (ValueError, TypeError):
        return 0.0
    
    
gc = gspread.service_account(filename="service_account.json")

def fetch_sheet_data(spreadsheet_id: str):
    try:
        sheet = gc.open_by_key(spreadsheet_id)
        worksheet = sheet.sheet1 
        data = worksheet.get_all_records()
        return data
    except Exception as e:
        return {"error": str(e)}

import time
from googleapiclient.discovery import build
from google.oauth2 import service_account
from sqlalchemy.orm import Session
from app.models import SheetMapping
from app.config import FILENAME_PATTERN, DRIVE_FOLDER_ID, SYNC_CACHE_TTL_SECONDS

DRIVE_SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

_drive_creds = service_account.Credentials.from_service_account_file(
    "service_account.json", scopes=DRIVE_SCOPES
)
_drive_service = build("drive", "v3", credentials=_drive_creds)

_last_sync_time = 0  # เก็บ timestamp การ sync ล่าสุด (in-memory, ระดับ process)


def list_course_spreadsheets():
    """ดึงรายชื่อไฟล์ spreadsheet ทั้งหมดที่แชร์ให้ service account (หรือใน folder ที่กำหนด)"""
    query = "mimeType='application/vnd.google-apps.spreadsheet' and trashed=false"
    if DRIVE_FOLDER_ID:
        query += f" and '{DRIVE_FOLDER_ID}' in parents"

    files = []
    page_token = None
    while True:
        resp = _drive_service.files().list(
            q=query,
            fields="nextPageToken, files(id, name)",
            pageSize=100,
            pageToken=page_token,
        ).execute()
        files.extend(resp.get("files", []))
        page_token = resp.get("nextPageToken")
        if not page_token:
            break
    return files


from app.config import FILENAME_PATTERN, DRIVE_FOLDER_ID, SYNC_CACHE_TTL_SECONDS, DEFAULT_COURSE

def sync_sheet_registry(db: Session, force: bool = False):
    global _last_sync_time

    if not force and (time.time() - _last_sync_time) < SYNC_CACHE_TTL_SECONDS:
        return {"skipped": True, "reason": "cache ยังไม่หมดอายุ"}

    files = list_course_spreadsheets()
    updated = 0
    unmatched = []

    for f in files:
        match = FILENAME_PATTERN.search(f["name"])
        if not match:
            unmatched.append(f["name"])
            continue

        course = (match.group("course") or DEFAULT_COURSE).strip()
        batch = int(match.group("batch"))

        existing = db.query(SheetMapping).filter(
            SheetMapping.course == course,
            SheetMapping.batch == batch,
        ).first()

        if existing:
            if existing.spreadsheet_id != f["id"]:
                existing.spreadsheet_id = f["id"]
                updated += 1
        else:
            db.add(SheetMapping(course=course, batch=batch, spreadsheet_id=f["id"]))
            updated += 1

    db.commit()
    _last_sync_time = time.time()

    return {
        "skipped": False,
        "updated_or_added": updated,
        "unmatched_files": unmatched,
    }

def fetch_sheet_data(spreadsheet_id: str, tab_name: str = None):
    try:
        sheet = gc.open_by_key(spreadsheet_id)
        worksheet = sheet.worksheet(tab_name) if tab_name else sheet.sheet1
        # ใช้ get_all_values แทน get_all_records เพราะชีตมี merge cell / header ซับซ้อน
        values = worksheet.get_all_values()
        return {"headers_note": "raw grid data (ไม่ผ่านการแปลง header)", "rows": values}
    except Exception as e:
        return {"error": str(e)}
    
def get_course_subjects_grouped(spreadsheet_id: str, tab_name: str = "แถลงหลักสูตร"):
    sheet = gc.open_by_key(spreadsheet_id)
    worksheet = sheet.worksheet(tab_name)
    values = worksheet.get_all_values()

    header_idx = None
    for i, row in enumerate(values):
        if any(cell.strip() == "ลำดับ" for cell in row):
            header_idx = i
            break

    if header_idx is None:
        raise ValueError(f"ไม่พบหัวตาราง (คำว่า 'ลำดับ') ในแท็บ '{tab_name}'")

    groups = []
    current_group = None
    group_counter = 0
    total_credit = 0.0

    for row in values[header_idx + 1:]:
        if not any(cell.strip() for cell in row):
            continue  # แถวว่างทั้งแถว ข้ามไป

        ladub = row[0].strip() if len(row) > 0 else ""
        name = row[1].strip() if len(row) > 1 else ""
        credit_cell = row[2].strip() if len(row) > 2 else ""
        sent_cell = row[3].strip() if len(row) > 3 else ""

        if ladub == "":
            # แถวย่อย (เช่น กำหนดสอบย่อยของวิชาลำดับก่อนหน้า) ไม่ใช่วิชาใหม่ -> ข้าม ไม่ break
            continue

        if not ladub.isdigit():
            # เจอแถวที่ไม่ใช่ตัวเลขและไม่ใช่ค่าว่าง (เช่น แถวสรุปยอดรวมด้านล่างตาราง) -> หยุดจริง
            break

        sent = sent_cell.upper() == "TRUE"

        if credit_cell:
            group_counter += 1
            credit_value = format_credit(credit_cell)
            total_credit += credit_value
            current_group = {
                "groupId": f"M{group_counter:02d}",
                "totalCredits": credit_value,
                "subjects": [],
            }
            groups.append(current_group)

        if current_group is None:
            continue

        current_group["subjects"].append({
            "ladub": int(ladub),
            "name": name,
            "sent": sent,
        })

    return groups, total_credit