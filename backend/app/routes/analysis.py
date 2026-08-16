"""客诉智能分析接口：POST /api/analysis/run。"""
from flask import Blueprint, current_app, jsonify, request
from sqlalchemy import exists

from ..db import db
from ..models import AnalysisResult, DatasetInfo
from ..services.complaint_analyzer import analyze_dataset_info, generate_complaint_insight

bp = Blueprint("analysis", __name__, url_prefix="/api/analysis")


@bp.post("/insights")
def complaint_insights():
    """根据当前前端节点对应的数据库记录生成聚合 AI 洞察。"""
    body = request.get_json(silent=True) or {}
    label = str(body.get("label") or "当前客诉集合").strip()[:200]
    raw_ids = body.get("dataset_info_ids")
    if not isinstance(raw_ids, list):
        return jsonify({"error": "dataset_info_ids 必须是数组"}), 400
    try:
        ids = list(dict.fromkeys(int(value) for value in raw_ids))
    except (TypeError, ValueError):
        return jsonify({"error": "dataset_info_ids 只能包含整数"}), 400
    if not 1 <= len(ids) <= 200:
        return jsonify({"error": "每次请选择 1 到 200 条客诉"}), 400

    rows = DatasetInfo.query.filter(DatasetInfo.id.in_(ids)).all()
    by_id = {row.id: row for row in rows}
    records = []
    for item_id in ids:
        row = by_id.get(item_id)
        if row is None:
            continue
        records.append({
            "id": row.id,
            "content": row.customer_transcript,
            "category": "/".join(filter(None, [row.category_l1, row.category_l2, row.category_l3])),
            "sku": row.sku,
            "platform": row.platform,
            "touchpoint": row.touchpoint,
            "complaint_time": str(row.complaint_time or row.created_at),
        })
    if not records:
        return jsonify({"error": "没有找到可分析的客诉记录"}), 404

    try:
        insight = generate_complaint_insight(label, records)
    except Exception as exc:  # noqa: BLE001 - 转为清晰的上游服务错误
        current_app.logger.exception("MiMo 聚合洞察失败")
        return jsonify({"error": f"MiMo AI 洞察失败：{str(exc)[:500]}"}), 502
    return jsonify({
        **insight.model_dump(),
        "sample_count": len(records),
        "provider": "Xiaomi MiMo",
        "model": current_app.config["MIMO_MODEL"],
    })


@bp.post("/run")
def run_analysis():
    """依次分析尚未生成 analysis_result 的数据，单条提交以保留已完成进度。"""
    body = request.get_json(silent=True) or {}
    try:
        limit = int(body.get("limit", 100))
    except (TypeError, ValueError):
        return jsonify({"error": "limit 必须是整数"}), 400
    if not 1 <= limit <= 1000:
        return jsonify({"error": "limit 必须在 1 到 1000 之间"}), 400

    pending = (
        DatasetInfo.query
        .filter(~exists().where(AnalysisResult.dataset_info_id == DatasetInfo.id))
        .order_by(DatasetInfo.id)
        .limit(limit)
        .all()
    )
    analyzed = 0
    errors = []
    for item in pending:
        current_app.logger.info("开始分析 dataset_info_id=%s", item.id)
        try:
            structured = analyze_dataset_info(item)
            db.session.add(AnalysisResult(dataset_info_id=item.id, **structured.model_dump()))
            db.session.commit()
            analyzed += 1
            current_app.logger.info("分析成功 dataset_info_id=%s", item.id)
        except Exception as exc:  # noqa: BLE001 - 单条失败不应中断整个批次
            db.session.rollback()
            current = str(exc).strip() or exc.__class__.__name__
            current_app.logger.error(
                "分析失败 dataset_info_id=%s: %s", item.id, current.splitlines()[0]
            )
            errors.append({"dataset_info_id": item.id, "error": current[:500]})

    remaining = (
        DatasetInfo.query
        .filter(~exists().where(AnalysisResult.dataset_info_id == DatasetInfo.id))
        .count()
    )
    status = 200 if analyzed or not errors else 502
    return jsonify(
        {
            "requested": len(pending),
            "analyzed": analyzed,
            "failed": len(errors),
            "remaining": remaining,
            "errors": errors,
        }
    ), status
