from fastapi import FastAPI, File, UploadFile, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import pandas as pd
import pyodbc
import shutil
import os

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# === SQL CONFIG ===
SQL_CONN_STR = (
    'DRIVER={ODBC Driver 17 for SQL Server};'
    'SERVER=192.168.0.53;'
    'DATABASE=portal;'
    'UID=sanblueuat;'
    'PWD=Admin^portal'
)

HARDCODED_SQL_TYPES = {
    "title": "NVARCHAR(MAX)",
    "contactperson": "NVARCHAR(MAX)",
    "designation": "NVARCHAR(MAX)",
    "companyname": "NVARCHAR(MAX)",
    "address1": "NVARCHAR(MAX)",
    "address2": "NVARCHAR(MAX)",
    "address3": "NVARCHAR(MAX)",
    "city": "NVARCHAR(MAX)",
    "zip_code": "NVARCHAR(MAX)",
    "state": "NVARCHAR(MAX)",
    "country": "NVARCHAR(MAX)",
    "tel": "NVARCHAR(MAX)"
}

def sanitize_column_name(col):
    return col.strip().replace(" ", "").replace(".", "_").replace(";", "_").replace("-", "_").replace(":", "").lower()

def map_dtype_to_sql(col_name):
    return HARDCODED_SQL_TYPES.get(col_name.lower(), "NVARCHAR(MAX)")

def clean_dataframe(df):
    df = df.where(pd.notnull(df), None)
    df = df.applymap(lambda x: str(x).strip() if pd.notnull(x) else None)
    return df

def create_table(cursor, conn, table_name, df):
    cursor.execute(f"""
        IF OBJECT_ID(N'{table_name}', N'U') IS NOT NULL
        BEGIN
            DROP TABLE [{table_name}]
        END
    """)
    conn.commit()

    column_defs = ",\n    ".join([f"[{col}] {map_dtype_to_sql(col)}" for col in df.columns])
    cursor.execute(f"CREATE TABLE [{table_name}] (\n{column_defs}\n)")
    conn.commit()

def insert_data(cursor, table_name, df):
    columns = ", ".join(f"[{col}]" for col in df.columns)
    placeholders = ", ".join("?" for _ in df.columns)
    insert_sql = f"INSERT INTO [{table_name}] ({columns}) VALUES ({placeholders})"
    cursor.fast_executemany = True
    cursor.executemany(insert_sql, df.values.tolist())

@app.get("/", response_class=HTMLResponse)
async def form_page(request: Request):
    return templates.TemplateResponse("form.html", {"request": request})

@app.post("/upload")
async def upload_file(table_name: str = Form(...), file: UploadFile = File(...)):
    try:
        ext = os.path.splitext(file.filename)[1].lower()
        temp_path = f"temp{ext}"
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        if ext == ".csv":
            df = pd.read_csv(temp_path)
        elif ext in [".xlsx", ".xls"]:
            df = pd.read_excel(temp_path, engine="openpyxl")
        else:
            return {"error": "Unsupported file format"}

        df.columns = [sanitize_column_name(c) for c in df.columns]
        df = clean_dataframe(df)

        conn = pyodbc.connect(SQL_CONN_STR)
        cursor = conn.cursor()
        create_table(cursor, conn, table_name, df)
        insert_data(cursor, table_name, df)
        conn.commit()
        cursor.close()
        conn.close()

        return {"success": True, "rows": len(df), "table": table_name}
    except Exception as e:
        return {"error": str(e)}
