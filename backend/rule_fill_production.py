# -*- coding: utf-8 -*-
"""规则推断：对问大家(S4)咨询类记录，基于问题原文/品类推断
production_stage / production_substage / part_category / part_name / problem_nature，
直接 UPDATE analysis_result，不调用 MiMo。

用法：python rule_fill_production.py [limit]
"""
import sys

import psycopg2

conf = {
    "host": "127.0.0.1", "port": "55433", "user": "postgres",
    "password": "", "dbname": "postgres",
}

# 规则：(关键词, stage, substage, [part_category], [part_name], problem_nature)
RULES = [
    (["漏", "渗水"], "生产制造", "组装", ["密封与紧固"], ["密封圈/密封垫"], "质量缺陷"),
    (["涂层", "掉漆", "脱落"], "原材料", "涂层", ["结构壳体"], ["机身外壳"], "质量缺陷"),
    (["糊底"], "生产制造", "组装", ["容器内胆"], ["内胆/锅体（炖锅/饭煲）"], "质量缺陷"),
    (["电池", "续航", "充电", "电量"], "原材料", "电子元器件", ["线束与电源"], ["电池包"], "功能不符"),
    (["不转", "不工作", "没反应", "坏", "故障", "容易坏", "耐用"], "生产制造", "组装", ["动力系统"], ["电机"], "质量缺陷"),
    (["清洗", "换水", "清洁", "拆"], "安装调试", "首次使用指导", ["功能执行件"], ["滤网/滤篮"], "体验不佳"),
    (["干净", "洗干净", "洗的干净", "去污"], "安装调试", "首次使用指导", [], [], "体验不佳"),
    (["好用", "方便", "多大", "多久", "多少", "能不能", "可以吗", "能洗"], "安装调试", "首次使用指导", [], [], "体验不佳"),
]


def infer(text):
    text = str(text or "")
    for keywords, stage, substage, cats, parts, nature in RULES:
        if any(k in text for k in keywords):
            return stage, substage, cats, parts, nature
    return None


def main():
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    conn = psycopg2.connect(**conf)
    cur = conn.cursor()
    cur.execute("""
        SELECT a.id, d.id, d.customer_transcript
        FROM analysis_result a
        JOIN dataset_info d ON a.dataset_info_id = d.id
        WHERE d.touchpoint='S4'
          AND (a.production_stage IS NULL OR a.production_stage='')
        ORDER BY d.id
        LIMIT %s
    """, (limit,))
    rows = cur.fetchall()
    print(f"待处理（前 {len(rows)} 条）")
    updated = 0
    for a_id, d_id, text in rows:
        r = infer(text)
        if not r:
            print(f"  dataset_info_id={d_id}: 无匹配规则，跳过 | {text[:30]}")
            continue
        stage, substage, cats, parts, nature = r
        cur.execute("""
            UPDATE analysis_result
            SET production_stage=%s, production_substage=%s,
                part_category=%s::text[], part_name=%s::text[],
                problem_nature=%s
            WHERE id=%s
        """, (stage, substage, cats, parts, nature, a_id))
        updated += 1
        print(f"  dataset_info_id={d_id} -> {stage}/{substage} | {','.join(parts)} | {nature} | {text[:25]}")
    conn.commit()
    print(f"完成：更新 {updated} 条")
    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
