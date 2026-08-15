"""本地商品目录导入与规则分类。

商品源文件是“一个工作表一个商品”的参数抓取结果。本模块不调用模型，
仅使用商品参数和 SKU 前缀进行可审计的分类，并保留原始 JSON 供人工复核。
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

import openpyxl
import psycopg2
from flask import current_app


@dataclass(frozen=True)
class ProductClassification:
    category_l1: str
    category_l2: str
    category_l3: str
    confidence: float
    rule: str


def lookup_catalog_product(source_product_id: str) -> dict | None:
    """从独立 product_catalog 数据库读取一个商品的规范 SKU 和品类。"""
    source_product_id = str(source_product_id).strip()
    if not source_product_id:
        return None
    config = current_app.config
    try:
        conn = psycopg2.connect(
            host=config["DB_HOST"],
            port=config["DB_PORT"],
            user=config["DB_USER"],
            password=config["DB_PASSWORD"],
            dbname=config.get("CATALOG_DB_NAME", "product_catalog"),
            connect_timeout=3,
        )
    except Exception:  # 目录库未创建时不阻断旧格式导入
        return None
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT source_product_id, sku, category_l1, category_l2, category_l3
                FROM product_catalog WHERE source_product_id = %s
                """,
                (source_product_id,),
            )
            row = cur.fetchone()
            if row is None:
                return None
            return {
                "source_product_id": row[0],
                "sku": row[1],
                "category_l1": row[2],
                "category_l2": row[3],
                "category_l3": row[4],
            }
    finally:
        conn.close()


def _text(params: dict[str, str]) -> str:
    return " ".join(f"{key}={value}" for key, value in params.items()).lower()


def _sku(product_id: str, params: dict[str, str]) -> str:
    value = str(params.get("型号") or params.get("货号") or "").strip()
    # “1”这类抓取占位值不是可用 SKU，改用稳定的商品 ID。
    return value if len(value) >= 3 else product_id


def classify_product(product_id: str, params: dict[str, str], sku: str) -> ProductClassification:
    text = _text(params)
    prefix_match = re.match(r"[A-Z]+", sku.upper())
    prefix = prefix_match.group(0) if prefix_match else ""

    if "咖啡机" in text or prefix == "KFJ":
        return ProductClassification("厨电", "饮品冲调", "咖啡机", 0.99, "咖啡机参数/ KFJ 前缀")
    if "养生壶" in text or "煮茶器" in text or prefix in {"YSH", "ZCQ"}:
        return ProductClassification("厨电", "壶类", "养生壶", 0.99, "商品品类或 YSH/ZCQ 前缀")
    if "原汁机" in text or prefix == "YZJ":
        return ProductClassification("厨电", "榨汁类", "原汁机", 0.99, "商品品类或 YZJ 前缀")
    if "榨汁机" in text or prefix == "LLJ":
        return ProductClassification("厨电", "榨汁类", "榨汁机", 0.99, "商品品类或 LLJ 前缀")
    if prefix == "PBJ":
        return ProductClassification("厨电", "电动类", "破壁机", 0.98, "PBJ 前缀")
    if prefix == "DJJ":
        return ProductClassification("厨电", "电动类", "料理机", 0.96, "DJJ 前缀及料理参数")
    if prefix == "QSJ":
        return ProductClassification("厨电", "电动类", "绞菜机", 0.97, "产品类别或 QSJ 前缀")
    if prefix == "MDJ":
        return ProductClassification("厨电", "电动类", "研磨机", 0.96, "研磨参数或 MDJ 前缀")
    if "面条机" in text or prefix == "YMJ":
        return ProductClassification("厨电", "面食类", "面条机", 0.99, "面条机参数或 YMJ 前缀")
    if "和面机" in text or prefix == "HMJ":
        return ProductClassification("厨电", "面食类", "和面机", 0.99, "商品品类或 HMJ 前缀")
    if prefix == "SJJ":
        return ProductClassification("母婴小家电", "喂养护理", "辅食机", 0.95, "婴幼儿适用年龄及 SJJ 前缀")
    if prefix in {"DDZ", "ZDQ"} and "电炖盅" in text:
        return ProductClassification("厨电", "锅煲类", "电炖盅", 0.99, "电炖锅类型参数")
    if prefix == "DDZ":
        return ProductClassification("厨电", "锅煲类", "电炖盅", 0.96, "DDZ 前缀")
    if prefix == "DDG" or "电炖锅" in text:
        return ProductClassification("厨电", "锅煲类", "电炖锅", 0.98, "电炖锅类型或 DDG 前缀")
    if prefix == "DSG" or "电砂锅" in text:
        return ProductClassification("厨电", "锅煲类", "电砂锅", 0.98, "电炖锅类型或 DSG 前缀")
    if prefix == "DFB" or "电饭煲" in text:
        return ProductClassification("厨电", "锅煲类", "电饭煲", 0.99, "电饭煲多功能参数或 DFB 前缀")
    if prefix == "DFH":
        return ProductClassification("厨电", "电热类", "电热饭盒", 0.97, "加热/分层饭盒参数或 DFH 前缀")
    if prefix == "DHG":
        return ProductClassification("厨电", "锅煲类", "电煮锅", 0.99, "产品类别或 DHG 前缀")
    if prefix == "DTL":
        return ProductClassification("厨电", "电热类", "电磁炉", 0.99, "电磁炉参数或 DTL 前缀")
    if prefix == "DBC" or "电饼铛" in text:
        return ProductClassification("厨电", "电热类", "电饼铛", 0.99, "电饼铛参数或 DBC 前缀")
    if prefix == "ZDQ" or "煮蛋器" in text:
        return ProductClassification("厨电", "电热类", "煮蛋器", 0.99, "煮蛋器参数或 ZDQ 前缀")
    if prefix == "SNJ":
        return ProductClassification("厨电", "发酵类", "酸奶机", 0.99, "酸奶机参数或 SNJ 前缀")
    if prefix == "DDQ":
        return ProductClassification("厨电", "电动类", "电动打蛋器", 0.92, "手持/档位参数及 DDQ 前缀")
    if prefix == "ZTD":
        return ProductClassification("厨电", "消毒护理", "消毒柜", 0.99, "紫外线消毒及 ZTD 前缀")
    if prefix == "JSQ" or "加湿器分类" in text:
        return ProductClassification("生活小家电", "环境电器", "加湿器", 0.99, "加湿器参数或 JSQ 前缀")
    if prefix == "XYJ":
        if "内衣" in text or "内裤" in text:
            return ProductClassification("生活小家电", "洗护清洁", "内衣洗衣机", 0.98, "适用对象及 XYJ 前缀")
        return ProductClassification("生活小家电", "洗护清洁", "洗衣机", 0.99, "洗衣机/洗烘参数及 XYJ 前缀")
    if prefix == "DYD":
        return ProductClassification("生活小家电", "衣物护理", "挂烫机", 0.99, "商品品类或 DYD 前缀")
    if prefix == "HGJ":
        return ProductClassification("生活小家电", "衣物护理", "便携干衣机", 0.96, "烘干参数及 HGJ 前缀")
    if prefix == "ZFQ":
        return ProductClassification("个护小家电", "美容护理", "直发器", 0.99, "商品品类或 ZFQ 前缀")
    if prefix == "AMQ":
        return ProductClassification("个护小家电", "按摩护理", "眼部按摩仪", 0.99, "眼部润眼仪参数或 AMQ 前缀")
    if prefix == "ZYP" or "足浴器品牌" in text or "足疗机品牌" in text:
        product = "足浴器" if prefix == "ZYP" else "足疗机"
        return ProductClassification("个护小家电", "按摩护理", product, 0.98, "足浴/足疗参数")
    if prefix == "DFS":
        return ProductClassification("生活小家电", "环境电器", "电风扇", 0.99, "电风扇参数或 DFS 前缀")
    if prefix == "XCQ":
        return ProductClassification("生活小家电", "清洁电器", "吸尘器", 0.99, "吸尘器参数或 XCQ 前缀")
    if prefix == "MW":
        return ProductClassification("母婴小家电", "喂养护理", "奶瓶刷", 0.99, "商品品类或 MW 前缀")
    if prefix == "CX":
        product = "保温提锅" if "提锅" in text else "保温杯"
        return ProductClassification("生活小家电", "杯壶用品", product, 0.96, "保温杯/提锅参数及 CX 前缀")
    if prefix == "YSJ":
        return ProductClassification("生活小家电", "饮水设备", "便携饮水机", 0.91, "食品级水路/出水模式参数及 YSJ 前缀")
    if prefix == "ZDH":
        return ProductClassification("生活小家电", "饮水设备", "台式饮水机", 0.94, "水箱/沸腾除氯参数及 ZDH 前缀")
    if sku == "10004786":
        return ProductClassification("生活小家电", "厨房用品", "厨房秤", 0.88, "厨房使用环境及称重参数")
    if sku == "10000721":
        return ProductClassification("生活小家电", "洗护清洁", "洗衣机配件", 0.55, "颜色分类为洗衣舱配件；待人工复核")
    if sku == "1":
        return ProductClassification("个护小家电", "按摩护理", "足疗机", 0.92, "足疗机品牌字段")
    return ProductClassification("其他", "未识别", "待人工确认", 0.20, "缺少可识别商品类型字段；待人工复核")


def read_product_workbook(path: str | Path) -> list[dict]:
    workbook = openpyxl.load_workbook(path, data_only=True, read_only=True)
    products = []
    for sheet in workbook.worksheets:
        params = {
            str(row[0].value).strip(): row[1].value
            for row in sheet.iter_rows()
            if row[0].value is not None and row[1].value is not None
        }
        product_id = str(params.get("商品id") or sheet.title).strip()
        normalized = {key: str(value).strip() for key, value in params.items()}
        sku = _sku(product_id, normalized)
        classification = classify_product(product_id, normalized, sku)
        products.append(
            {
                "source_product_id": product_id,
                "source_sheet": sheet.title,
                "source_url": normalized.get("商品链接"),
                "sku": sku,
                "category_l1": classification.category_l1,
                "category_l2": classification.category_l2,
                "category_l3": classification.category_l3,
                "confidence": classification.confidence,
                "classification_rule": classification.rule,
                "raw_params": normalized,
            }
        )
    return products
