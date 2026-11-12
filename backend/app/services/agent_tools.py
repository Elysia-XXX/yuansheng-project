"""Read-only, validated tools. No arbitrary SQL or Python execution."""
import ast
import math
import operator
from collections import Counter
from datetime import date

from flask import current_app
from pydantic import BaseModel, ConfigDict, Field, model_validator

DIMENSIONS = ["platform", "category_l1", "category_l2", "category_l3", "sku", "evaluation_level", "function_tag_l1", "emotion_dimension", "problem_nature", "appeal_intent", "month"]


class Arguments(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class Filters(Arguments):
    platform: str | None = Field(default=None, max_length=100)
    category_l3: str | None = Field(default=None, max_length=100)
    sku: str | None = Field(default=None, max_length=100)
    evaluation_level: str | None = Field(default=None, max_length=100)
    keyword: str | None = Field(default=None, max_length=100)
    start_date: str | None = Field(default=None, description="包含，YYYY-MM-DD")
    end_date: str | None = Field(default=None, description="包含，YYYY-MM-DD")

    @model_validator(mode="after")
    def dates(self):
        for value in (self.start_date, self.end_date):
            if value:
                date.fromisoformat(value)
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValueError("开始日期不能晚于结束日期")
        return self


class Search(Arguments):
    filters: Filters = Field(default_factory=Filters)
    limit: int = Field(default=10, ge=1, le=30)
    offset: int = Field(default=0, ge=0, le=10000)


class Aggregate(Arguments):
    filters: Filters = Field(default_factory=Filters)
    group_by: str = Field(default="platform", json_schema_extra={"enum": DIMENSIONS})

    @model_validator(mode="after")
    def dimension(self):
        if self.group_by not in DIMENSIONS:
            raise ValueError("不支持的统计维度")
        return self


class Detail(Arguments):
    record_id: int = Field(ge=1)


class Calculate(Arguments):
    expression: str = Field(min_length=1, max_length=200, description="仅数字、括号、加减乘除、取余和幂；百分比请乘100")


def calculate(expression):
    tree = ast.parse(expression, mode="eval")
    if sum(1 for _ in ast.walk(tree)) > 80:
        raise ValueError("表达式过长")
    binary = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv, ast.Mod: operator.mod, ast.Pow: operator.pow}

    def visit(node):
        if isinstance(node, ast.Constant) and type(node.value) in (int, float):
            value = node.value
        elif isinstance(node, ast.UnaryOp) and type(node.op) in (ast.UAdd, ast.USub):
            value = visit(node.operand) * (-1 if isinstance(node.op, ast.USub) else 1)
        elif isinstance(node, ast.BinOp) and type(node.op) in binary:
            left, right = visit(node.left), visit(node.right)
            if isinstance(node.op, ast.Pow) and (abs(right) > 12 or abs(left) > 1e6):
                raise ValueError("幂运算超出限制")
            value = binary[type(node.op)](left, right)
        else:
            raise ValueError("只支持数字和算术运算")
        if type(value) not in (int, float) or not math.isfinite(value) or abs(value) > 1e15:
            raise ValueError("计算结果超出范围")
        return value

    return {"expression": expression, "value": visit(tree.body)}


DEMO_ROWS = [
    {"id": 1, "text": "养生壶用了两周，壶底出现水垢，希望提供清洗说明。", "platform": "京东", "sku": "YS-01", "category_l3": "养生壶", "evaluation_level": "中评", "function_tag_l1": "C6", "emotion_dimension": "悲伤", "problem_nature": "体验不佳", "appeal_intent": "改进建议", "time": "2026-10-02"},
    {"id": 2, "text": "破壁机噪音大，早上使用影响家人休息。", "platform": "天猫", "sku": "PB-02", "category_l3": "破壁机", "evaluation_level": "差评", "function_tag_l1": "C2", "emotion_dimension": "愤怒", "problem_nature": "性能不足", "appeal_intent": "改进建议", "time": "2026-10-05"},
    {"id": 3, "text": "养生壶加热很快，操作简单，家人很喜欢。", "platform": "京东", "sku": "YS-01", "category_l3": "养生壶", "evaluation_level": "好评", "function_tag_l1": "C10", "emotion_dimension": "快乐", "problem_nature": None, "appeal_intent": "改进建议", "time": "2026-10-08"},
    {"id": 4, "text": "空气炸锅抽屉卡住，联系售后申请换货。", "platform": "天猫", "sku": "KQ-03", "category_l3": "空气炸锅", "evaluation_level": "差评", "function_tag_l1": "C3", "emotion_dimension": "愤怒", "problem_nature": "质量故障", "appeal_intent": "换货", "time": "2026-10-12"},
    {"id": 5, "text": "破壁机打豆浆细腻，就是清洗有些麻烦。", "platform": "京东", "sku": "PB-02", "category_l3": "破壁机", "evaluation_level": "中评", "function_tag_l1": "C6", "emotion_dimension": "悲伤", "problem_nature": "体验不佳", "appeal_intent": "改进建议", "time": "2026-11-01"},
    {"id": 6, "text": "养生壶无法通电，要求退货。", "platform": "京东", "sku": "YS-01", "category_l3": "养生壶", "evaluation_level": "差评", "function_tag_l1": "C3", "emotion_dimension": "愤怒", "problem_nature": "质量故障", "appeal_intent": "退货", "time": "2026-11-03"},
]


def _demo_filtered(filters):
    rows = []
    for original in DEMO_ROWS:
        row = {"category_l1": "家用电器", "category_l2": "厨房电器", **original}
        if any(value and row.get(key) != value for key, value in filters.model_dump().items() if key not in ("keyword", "start_date", "end_date")):
            continue
        if filters.keyword and filters.keyword.casefold() not in row["text"].casefold():
            continue
        if filters.start_date and row["time"] < filters.start_date:
            continue
        if filters.end_date and row["time"] > filters.end_date:
            continue
        rows.append(row)
    return rows


def _query(filters):
    # Correlated latest-analysis join prevents double counting repeated analysis runs.
    from sqlalchemy import select, func
    from ..db import db
    from ..models import AnalysisResult as A, DatasetInfo as D
    if db.engine.dialect.name == "postgresql":
        from sqlalchemy import text
        db.session.execute(text("SET LOCAL statement_timeout = '5000'"))
    latest = select(func.max(A.id)).where(A.dataset_info_id == D.id).correlate(D).scalar_subquery()
    query = db.session.query(D, A).outerjoin(A, A.id == latest)
    timestamp = func.coalesce(D.complaint_time, D.created_at)
    for key in ("platform", "category_l3", "sku", "evaluation_level"):
        value = getattr(filters, key)
        if value:
            query = query.filter(getattr(A if key == "evaluation_level" else D, key) == value)
    if filters.keyword:
        query = query.filter(D.customer_transcript.contains(filters.keyword, autoescape=True))
    if filters.start_date:
        query = query.filter(func.date(timestamp) >= date.fromisoformat(filters.start_date))
    if filters.end_date:
        query = query.filter(func.date(timestamp) <= date.fromisoformat(filters.end_date))
    return query, D, A, timestamp


def search_records(args):
    if current_app.config.get("AGENT_DEMO_MODE"):
        rows = _demo_filtered(args.filters)
        return {"total": len(rows), "items": rows[args.offset:args.offset + args.limit], "offset": args.offset}
    query, D, A, timestamp = _query(args.filters)
    total = query.count()
    items = []
    for d, a in query.order_by(D.id.desc()).offset(args.offset).limit(args.limit).all():
        items.append({"id": d.id, "text": d.customer_transcript[:2000], "platform": d.platform, "sku": d.sku, "category_l3": d.category_l3, "time": str(d.complaint_time or d.created_at), "evaluation_level": a.evaluation_level if a else None})
    return {"total": total, "items": items, "offset": args.offset}


def aggregate_records(args):
    if current_app.config.get("AGENT_DEMO_MODE"):
        rows = _demo_filtered(args.filters)
        counts = Counter((row["time"][:7] if args.group_by == "month" else row.get(args.group_by)) or "未标注" for row in rows)
        total = len(rows)
        groups = sorted(counts.items(), key=lambda pair: (-pair[1], pair[0]))
    else:
        from sqlalchemy import func
        query, D, A, timestamp = _query(args.filters)
        field = func.to_char(timestamp, "YYYY-MM") if args.group_by == "month" else getattr(D if hasattr(D, args.group_by) else A, args.group_by)
        total = query.count()
        groups = query.with_entities(field, func.count(D.id)).group_by(field).order_by(func.count(D.id).desc(), field).limit(101).all()
    return {"group_by": args.group_by, "total": total, "truncated": len(groups) > 100, "groups": [{"label": label or "未标注", "count": count, "share_percent": round(count * 100 / total, 2) if total else 0} for label, count in groups[:100]], "denominator": "当前筛选范围全部原声记录数，包含未标注记录"}


def get_record(args):
    if current_app.config.get("AGENT_DEMO_MODE"):
        return next((dict(row) for row in DEMO_ROWS if row["id"] == args.record_id), {"error": "记录不存在"})
    query, D, A, timestamp = _query(Filters())
    row = query.filter(D.id == args.record_id).first()
    if not row:
        return {"error": "记录不存在"}
    d, a = row
    # Deliberately omit customer profile and order details from model context.
    return {"id": d.id, "text": d.customer_transcript[:6000], "platform": d.platform, "sku": d.sku, "category_l3": d.category_l3, "time": str(d.complaint_time or d.created_at), "analysis": {key: getattr(a, key) for key in DIMENSIONS if key != "month" and hasattr(A, key)} if a else None}


def describe_data(args):
    return {"source": "演示样本（虚构）" if current_app.config.get("AGENT_DEMO_MODE") else "PostgreSQL 客户原声库", "dimensions": DIMENSIONS, "filters": Filters.model_json_schema(), "counting": "一条原声计一次，使用最新分析标签；未标注不等于差评；样本占比不代表全量产品故障率", "tools": list(REGISTRY)}


REGISTRY = {
    "describe_data": (Arguments, describe_data, "查看数据来源、字段、筛选项和统计口径。开始数据分析前先调用。"),
    "search_records": (Search, search_records, "按关键词、平台、商品、评价等级、日期筛选原声；返回总量和分页样本。"),
    "aggregate_records": (Aggregate, aggregate_records, "对全部符合筛选的原声按指定维度统计数量与占比；不是仅对搜索样本统计。"),
    "get_record": (Detail, get_record, "根据记录ID查看一条原声及其最新分析标签。"),
    "calculate": (Calculate, lambda args: calculate(args.expression), "安全计算比例、差值等算术表达式。"),
}


def definitions():
    return [{"type": "function", "function": {"name": name, "description": description, "parameters": schema.model_json_schema()}} for name, (schema, _, description) in REGISTRY.items()]


def execute(name, arguments):
    if name not in REGISTRY:
        raise ValueError("未知工具")
    schema, handler, _ = REGISTRY[name]
    return handler(schema.model_validate(arguments))
