"""Read-only analytics APIs consumed by the complaint-analysis dashboard."""
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime
from decimal import Decimal
from uuid import uuid4

from flask import Blueprint, jsonify, request
from sqlalchemy import func

from ..models import AnalysisResult, DatasetInfo
from ..schemas.complaint_analysis import FUNCTION_TAGS, PART_TO_CATEGORY

bp = Blueprint("analytics", __name__, url_prefix="/api/v1")

DIMENSION_TITLES = {
    "production": "生产环节分析",
    "parts": "产品部件分析",
    "function": "功能分析",
    "customer": "客户画像",
    "lifecycle": "生命周期分析",
    "orders": "订单交易分析",
    "semantic": "语义内容分析",
    "brand": "渠道与营销分析",
}

FUNCTION_LABELS = {
    "C1": "功能缺陷", "C2": "性能不达标", "C3": "质量故障",
    "C4": "安全隐患", "C5": "外观做工", "C6": "使用体验",
    "C7": "售后服务", "C8": "物流包装", "C9": "虚假宣传",
    "C10": "咨询建议",
}

SOURCE_TYPES = {
    "京东": ["商品评价", "客服聊天记录", "退货原因", "售后工单", "问大家"],
    "淘宝": ["商品评价", "客服聊天记录", "退货原因", "售后工单", "问大家"],
    "天猫": ["商品评价", "客服聊天记录", "退货原因", "售后工单", "问大家"],
    "小红书": ["种草笔记", "评论", "私信客服"],
    "企业客服电话": ["通话录音", "通话记录", "工单登记"],
}


def _meta(endpoint: str, query: dict | None = None) -> dict:
    return {
        "contractVersion": "1.0.0",
        "endpoint": endpoint,
        "method": "GET",
        "contentType": "application/json",
        "generatedAt": datetime.now().astimezone().isoformat(timespec="seconds"),
        "requestId": f"req_{uuid4().hex[:12]}",
        "query": query or {},
    }


def _response(endpoint: str, data: dict, query: dict | None = None):
    return jsonify({"meta": _meta(endpoint, query), "data": data})


def _month_key(value) -> str | None:
    if value is None:
        return None
    return value.strftime("%Y-%m")


def _month_shift(month: str, delta: int) -> str:
    year, number = map(int, month.split("-"))
    index = year * 12 + number - 1 + delta
    return f"{index // 12:04d}-{index % 12 + 1:02d}"


def _query_rows():
    """Return one flattened record per dataset row (latest analysis result wins)."""
    analysis = (
        AnalysisResult.query
        .order_by(AnalysisResult.dataset_info_id, AnalysisResult.id.desc())
        .all()
    )
    latest = {}
    for item in analysis:
        latest.setdefault(item.dataset_info_id, item)
    rows = []
    for item in DatasetInfo.query.order_by(DatasetInfo.id).all():
        analyzed = latest.get(item.id)
        rows.append({
            "id": item.id,
            "text": item.customer_transcript,
            "time": item.complaint_time or item.created_at,
            "touchpoint": item.touchpoint,
            "source_form": item.source_form,
            "category_l1": item.category_l1,
            "category_l2": item.category_l2,
            "category_l3": item.category_l3,
            "sku": item.sku,
            "region": item.region,
            "province": item.province,
            "city_tier": item.city_tier,
            "gender": item.gender,
            "age": item.age,
            "use_scene": item.use_scene,
            "user_type": item.user_type,
            "member_level": item.member_level,
            "price_band": item.price_band,
            "paid_amount": item.paid_amount,
            "original_amount": item.original_amount,
            "platform": item.platform,
            "promo_type": item.promo_type,
            "warranty_status": item.warranty_status,
            "is_gift": item.is_gift,
            "duration_to_complaint": item.duration_to_complaint,
            "product_season": item.product_season,
            "complaint_season": item.complaint_season,
            "lifecycle_stage": item.lifecycle_stage,
            "function_tag_l1": analyzed.function_tag_l1 if analyzed else None,
            "function_tag_l2": analyzed.function_tag_l2 or [] if analyzed else [],
            "production_stage": analyzed.production_stage if analyzed else None,
            "production_substage": analyzed.production_substage if analyzed else None,
            "part_category": analyzed.part_category or [] if analyzed else [],
            "part_name": analyzed.part_name or [] if analyzed else [],
            "evaluation_level": analyzed.evaluation_level if analyzed else None,
            "emotion_dimension": analyzed.emotion_dimension if analyzed else None,
            "problem_nature": analyzed.problem_nature if analyzed else None,
            "keyword_cluster": analyzed.keyword_cluster or [] if analyzed else [],
            "appeal_intent": analyzed.appeal_intent if analyzed else None,
            "qa_answers": item.qa_answers or [],
        })
    return rows


def _filtered_rows(rows, months: int = 6, end_month: str | None = None):
    available = sorted({_month_key(row["time"]) for row in rows if row["time"]})
    end = end_month if end_month in available else (available[-1] if available else datetime.now().strftime("%Y-%m"))
    start = _month_shift(end, -(months - 1))
    return [row for row in rows if (key := _month_key(row["time"])) and start <= key <= end], end


def _top(rows, field: str, limit: int = 6) -> list[tuple[str, int]]:
    counter = Counter()
    for row in rows:
        value = row.get(field)
        values = value if isinstance(value, list) else [value]
        for entry in values:
            if entry is not None and str(entry).strip():
                counter[str(entry)] += 1
    return counter.most_common(limit)


def _shares(items: list[tuple[str, int]]) -> list[int]:
    total = sum(count for _, count in items)
    return [round(count * 100 / total) if total else 0 for _, count in items]


def _complaint(row: dict) -> dict:
    profile = row.get("use_scene") or row.get("user_type") or row.get("region") or "未分类用户"
    return {
        "id": row["id"],
        "source": row.get("platform") or row.get("touchpoint") or "未知来源",
        "text": row.get("text") or "",
        "time": row["time"].isoformat(sep=" ", timespec="minutes") if row.get("time") else None,
        "profile": profile,
        "qa_answers": row.get("qa_answers") or [],
    }


def _leaf(label: str, rows: list[dict], meta: str | None = None) -> dict:
    node = {"label": label, "complaints": [_complaint(row) for row in rows]}
    if meta:
        node["meta"] = meta
    return node


def _group(rows: list[dict], field: str) -> dict[str, list[dict]]:
    result = defaultdict(list)
    for row in rows:
        value = row.get(field)
        values = value if isinstance(value, list) else [value]
        for entry in values:
            if entry is not None and str(entry).strip():
                result[str(entry)].append(row)
    return result


def _sectioned_tree(rows: list[dict], sections: list[tuple[str, str]]) -> list[dict]:
    tree = []
    for label, field in sections:
        groups = _group(rows, field)
        children = [_leaf(value, grouped) for value, grouped in sorted(groups.items(), key=lambda item: (-len(item[1]), item[0]))]
        tree.append({"label": label, "children": children})
    return tree


def _category_tree(rows: list[dict]) -> list[dict]:
    level1 = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    for row in rows:
        level1[row.get("category_l1") or "未分类"][row.get("category_l2") or "未分类"][row.get("category_l3") or "未分类"].append(row)
    tree = []
    for l1, l2s in sorted(level1.items()):
        l2_nodes = []
        for l2, l3s in sorted(l2s.items()):
            leaves = []
            for l3, grouped in sorted(l3s.items()):
                skus = sorted({row.get("sku") for row in grouped if row.get("sku")})
                meta = "SKU: " + "、".join(skus[:5]) if skus else None
                leaves.append(_leaf(l3, grouped, meta))
            l2_nodes.append({"label": l2, "children": leaves})
        tree.append({"label": l1, "children": l2_nodes})
    return tree


def _dimension_tree(dimension: str, rows: list[dict]) -> list[dict]:
    if dimension == "category":
        return _category_tree(rows)
    if dimension == "production":
        stages = _group(rows, "production_stage")
        return [{"label": stage, "children": [_leaf(name, values) for name, values in sorted(_group(grouped, "production_substage").items())]} for stage, grouped in sorted(stages.items())]
    if dimension == "parts":
        categories = _group(rows, "part_category")
        result = []
        for category, grouped in sorted(categories.items()):
            names = defaultdict(list)
            for row in grouped:
                for name in row.get("part_name", []):
                    if PART_TO_CATEGORY.get(name) == category:
                        names[name].append(row)
            result.append({"label": category, "children": [_leaf(name, values) for name, values in sorted(names.items())]})
        return result
    if dimension == "function":
        codes = _group(rows, "function_tag_l1")
        return [{"label": FUNCTION_LABELS.get(code, code), "meta": code, "children": [_leaf(name, values) for name, values in sorted(_group(grouped, "function_tag_l2").items())]} for code, grouped in sorted(codes.items())]
    if dimension == "customer":
        return _sectioned_tree(rows, [("大区", "region"), ("省份", "province"), ("城市线级", "city_tier"), ("性别", "gender"), ("年龄", "age"), ("使用场景", "use_scene"), ("用户类型", "user_type"), ("会员等级", "member_level")])
    if dimension == "lifecycle":
        return [_leaf(value, grouped) for value, grouped in sorted(_group(rows, "lifecycle_stage").items())]
    if dimension == "orders":
        normalized = []
        for row in rows:
            copy = dict(row)
            copy["is_gift_label"] = "是" if row.get("is_gift") is True else "否" if row.get("is_gift") is False else None
            copy["complaint_month"] = _month_key(row.get("time"))
            copy["paid_amount_label"] = str(row["paid_amount"]) if isinstance(row.get("paid_amount"), Decimal) else row.get("paid_amount")
            copy["original_amount_label"] = str(row["original_amount"]) if isinstance(row.get("original_amount"), Decimal) else row.get("original_amount")
            normalized.append(copy)
        return _sectioned_tree(normalized, [("购买价格带", "price_band"), ("实付金额", "paid_amount_label"), ("原价金额", "original_amount_label"), ("购买平台", "platform"), ("促销类型", "promo_type"), ("在保状态", "warranty_status"), ("是否赠品", "is_gift_label"), ("投诉月份", "complaint_month"), ("购买到投诉时长", "duration_to_complaint"), ("产品季节性", "product_season"), ("投诉季节", "complaint_season")])
    if dimension == "semantic":
        return _sectioned_tree(rows, [("评价等级", "evaluation_level"), ("情绪维度", "emotion_dimension"), ("问题性质", "problem_nature"), ("高频关键词簇", "keyword_cluster"), ("诉求意图", "appeal_intent")])
    if dimension == "brand":
        normalized = []
        for row in rows:
            copy = dict(row)
            copy["is_gift_label"] = "是" if row.get("is_gift") is True else "否" if row.get("is_gift") is False else None
            normalized.append(copy)
        return _sectioned_tree(normalized, [("购买平台", "platform"), ("触点渠道", "touchpoint"), ("促销类型", "promo_type"), ("是否赠品", "is_gift_label")])
    return []


def _dimension_fields(dimension: str) -> list[str]:
    return {
        "production": ["production_stage", "production_substage"],
        "parts": ["part_category", "part_name"],
        "function": ["function_tag_l1", "function_tag_l2"],
        "customer": ["region", "province", "city_tier", "gender", "age", "use_scene", "user_type", "member_level"],
        "lifecycle": ["lifecycle_stage"],
        "orders": ["price_band", "platform", "promo_type", "warranty_status", "duration_to_complaint", "product_season", "complaint_season"],
        "semantic": ["evaluation_level", "emotion_dimension", "problem_nature", "keyword_cluster", "appeal_intent"],
        "brand": ["platform", "touchpoint", "promo_type"],
    }.get(dimension, [])


@bp.get("/dashboard/home")
def home_dashboard():
    rows = _query_rows()
    month_counts = Counter(_month_key(row["time"]) for row in rows if row["time"])
    available = sorted(month_counts)
    end = request.args.get("month")
    if end not in available:
        end = available[-1] if available else datetime.now().strftime("%Y-%m")
    series_months = [_month_shift(end, offset) for offset in range(-11, 1)]
    months = {}
    for month in series_months:
        selected = [row for row in rows if _month_key(row["time"]) == month]
        def values(field):
            items = _top(selected, field, 5)
            return [name for name, _ in items], [count for _, count in items]
        category_labels, category = values("category_l2")
        production_labels, production = values("production_stage")
        profile_labels, profile = values("use_scene")
        platform_labels, platform = values("platform")
        months[month] = {
            "total": len(selected), "previous": month_counts.get(_month_shift(month, -1), 0),
            "category": category, "categoryLabels": category_labels,
            "production": production, "productionLabels": production_labels,
            "profile": profile, "profileLabels": profile_labels,
            "platform": platform, "platformLabels": platform_labels,
        }
    return _response("/api/v1/dashboard/home", {"months": months, "monthSeries": {month: month_counts.get(month, 0) for month in series_months}}, {"month": end})


@bp.get("/analysis/category/dashboard")
def category_dashboard():
    rows = _query_rows()
    filtered, end = _filtered_rows(rows, 6, request.args.get("endMonth"))
    month_series = Counter(_month_key(row["time"]) for row in rows if row["time"])
    products = _top(filtered, "category_l3", 10)
    previous_rows, _ = _filtered_rows(rows, 6, _month_shift(end, -1))
    previous = dict(_top(previous_rows, "category_l3", 1000))
    top_products = []
    for name, count in products:
        old = previous.get(name, 0)
        trend = ((count - old) * 100 / old) if old else (100.0 if count else 0.0)
        top_products.append({"name": name, "count": count, "trend": f"{trend:+.1f}%", "down": trend < 0})
    series_keys = [_month_shift(end, offset) for offset in range(-11, 1)]
    level1 = _top(filtered, "category_l1", 8)
    level2 = _top(filtered, "category_l2", 10)
    return _response("/api/v1/analysis/category/dashboard", {
        "monthSeries": {key: month_series.get(key, 0) for key in series_keys},
        "topProducts": top_products,
        "level1": [{"name": name, "count": count} for name, count in level1],
        "level2": [{"name": name, "count": count} for name, count in level2],
    }, {"endMonth": end, "months": 6})


@bp.get("/analysis/<dimension>/dashboard")
def dimension_dashboard(dimension: str):
    if dimension not in DIMENSION_TITLES:
        return jsonify({"error": "未知分析维度"}), 404
    rows = _query_rows()
    filtered, end = _filtered_rows(rows, 6, request.args.get("endMonth"))
    fields = _dimension_fields(dimension)
    primary = fields[0]
    secondary_items = _top(filtered, primary, 6)
    tag_counter = Counter()
    for field in fields[1:] or fields:
        tag_counter.update(dict(_top(filtered, field, 1000)))
    tags = [name for name, _ in tag_counter.most_common(10)]
    overall = len(filtered)
    dimension_total = sum(1 for row in filtered if any(row.get(field) for field in fields))
    series_keys = [_month_shift(end, offset) for offset in range(-11, 1)]
    dimension_months = Counter(
        _month_key(row["time"])
        for row in rows
        if row["time"] and any(row.get(field) for field in fields)
    )
    return _response(f"/api/v1/analysis/{dimension}/dashboard", {
        "title": DIMENSION_TITLES[dimension],
        "secondary": [name for name, _ in secondary_items],
        "shares": _shares(secondary_items),
        "tags": tags,
        "topTags": [{"name": name, "count": count} for name, count in tag_counter.most_common(10)],
        "factor": dimension_total / overall if overall else 0,
        "monthSeries": {key: dimension_months.get(key, 0) for key in series_keys},
        "summary": {"total": dimension_total, "peakSecondary": secondary_items[0][0] if secondary_items else "暂无数据", "riskTagCount": min(3, len(tags))},
    }, {"endMonth": end, "months": 6})


@bp.get("/analysis/<dimension>/complaints")
def dimension_complaints(dimension: str):
    if dimension not in {*DIMENSION_TITLES, "category"}:
        return jsonify({"error": "未知分析维度"}), 404
    try:
        months = max(1, min(24, int(request.args.get("months", 6))))
    except (TypeError, ValueError):
        return jsonify({"error": "months 必须是 1 到 24 的整数"}), 400
    rows = _query_rows()
    filtered, end = _filtered_rows(rows, months, request.args.get("endMonth"))
    return _response(f"/api/v1/analysis/{dimension}/complaints", {"dimension": dimension, "tree": _dimension_tree(dimension, filtered)}, {"endMonth": end, "months": request.args.get("months", 6)})


@bp.get("/qa/questions")
def qa_questions():
    """返回问大家（S4）真实问答数据：问题、商品、品类、来源、回答列表。"""
    rows = _query_rows()
    items = []
    for row in rows:
        if row.get("touchpoint") != "S4":
            continue
        answers = row.get("qa_answers") or []
        items.append({
            "id": row["id"],
            "question": row.get("text") or "",
            "source_product_id": row.get("source_product_id"),
            "category_l1": row.get("category_l1"),
            "category_l2": row.get("category_l2"),
            "category_l3": row.get("category_l3"),
            "sku": row.get("sku"),
            "platform": row.get("platform"),
            "answer_count": len(answers),
            "answers": answers,
        })
    return _response("/api/v1/qa/questions", {"items": items, "total": len(items)})


@bp.get("/data-import/options")
def data_import_options():
    return _response("/api/v1/data-import/options", {"sourceTypes": SOURCE_TYPES})
