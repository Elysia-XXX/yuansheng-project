# -*- coding: utf-8 -*-
"""将问大家(S4)中 production_substage='首次使用指导' 的记录，
依据问题文本语义细分为「购买咨询」下的四类子标签，并写入数据库。

四类：
  效果咨询：询问使用效果、性能、质量、干净程度、声音、快慢、口感等
  功能咨询：询问能否做某事、容量、档位、模式、适用场景等
  操作咨询：询问怎么操作、怎么清洗、怎么换水、怎么安装等
  其他咨询：购买建议、推荐、颜色、价格、尺寸、材质、品牌对比等

用法：python rule_refine_guide.py
"""
import psycopg2

conf = {
    "host": "127.0.0.1", "port": "55433", "user": "postgres",
    "password": "", "dbname": "postgres",
}

# 操作咨询关键词：问怎么做/怎么用/怎么清洗/怎么装
OPERATE = ["怎么", "如何", "操作", "换水", "加水", "倒水", "放水", "清洗", "拆洗", "清洁",
           "安装", "拆", "装", "接水", "上水", "下水", "用水", "排", "洗器具", "保养",
           "能不能用", "怎么用", "要不要加水", "需要加水", "要自己", "用手", "手洗"]

# 功能咨询关键词：问能不能做某事/容量/档位/模式/适用
FUNCTION = ["能洗", "能蒸", "能炖", "能打", "能搅", "能绞", "能磨", "能压", "能加热",
            "能摇头", "能带", "能不能", "可以吗", "可以洗", "可以蒸", "可以打", "可以搅",
            "可以绞", "可以磨", "可以炖", "可以脱水", "可以", "能不能", "容量", "多大",
            "几件", "几双", "几升", "够用", "够吗", "放下", "大小", "档位", "模式",
            "预约", "定时", "速洗", "高温", "几度", "功率", "瓦", "几档", "功能", "适用",
            "支持", "能装", "能放", "能放下", "几几", "同时"]

# 效果咨询关键词：问效果/性能/质量/干净/声音/快慢/口感/耐用
EFFECT = ["干净", "洗干净", "洗净", "去污", "洗掉", "好用", "质量", "品质", "声音",
          "噪音", "响", "吵", "静音", "安静", "快不", "快吗", "慢", "分钟", "多久",
          "长时间", "效果", "口感", "好吃", "味道", "香味", "粘稠", "细腻", "烂",
          "软烂", "熟透", "发烫", "发热", "烫", "容易坏", "耐用", "故障", "坏了",
          "半年", "一年", "风力", "凉快", "散热", "甩干", "烘干", "脱得干", "保温",
          "加热快", "快不快", "舒服", "遮光", "助眠", "坚固", "结实", "脱水", "脱干净",
          "转不动", "转不", "能不能洗干净", "怎么样", "好不好", "洗的干", "洗得干",
          "能洗干净", "能洗干", "去味", "异味", "气味", "结实", "安全", "密封"]

# 其他咨询关键词：购买建议/推荐/对比/颜色/价格/尺寸/材质/保修/品牌
OTHER = ["推荐", "值得", "购买", "买哪个", "哪个好", "选择", "有必要", "要不要买",
         "颜色", "好看", "多少钱", "价格", "活动", "入手", "贵", "性价比", "尺寸",
         "直径", "高", "重", "重吗", "大不大", "厚", "材质", "不锈钢", "塑料", "玻璃",
         "陶瓷", "硅胶", "保修", "质保", "售后", "保几年", "哪个牌", "对比", "区别"]


def classify(text):
    t = str(text or "")
    # 效果优先（“能洗干净吗”更偏效果）
    if any(k in t for k in EFFECT):
        return "效果咨询"
    if any(k in t for k in OPERATE):
        return "操作咨询"
    if any(k in t for k in FUNCTION):
        return "功能咨询"
    return "其他咨询"


def main():
    conn = psycopg2.connect(**conf)
    cur = conn.cursor()
    cur.execute("""
        SELECT d.id, d.customer_transcript
        FROM dataset_info d
        JOIN analysis_result a ON a.dataset_info_id = d.id
        WHERE d.touchpoint='S4' AND a.production_substage = %s
        ORDER BY d.id
    """, ("首次使用指导",))
    rows = cur.fetchall()
    print(f"待细分：{len(rows)} 条")

    stats = {}
    updates = []
    for d_id, text in rows:
        label = classify(text)
        stats[label] = stats.get(label, 0) + 1
        updates.append((label, d_id))

    for label, cnt in stats.items():
        print(f"  {label}: {cnt}")

    cur.executemany(
        "UPDATE analysis_result SET production_stage=%s, production_substage=%s WHERE dataset_info_id=%s",
        [("购买咨询", label, d_id) for label, d_id in updates],
    )
    conn.commit()
    print(f"已更新 {len(updates)} 条：production_stage=购买咨询，substage 细分完成")
    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
