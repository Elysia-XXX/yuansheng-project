"""客户评价管理：聚合 dataset_info 与 analysis_result。"""
from datetime import date, datetime
from decimal import Decimal

from flask import Blueprint, jsonify, request
from sqlalchemy import asc, desc

from ..db import db
from ..models import AnalysisResult, DatasetInfo

bp = Blueprint("reviews", __name__, url_prefix="/api/reviews")

LIST_FIELDS = (
    "dataset_info_id", "category_l1", "category_l2", "category_l3", "sku",
    "touchpoint", "platform", "function_tag_l1", "evaluation_level", "emotion_dimension",
    "problem_nature", "appeal_intent", "analysis_status",
)
SORT_FIELDS = {"id": DatasetInfo.id, "created_at": DatasetInfo.created_at}
DATASET_DETAIL_FIELDS = (
    "id", "source_product_id", "customer_transcript", "touchpoint", "source_form",
    "category_l1", "category_l2", "category_l3", "sku", "region", "province",
    "city_tier", "gender", "age", "use_scene", "user_type", "member_level",
    "price_band", "paid_amount", "original_amount", "platform", "promo_type",
    "warranty_status", "is_gift", "complaint_time", "duration_to_complaint",
    "product_season", "complaint_season", "lifecycle_stage", "created_at",
)
ANALYSIS_DETAIL_FIELDS = (
    "id", "dataset_info_id", "function_tag_l1", "function_tag_l2", "production_stage",
    "production_substage", "part_category", "part_name", "evaluation_level", "emotion_dimension",
    "problem_nature", "keyword_cluster", "appeal_intent", "created_at",
)


def _json_value(value):
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    return value


def _serialize(model, fields):
    return {field: _json_value(getattr(model, field)) for field in fields}


def _filter_value(query, field, value):
    if value:
        query = query.filter(field == value)
    return query


@bp.get("")
def list_reviews():
    try:
        page = max(int(request.args.get("page", 1)), 1)
        page_size = min(max(int(request.args.get("page_size", 20)), 1), 100)
    except (TypeError, ValueError):
        return jsonify({"error": "page 和 page_size 必须是整数"}), 400

    query = db.session.query(DatasetInfo, AnalysisResult).outerjoin(
        AnalysisResult, AnalysisResult.dataset_info_id == DatasetInfo.id
    )
    dataset_filters = {
        "category_l1": DatasetInfo.category_l1, "category_l2": DatasetInfo.category_l2,
        "category_l3": DatasetInfo.category_l3, "sku": DatasetInfo.sku,
        "touchpoint": DatasetInfo.touchpoint, "platform": DatasetInfo.platform,
    }
    analysis_filters = {
        "function_tag_l1": AnalysisResult.function_tag_l1,
        "evaluation_level": AnalysisResult.evaluation_level,
        "emotion_dimension": AnalysisResult.emotion_dimension,
        "problem_nature": AnalysisResult.problem_nature,
        "appeal_intent": AnalysisResult.appeal_intent,
    }
    for name, field in {**dataset_filters, **analysis_filters}.items():
        query = _filter_value(query, field, request.args.get(name))

    status = request.args.get("analysis_status", "all")
    if status == "analyzed":
        query = query.filter(AnalysisResult.id.isnot(None))
    elif status == "pending":
        query = query.filter(AnalysisResult.id.is_(None))
    elif status != "all":
        return jsonify({"error": "analysis_status 只能是 analyzed、pending 或 all"}), 400

    total = query.count()
    sort_field = SORT_FIELDS.get(request.args.get("sort_by", "id"), DatasetInfo.id)
    order = desc(sort_field) if request.args.get("sort_order", "desc").lower() == "desc" else asc(sort_field)
    rows = query.order_by(order).offset((page - 1) * page_size).limit(page_size).all()
    items = []
    for dataset, analysis in rows:
        items.append({
            "dataset_info_id": dataset.id,
            "category_l1": dataset.category_l1,
            "category_l2": dataset.category_l2,
            "category_l3": dataset.category_l3,
            "sku": dataset.sku,
            "touchpoint": dataset.touchpoint,
            "platform": dataset.platform,
            "function_tag_l1": analysis.function_tag_l1 if analysis else None,
            "evaluation_level": analysis.evaluation_level if analysis else None,
            "emotion_dimension": analysis.emotion_dimension if analysis else None,
            "problem_nature": analysis.problem_nature if analysis else None,
            "appeal_intent": analysis.appeal_intent if analysis else None,
            "analysis_status": "analyzed" if analysis else "pending",
        })
    return jsonify({
        "items": items, "total": total, "page": page, "page_size": page_size,
        "pages": (total + page_size - 1) // page_size,
    })


@bp.get("/<int:dataset_info_id>")
def detail_review(dataset_info_id):
    dataset = db.session.get(DatasetInfo, dataset_info_id)
    if dataset is None:
        return jsonify({"error": "评论不存在"}), 404
    analysis = AnalysisResult.query.filter_by(dataset_info_id=dataset_info_id).order_by(AnalysisResult.id.desc()).first()
    return jsonify({
        "dataset_info": _serialize(dataset, DATASET_DETAIL_FIELDS),
        "analysis_result": _serialize(analysis, ANALYSIS_DETAIL_FIELDS) if analysis else None,
    })
