# # app/main.py
# from fastapi import APIRouter, FastAPI
# from fastapi.middleware.cors import CORSMiddleware
# from app.schemas import DefaultResponse

# # 🌟 Import Router ที่เราแยกไฟล์ไว้เข้ามา
# from app.routers import menu, test_api

# router = APIRouter(prefix="/api", tags=["Menu"])

# app = FastAPI(title="Signal School Evaluation API")

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # 🌟 นำ Router มาเชื่อมต่อกับแอปหลัก
# app.include_router(menu.router)
# app.include_router(test_api.router)

# # Route พื้นฐานที่เอาไว้เช็คว่า Server ล่มไหม (มักจะเก็บไว้ที่หน้าหลัก)
# @app.get("/", response_model=DefaultResponse, tags=["Health Check"])
# def health_check():
#     return {"status": "success", "message": "FastAPI Service is running perfectly 🚀"}

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 1. Import Router ที่เราแยกไฟล์ไว้ (เพิ่ม sheets เข้ามา)
from app.routers import menu, test_api, sheets

# 2. Import Database และ Models เพื่อสร้างตาราง
from app.database import engine, Base
import app.models 

# สั่งให้ SQLAlchemy สร้างตารางใน SQLite (ทำงานเฉพาะตอนที่ยังไม่มีไฟล์ .db)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Signal School Evaluation API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# นำ Router มาเชื่อมต่อกับแอปหลัก
app.include_router(menu.router)
app.include_router(test_api.router)
app.include_router(sheets.router) # เชื่อม API ของ Sheets Registry

# Route พื้นฐานที่เอาไว้เช็คว่า Server ล่มไหม
@app.get("/", tags=["Health Check"])
def health_check():
    return {"status": "success", "message": "FastAPI Service is running"}