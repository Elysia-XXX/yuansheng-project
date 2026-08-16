# -*- coding: utf-8 -*-
"""将 shop_qa.xlsx（淘宝「问大家」问答数据）导入 PostgreSQL 的 dataset_info 表。

Excel 结构（sheet「问大家汇总」）：
- 第 1 行：中文表头（商品id / 问题 / 回答用户 / 回答内容 / 回答时间 / 购买状态）
- 第 2 行起：数据（一个问题可能有多条回答，也可能没有回答）

映射规则：
- 商品id     -> source_product_id，并从 product_catalog 补齐 sku / category_l1/2/3
- 问题       -> customer_transcript
- touchpoint -> S4（问大家）
- source_form -> Q→多A对
- platform   -> 淘宝
- 回答用户/回答内容/回答时间/购买状态 -> 合并为 qa_answers（JSON 数组），无回答则为 []
- 其余字段留空

幂等：已存在 (source_product_id, customer_transcript, touchpoint='S4') 的记录跳过。

用法：
    python import_shop_qa.py [xlsx路径]
"""
import json
import os
import sys

import openpyxl
import psycopg2

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND = os.path.join(ROOT, "backend")


def load_db_config():
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


def load_catalog_map(conf):
    """读取 product_catalog 库，返回 source_product_id -> {sku, l1, l2, l3}。"""
    catalog_conf = dict(conf)
    catalog_conf["dbname"] = "product_catalog"
    mapping = {}
    try:
        conn = psycopg2.connect(**catalog_conf)
    except Exception as exc:  # 目录库不可用时仍可导入，只是品类缺省
        print(f"警告：无法连接 product_catalog 库（{exc}），品类将使用缺省值")
        return mapping
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT source_product_id, sku, category_l1, category_l2, category_l3 "
                "FROM product_catalog"
            )
            for row in cur.fetchall():
                mapping[str(row[0]).strip()] = {
                    "sku": row[1],
                    "category_l1": row[2],
                    "category_l2": row[3],
                    "category_l3": row[4],
                }
    finally:
        conn.close()
    return mapping


def parse_qa_rows(ws):
    """按 (商品id, 问题) 分组，返回 { (pid, question): [answers...] }，保持首次出现顺序。"""
    groups = {}
    order = []
    for r in range(2, ws.max_row + 1):
        pid = ws.cell(row=r, column=1).value
        question = ws.cell(row=r, column=2).value
        user = ws.cell(row=r, column=3).value
        content = ws.cell(row=r, column=4).value
        time_str = ws.cell(row=r, column=5).value
        status = ws.cell(row=r, column=6).value
        if pid is None or question is None:
            continue
        pid = str(pid).strip()
        question = str(question).strip()
        if not pid or not question:
            continue
        key = (pid, question)
        if key not in groups:
            groups[key] = []
            order.append(key)
        if content is not None and str(content).strip():
            groups[key].append(
                {
                    "user": str(user).strip() if user is not None else None,
                    "content": str(content).strip(),
                    "time": str(time_str).strip() if time_str is not None else None,
                    "status": str(status).strip() if status is not None else None,
                }
            )
    return groups, order


def main():
    xlsx_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        ROOT, "shop_qa.xlsx"
    )
    conf = load_db_config()

    wb = openpyxl.load_workbook(xlsx_path, data_only=True)
    ws = wb.active
    print(f"读取工作表：{ws.title}（{ws.max_row - 1} 行）")

    groups, order = parse_qa_rows(ws)
    print(f"去重后问题数（商品id, 问题）：{len(order)}")

    catalog = load_catalog_map(conf)
    matched = sum(1 for pid, _ in order if pid in catalog)
    print(f"商品目录命中：{matched}/{len(order)}")

    records = []
    for pid, question in order:
        info = catalog.get(pid, {})
        records.append(
            {
                "source_product_id": pid,
                "customer_transcript": question,
                "touchpoint": "S4",
                "source_form": "Q→多A对",
                "category_l1": info.get("category_l1") or "其他",
                "category_l2": info.get("category_l2") or "未识别",
                "category_l3": info.get("category_l3") or "待人工确认",
                "sku": info.get("sku") or pid,
                "platform": "淘宝",
                "qa_answers": groups[(pid, question)],
            }
        )

    conn = psycopg2.connect(**conf)
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT source_product_id, customer_transcript "
                "FROM dataset_info WHERE touchpoint = 'S4'"
            )
            existing = {
                (str(pid), str(transcript)) for pid, transcript in cur.fetchall()
            }
        to_insert = [rec for rec in records if (rec["source_product_id"], rec["customer_transcript"]) not in existing]
        skipped = len(records) - len(to_insert)
        print(f"已存在跳过：{skipped}，待导入：{len(to_insert)}")
        if not to_insert:
            print("没有需要导入的新数据")
            return
        for rec in to_insert:
            rec["qa_answers"] = json.dumps(rec["qa_answers"], ensure_ascii=False)
        sql = (
            "INSERT INTO dataset_info "
            "(source_product_id, customer_transcript, touchpoint, source_form, "
            " category_l1, category_l2, category_l3, sku, platform, qa_answers) "
            "VALUES (%(source_product_id)s, %(customer_transcript)s, %(touchpoint)s, "
            " %(source_form)s, %(category_l1)s, %(category_l2)s, %(category_l3)s, "
            " %(sku)s, %(platform)s, %(qa_answers)s::jsonb)"
        )
        with conn.cursor() as cur:
            cur.executemany(sql, to_insert)
        conn.commit()
        print(f"成功导入 {len(to_insert)} 行到 dataset_info 表")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
