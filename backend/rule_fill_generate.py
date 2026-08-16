# -*- coding: utf-8 -*-
"""生成问大家(S4)生产环节/部件/问题性质答案文件，不写库。

用法：python rule_fill_generate.py
输出：
  rule_fill_output.json   —— 全部待处理记录的推断结果
  rule_fill_unmatched.txt —— 未命中规则的问题清单
"""
import json
import os

import psycopg2

BACKEND = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BACKEND, "rule_fill_output.json")
UNMATCHED = os.path.join(BACKEND, "rule_fill_unmatched.txt")

conf = {
    "host": "127.0.0.1", "port": "55433", "user": "postgres",
    "password": "", "dbname": "postgres",
}

# (关键词列表, stage, substage, [part_category], [part_name], problem_nature)
RULES = [
    (["漏", "渗水", "滴水"], "生产制造", "组装", ["密封与紧固"], ["密封圈/密封垫"], "质量缺陷"),
    (["涂层", "掉漆", "脱落"], "原材料", "涂层", ["结构壳体"], ["机身外壳"], "质量缺陷"),
    (["糊底"], "生产制造", "组装", ["容器内胆"], ["内胆/锅体（炖锅/饭煲）"], "质量缺陷"),
    (["电池", "续航", "充电", "电量", "耐用"], "原材料", "电子元器件", ["线束与电源"], ["电池包"], "功能不符"),
    (["不转", "不工作", "没反应", "转不动", "故障", "容易坏", "按键", "失灵", "噪音"], "生产制造", "组装", ["动力系统"], ["电机"], "质量缺陷"),
    (["清洗", "换水", "清洁", "拆", "拧干", "脱水", "泡沫"], "安装调试", "首次使用指导", ["功能执行件"], ["滤网/滤篮"], "体验不佳"),
    (["干净", "洗干净", "洗净", "去污", "血", "分泌物", "经血", "抹布"], "安装调试", "首次使用指导", [], [], "体验不佳"),
    (["好用", "方便", "多大", "多久", "多少", "能不能", "可以吗", "能洗", "值得", "质量", "适合", "推荐", "购买", "好用吗", "怎么样", "放"], "安装调试", "首次使用指导", [], [], "体验不佳"),
]

DEFAULT = ("安装调试", "首次使用指导", [], [], "体验不佳")


def infer(text):
    t = str(text or "")
    for keywords, stage, substage, cats, parts, nature in RULES:
        if any(k in t for k in keywords):
            return stage, substage, cats, parts, nature
    return None


def main():
    conn = psycopg2.connect(**conf)
    cur = conn.cursor()
    cur.execute("""
        SELECT d.id, d.customer_transcript
        FROM analysis_result a
        JOIN dataset_info d ON a.dataset_info_id = d.id
        WHERE d.touchpoint='S4'
          AND (a.production_stage IS NULL OR a.production_stage='')
        ORDER BY d.id
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()

    outputs = []
    unmatched = []
    for d_id, text in rows:
        r = infer(text)
        if r is None:
            stage, substage, cats, parts, nature = DEFAULT
            unmatched.append(f"{d_id}\t{text}")
        else:
            stage, substage, cats, parts, nature = r
        outputs.append({
            "dataset_info_id": d_id,
            "production_stage": stage,
            "production_substage": substage,
            "part_category": cats,
            "part_name": parts,
            "problem_nature": nature,
        })

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(outputs, f, ensure_ascii=False, indent=2)
    with open(UNMATCHED, "w", encoding="utf-8") as f:
        f.write("\n".join(unmatched) + ("\n" if unmatched else ""))

    print(f"待处理 {len(rows)} 条 -> 已生成 {len(outputs)} 条结果到 {OUT}")
    print(f"未命中规则（走默认体验不佳）：{len(unmatched)} 条，清单见 {UNMATCHED}")


if __name__ == "__main__":
    main()
