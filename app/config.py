import re

SPREADSHEET_ID = "1a21LlIxwzdjq4yFK4OAoHuA2WRgQC0OgSkLmn0Ga9m8"
SHEET_NAME = "Sheet1"
GOOGLE_CREDENTIALS_FILE = "service_account.json"
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# รองรับทั้งแบบมี/ไม่มีคำว่า "เหล่า" และทั้ง "ขั้น"/"ชั้น", "รุ่น"/"รุ่นที่"
# ตัวอย่างที่ต้อง match ได้ทั้งหมด:
#   "บันทึกคะแนนชั้นนายร้อย เหล่า ส. รุ่น 68"
#   "บันทึกคะแนนขั้นนายร้อย รุ่น 68"          <- ไม่มีเหล่า
FILENAME_PATTERN = re.compile(
    r"(?:เหล่า\s*(?P<course>[^\s]+)\s*)?รุ่น(?:ที่)?\s*(?P<batch>\d+)"
)

DEFAULT_COURSE = "รวม"  # ใช้เมื่อไฟล์ไม่มีคำว่า "เหล่า" ในชื่อ

DRIVE_FOLDER_ID = None
SYNC_CACHE_TTL_SECONDS = 300