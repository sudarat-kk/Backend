from fastapi import APIRouter, HTTPException, status
from app.config import SHEET_NAME
from app.schemas import MenuGroup
from app.services import get_public_sheet_dataframe, format_credit
import json
import os
from fastapi import APIRouter, HTTPException, status

# ประกาศ Router และตั้งค่า Prefix ให้เติม "/api" ไว้ข้างหน้าอัตโนมัติ
router = APIRouter(
    prefix="/api",
    tags=["Menu"]
)

# สังเกตว่าเราใช้ @router แทน @app และไม่ต้องพิมพ์ /api ซ้ำแล้ว
@router.get("/menu-structure", response_model=list[MenuGroup])
def get_menu_structure():
    try:
        df = get_public_sheet_dataframe(SHEET_NAME)
        grouped_data = {}
        order_keys = []

        for _, row in df.iterrows():
            group = str(row.get('group_id', 'Unknown'))
            if group not in grouped_data:
                grouped_data[group] = {"groupId": group, "totalCredits": 0, "subjects": []}
                order_keys.append(group)

            credit = format_credit(row.get('total_credits', 0))
            grouped_data[group]["totalCredits"] += credit
            grouped_data[group]["subjects"].append({"name": str(row.get('subject_name', ''))})

        return [grouped_data[key] for key in order_keys]

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"ดึงข้อมูลเมนูไม่สำเร็จ: {str(e)}"
        )
    
@router.get("/navigation")
def get_header_navigation():
    # ระบุ path ของไฟล์ JSON (เนื่องจากไฟล์อยู่ระดับเดียวกับโฟลเดอร์ app)
    file_path = "navigation.json"
    
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="ไม่พบไฟล์ navigation.json"
        )
        
    try:
        # เปิดอ่านไฟล์และส่งข้อมูลกลับไปเป็น JSON
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"เกิดข้อผิดพลาดในการอ่านไฟล์ JSON: {str(e)}"
        )