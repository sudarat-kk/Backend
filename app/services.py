# app/services.py
import urllib.parse
import pandas as pd
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