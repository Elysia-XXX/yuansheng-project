# -*- coding: utf-8 -*-
"""将 dataset_info_表一.xlsx 的数据导入 PostgreSQL 的 dataset_info 表。

Excel 结构：
- 第 1 行：中文表头（跳过）
- 第 2 行：英文字段名（对应数据库列名，用作映射）
- 第 3 行起：数据

用法：
    python import_dataset.py [xlsx路径]
    （连接信息从 backend/.env 读取；xlsx 默认取项目根目录 dataset_info_表一.xlsx）
"""
import os
import sys

import openpyxl
import psycopg2

# 允许直接运行：backend/import_dataset.py 时把项目根加入路径以读取 .env
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND = os.path.join(ROOT, "backend")


def load_db_config():
    """从 backend/.env 读取数据库连接配置，缺省用后端默认值。"""
    conf = {
        "host": "127.0.0.1",
        "port": "55433",
        "user": "postgres",
        "password": "",
        "dbname": "postgres",
    }
    env_path = os.path.join(BACKEND, ".env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                key = key.strip().upper()
                value = value.strip()
                if key == "DB_HOST":
                    conf["host"] = value
                elif key == "DB_PORT":
                    conf["port"] = value
                elif key == "DB_USER":
                    conf["user"] = value
                elif key == "DB_PASSWORD":
                    conf["password"] = value
                elif key == "DB_NAME":
                    conf["dbname"] = value
    return conf


def convert(value, field):
    """按字段类型做基础清洗：空串→None、是/否→布尔、金额/时间。"""
    if value is None:
        return None
    s = str(value).strip()
    if s == "":
        return None
    if field == "is_gift":
        if s in ("是", "true", "True", "TRUE", "1"):
            return True
        if s in ("否", "false", "False", "FALSE", "0"):
            return False
        return s
    if field in ("paid_amount", "original_amount"):
        try:
            return float(s)
        except ValueError:
            return None
    if field in ("complaint_time", "created_at"):
        # 已是字符串，交给 psycopg2 推断为 timestamp
        return s
    return s


def main():
    xlsx_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        ROOT, "dataset_info_表一.xlsx"
    )
    conf = load_db_config()

    wb = openpyxl.load_workbook(xlsx_path, data_only=True)
    ws = wb.active

    header_row = None
    for r in range(1, min(ws.max_row, 4) + 1):
        values = [ws.cell(row=r, column=c).value for c in range(1, ws.max_column + 1)]
        if any(v and str(v).strip().lower() in (
            "customer_transcript", "touchpoint", "category_l1"
        ) for v in values):
            header_row = r
            break
    if header_row is None:
        raise SystemExit("未找到字段名行（应包含 customer_transcript 等）")

    fields = []
    for c in range(1, ws.max_column + 1):
        v = ws.cell(row=header_row, column=c).value
        fields.append(None if v is None else str(v).strip())

    data_start = header_row + 1
    rows = []
    for r in range(data_start, ws.max_row + 1):
        rec = {}
        empty = True
        for c, field in enumerate(fields, start=1):
            if field:
                rec[field] = convert(ws.cell(row=r, column=c).value, field)
                if rec[field] is not None:
                    empty = False
        if empty:
            continue
        rows.append(rec)

    if not rows:
        raise SystemExit("Excel 中没有可导入的数据行")

    cols = [f for f in fields if f and any(rec.get(f) is not None for rec in rows)]
    sql = (
        "INSERT INTO dataset_info ({}) VALUES ({})"
    ).format(
        ", ".join(cols),
        ", ".join("%({})s".format(c) for c in cols),
    )

    conn = psycopg2.connect(**conf)
    try:
        with conn.cursor() as cur:
            cur.executemany(sql, rows)
        conn.commit()
        print(f"成功导入 {len(rows)} 行到 dataset_info 表")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
