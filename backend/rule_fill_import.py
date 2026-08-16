# -*- coding: utf-8 -*-
"""一次性将 rule_fill_output.json 中的结果导入 analysis_result。

用法：python rule_fill_import.py
"""
import json
import os

import psycopg2

BACKEND = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(BACKEND, "rule_fill_output.json")

conf = {
    "host": "127.0.0.1", "port": "55433", "user": "postgres",
    "password": "", "dbname": "postgres",
}


def main():
    if not os.path.exists(SRC):
        raise SystemExit(f"未找到 {SRC}，请先运行 rule_fill_generate.py")
    with open(SRC, encoding="utf-8") as f:
        items = json.load(f)
    print(f"读取结果文件：{len(items)} 条")

    conn = psycopg2.connect(**conf)
    cur = conn.cursor()
    sql = """
        UPDATE analysis_result
        SET production_stage=%s, production_substage=%s,
            part_category=%s::text[], part_name=%s::text[],
            problem_nature=%s
        WHERE dataset_info_id=%s
    """
    rows = [
        (i["production_stage"], i["production_substage"], i["part_category"],
         i["part_name"], i["problem_nature"], i["dataset_info_id"])
        for i in items
    ]
    try:
        cur.executemany(sql, rows)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()
    print(f"一次性导入完成：共更新 {len(rows)} 条 analysis_result")


if __name__ == "__main__":
    main()
