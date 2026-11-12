"""Conversational workspace API; history is scoped to each client request."""
from flask import Blueprint, current_app, jsonify, request
from pydantic import ValidationError
from ..services.agent_tools import REGISTRY
from ..services.data_agent import ChatInput, run_chat

bp = Blueprint("agent", __name__, url_prefix="/api/agent")


@bp.get("/status")
def status():
    demo = current_app.config.get("AGENT_DEMO_MODE", False)
    return jsonify({"mode": "demo" if demo else "model", "configured": demo or bool(current_app.config.get("AGENT_API_KEY")), "model": None if demo else current_app.config.get("AGENT_MODEL"), "source": "6 条虚构演示原声" if demo else "PostgreSQL 客户原声库", "tools": [{"name": name, "description": description} for name, (_, _, description) in REGISTRY.items()]})


@bp.post("/chat")
def chat():
    if request.content_length and request.content_length > 640000:
        return jsonify({"error": "请求过大，请新建对话"}), 413
    if not request.is_json:
        return jsonify({"error": "请使用 JSON 请求"}), 400
    try:
        raw = request.get_json(silent=True)
        payload = ChatInput.model_validate(raw)
        if not payload.message.strip():
            raise ValueError("empty")
    except (ValidationError, ValueError):
        return jsonify({"error": "请求无效：问题最多4000字，历史最多12条，角色仅允许user/assistant"}), 400
    return jsonify(run_chat(payload))
