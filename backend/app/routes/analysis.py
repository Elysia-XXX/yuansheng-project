"""客诉智能分析接口：POST /api/analysis/run。"""
from flask import Blueprint, current_app, jsonify, request
from sqlalchemy import exists

from ..db import db
from ..models import AnalysisResult, DatasetInfo
from ..services.complaint_analyzer import analyze_dataset_info

bp = Blueprint("analysis", __name__, url_prefix="/api/analysis")


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
