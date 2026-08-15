"""数据导入蓝图：POST /api/dataset/import

接收 xlsx 文件，解析后写入 dataset_info 表。
Excel 格式约定：
- 第 1 行：中文表头（跳过）
- 第 2 行：英文字段名（对应数据库列名，用作列映射）
- 第 3 行起：数据
"""
import io
from datetime import datetime

import openpyxl
from flask import Blueprint, jsonify, request
from sqlalchemy.exc import SQLAlchemyError

from ..db import db
from ..models import DatasetInfo
from ..services.product_catalog import lookup_catalog_product

bp = Blueprint("dataset", __name__, url_prefix="/api/dataset")

# 完整格式的旧模板仍要求这些字段；如果提供 source_product_id，则其余字段可省略。
REQUIRED_FIELDS = [
    "customer_transcript",
    "touchpoint",
    "category_l1",
    "category_l2",
    "category_l3",
    "sku",
    "platform",
]

PRODUCT_ID_FIELDS = {"source_product_id", "product_id", "商品id", "商品 ID", "商品ID", "产品id", "产品ID"}

# 用于定位“字段名行”的关键列
KNOWN_FIELDS = {"customer_transcript", "touchpoint", "category_l1", "sku"}

# 数据库列名 -> 中文表头（仅用于错误提示）
FIELD_LABELS = {
    "customer_transcript": "客户原文",
    "touchpoint": "触点渠道",
    "category_l1": "一级分类",
    "category_l2": "二级分类",
    "category_l3": "三级分类",
    "sku": "SKU编码",
    "platform": "购买平台",
}

FIELD_ALIASES = {
    "customer_transcript": "customer_transcript",
    "customer_review": "customer_transcript",
    "客户评价": "customer_transcript",
    "客户原文": "customer_transcript",
    "touchpoint": "touchpoint",
    "触点渠道": "touchpoint",
    "source_form": "source_form",
    "原始形态": "source_form",
    "category_l1": "category_l1",
    "一级分类": "category_l1",
    "category_l2": "category_l2",
    "二级分类": "category_l2",
    "category_l3": "category_l3",
    "三级分类": "category_l3",
    "sku": "sku",
    "sku编码": "sku",
    "购买平台": "platform",
    "platform": "platform",
    "商品id": "source_product_id",
    "商品id": "source_product_id",
    "商品 ID": "source_product_id",
    "商品ID": "source_product_id",
    "产品id": "source_product_id",
    "产品ID": "source_product_id",
    "product_id": "source_product_id",
    "source_product_id": "source_product_id",
}


def _normalize_field(value):
    """兼容英文模板和常见中文表头。"""
    value = _clean_value(value)
    if value is None:
        return None
    compact = value.lower().replace(" ", "").replace("_", "")
    for alias, field in FIELD_ALIASES.items():
        if alias.lower().replace(" ", "").replace("_", "") == compact:
            return field
    return value


def _clean_value(value):
    """统一去除空白，返回 None 表示空值。"""
    if value is None:
        return None
    s = str(value).strip()
    return s if s else None


def _convert(value, field):
    """按字段类型转换：是/否→bool、金额→float、其余保留。"""
    if value is None:
        return None
    if field == "source_product_id":
        return str(value).strip()
    if field == "is_gift":
        if value in ("是", "true", "True", "TRUE", "1"):
            return True
        if value in ("否", "false", "False", "FALSE", "0"):
            return False
        return value
    if field in ("paid_amount", "original_amount"):
        try:
            return float(value)
        except ValueError:
            return None
    return value


def _locate_header_row(ws):
    """找到英文字段名行，或只有商品 ID 的简化字段名行。"""
    candidates = []
    for r in range(1, min(ws.max_row, 5) + 1):
        raw_values = [_clean_value(ws.cell(row=r, column=c).value) for c in range(1, ws.max_column + 1)]
        values = [_normalize_field(value) for value in raw_values]
        if "customer_transcript" in values or "touchpoint" in values:
            return r, values
        if "source_product_id" in values:
            candidates.append((r, values))
    if candidates:
        return candidates[0]
    return None, None


def _enrich_from_product_catalog(rec):
    """用商品 ID 补齐 SKU 和品类；用户显式填写的值优先。"""
    source_product_id = rec.get("source_product_id")
    if not source_product_id:
        return rec, False
    catalog = lookup_catalog_product(source_product_id)
    if catalog:
        for field in ("sku", "category_l1", "category_l2", "category_l3"):
            if not rec.get(field):
                rec[field] = catalog[field]
        rec["source_product_id"] = catalog["source_product_id"]
        matched = True
    else:
        rec.setdefault("sku", source_product_id)
        rec.setdefault("category_l1", "其他")
        rec.setdefault("category_l2", "未识别")
        rec.setdefault("category_l3", "待人工确认")
        matched = False

    # 保持现有数据库 NOT NULL 约束，同时明确标记“只提供商品 ID”的缺省字段。
    rec.setdefault("customer_transcript", "未提供客户原文")
    rec.setdefault("touchpoint", "S1")
    rec.setdefault("platform", "未提供")
    return rec, matched


@bp.post("/record")
def insert_dataset_record():
    """逐条写入 dataset_info；仅商品 ID和客户评价为必填。"""
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"error": "请求体必须是 JSON 对象"}), 400

    allowed = {column.name for column in DatasetInfo.__table__.columns}
    rec = {}
    for key, value in payload.items():
        field = _normalize_field(key)
        if field == "customer_review":
            field = "customer_transcript"
        if field not in allowed:
            continue
        clean = _clean_value(value)
        rec[field] = _convert(clean, field)

    product_id = rec.get("source_product_id")
    transcript = rec.get("customer_transcript")
    if not product_id or not transcript:
        return jsonify({"error": "商品 ID 和客户评价具体内容不能为空"}), 400

    if isinstance(rec.get("complaint_time"), str):
        try:
            rec["complaint_time"] = datetime.fromisoformat(
                rec["complaint_time"].replace("Z", "+00:00")
            )
        except ValueError:
            return jsonify({"error": "complaint_time 必须是 ISO 日期时间格式"}), 400

    rec, matched = _enrich_from_product_catalog(rec)
    try:
        row = DatasetInfo(**rec)
        db.session.add(row)
        db.session.commit()
    except SQLAlchemyError as exc:
        db.session.rollback()
        return jsonify({"error": f"写入数据库失败：{exc}"}), 500

    return jsonify(
        {
            "id": row.id,
            "source_product_id": row.source_product_id,
            "sku": row.sku,
            "category_l1": row.category_l1,
            "category_l2": row.category_l2,
            "category_l3": row.category_l3,
            "catalog_matched": matched,
        }
    ), 201


@bp.post("/import")
def import_dataset():
    file = request.files.get("file")
    if file is None or file.filename == "":
        return jsonify({"error": "请上传 xlsx 文件（字段名 file）"}), 400

    if not file.filename.lower().endswith(".xlsx"):
        return jsonify({"error": "仅支持 .xlsx 文件"}), 400

    try:
        wb = openpyxl.load_workbook(io.BytesIO(file.read()), data_only=True)
    except Exception as exc:  # noqa: BLE001
        return jsonify({"error": f"文件解析失败：{exc}"}), 400

    ws = wb.active
    header_row, fields = _locate_header_row(ws)
    if header_row is None:
        return jsonify({"error": "未找到字段名行（应含 customer_transcript 等列）"}), 400

    records = []
    for r in range(header_row + 1, ws.max_row + 1):
        rec = {}
        for c, field in enumerate(fields, start=1):
            raw = _clean_value(ws.cell(row=r, column=c).value)
            rec[field] = _convert(raw, field)
        # 整行为空则跳过
        if all(v is None for v in rec.values()):
            continue
        records.append((r, rec))

    # 商品 ID 模式：只填 source_product_id / 商品id 即可；其余字段按目录自动补齐。
    errors = []
    valid = []
    catalog_matched = 0
    catalog_unmatched = 0
    for row_no, rec in records:
        if rec.get("source_product_id"):
            rec, matched = _enrich_from_product_catalog(rec)
            catalog_matched += int(matched)
            catalog_unmatched += int(not matched)
            missing = [f for f in ("sku", "category_l1", "category_l2", "category_l3") if not rec.get(f)]
        else:
            missing = REQUIRED_FIELDS
            missing = [f for f in missing if not rec.get(f)]
        if missing:
            labels = "、".join(FIELD_LABELS.get(f, f) for f in missing)
            errors.append({"row": row_no, "error": f"缺少必填字段：{labels}"})
            continue
        valid.append(rec)

    if not valid:
        return jsonify({"imported": 0, "errors": errors, "total": len(records)}), 400

    try:
        db.session.add_all(DatasetInfo(**rec) for rec in valid)
        db.session.commit()
    except SQLAlchemyError as exc:
        db.session.rollback()
        return jsonify({"error": f"写入数据库失败：{exc}"}), 500

    return jsonify(
        {
            "imported": len(valid),
            "errors": errors,
            "total": len(records),
            "catalog_matched": catalog_matched,
            "catalog_unmatched": catalog_unmatched,
        }
    )
