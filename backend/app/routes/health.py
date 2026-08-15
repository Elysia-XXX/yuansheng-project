"""健康检查接口：GET /api/health

返回服务状态与数据库连通性（执行 SELECT 1）。
"""
from flask import Blueprint, jsonify
from sqlalchemy import text

from ..db import db

bp = Blueprint("health", __name__)


@bp.get("/health")
def health():
    database_status = "ok"
    database_error = None
    try:
        db.session.execute(text("SELECT 1"))
    except Exception as exc:  # noqa: BLE001 - 健康检查需捕获所有异常
        database_status = "error"
        database_error = str(exc)

    return jsonify(
        {
            "status": "ok",
            "service": "original-soundtrack-backend",
            "database": database_status,
            "database_error": database_error,
        }
    )
