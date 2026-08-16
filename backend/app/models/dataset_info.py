"""表一：数据集需要提供的信息（含客户原文）。

对应 schema.sql 中的 dataset_info 表。
"""
from sqlalchemy import BigInteger, Boolean, DateTime, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from ..db import db


class DatasetInfo(db.Model):
    """数据集提供的信息 + 客户原文。"""

    __tablename__ = "dataset_info"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    # 商品目录中的原始商品 ID；用于从 product_catalog 自动补齐 SKU 和品类。
    source_product_id: Mapped[str | None] = mapped_column(String(50), index=True)

    # 客户原文与来源渠道
    customer_transcript: Mapped[str] = mapped_column(Text, nullable=False)
    touchpoint: Mapped[str] = mapped_column(String(10), nullable=False)
    source_form: Mapped[str | None] = mapped_column(Text)

    # 品类（SKU 级）
    category_l1: Mapped[str] = mapped_column(String(50), nullable=False)
    category_l2: Mapped[str] = mapped_column(String(50), nullable=False)
    category_l3: Mapped[str] = mapped_column(String(50), nullable=False)
    sku: Mapped[str] = mapped_column(String(50), nullable=False)

    # 客户画像
    region: Mapped[str | None] = mapped_column(String(20))
    province: Mapped[str | None] = mapped_column(String(50))
    city_tier: Mapped[str | None] = mapped_column(String(20))
    gender: Mapped[str | None] = mapped_column(String(20))
    age: Mapped[str | None] = mapped_column(String(20))
    use_scene: Mapped[str | None] = mapped_column(String(50))
    user_type: Mapped[str | None] = mapped_column(String(30))
    member_level: Mapped[str | None] = mapped_column(String(20))

    # 订单交易
    price_band: Mapped[str | None] = mapped_column(String(20))
    paid_amount: Mapped[object | None] = mapped_column(Numeric(10, 2))
    original_amount: Mapped[object | None] = mapped_column(Numeric(10, 2))
    platform: Mapped[str] = mapped_column(String(30), nullable=False)
    promo_type: Mapped[str | None] = mapped_column(String(50))
    warranty_status: Mapped[str | None] = mapped_column(String(30))
    is_gift: Mapped[bool | None] = mapped_column(Boolean)
    complaint_time: Mapped[object | None] = mapped_column(DateTime)
    duration_to_complaint: Mapped[str | None] = mapped_column(String(20))
    product_season: Mapped[str | None] = mapped_column(String(30))
    complaint_season: Mapped[str | None] = mapped_column(String(10))

    # 生命周期
    lifecycle_stage: Mapped[str | None] = mapped_column(String(30))

    # 问大家（S4）回答内容，JSON 数组：[{user, content, time, status}, ...]
    qa_answers: Mapped[list | None] = mapped_column(JSONB)

    # 通用
    created_at: Mapped[object] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    def __repr__(self) -> str:
        return f"<DatasetInfo {self.id} {self.sku}>"
