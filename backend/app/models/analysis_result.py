"""表二：需要从对话中分析的信息。

对应 schema.sql 中的 analysis_result 表。
"""
from sqlalchemy import BigInteger, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db import db


class AnalysisResult(db.Model):
    """从客户对话/原声中分析打标的结果，关联到 dataset_info。"""

    __tablename__ = "analysis_result"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    dataset_info_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("dataset_info.id", ondelete="CASCADE"),
        nullable=False,
    )

    # 功能标签
    function_tag_l1: Mapped[str] = mapped_column(String(30), nullable=False)
    function_tag_l2: Mapped[list[str] | None] = mapped_column(ARRAY(Text))

    # 生产环节 / 产品部件
    production_stage: Mapped[str | None] = mapped_column(String(30))
    production_substage: Mapped[str | None] = mapped_column(String(50))
    part_category: Mapped[list[str] | None] = mapped_column(ARRAY(Text))
    part_name: Mapped[list[str] | None] = mapped_column(ARRAY(Text))

    # 语义分析
    evaluation_level: Mapped[str] = mapped_column(String(30), nullable=False)
    emotion_dimension: Mapped[str] = mapped_column(String(30), nullable=False)
    problem_nature: Mapped[str] = mapped_column(String(30), nullable=False)
    keyword_cluster: Mapped[list[str] | None] = mapped_column(ARRAY(Text))
    appeal_intent: Mapped[str] = mapped_column(String(30), nullable=False)

    # 通用
    created_at: Mapped[object] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    dataset_info: Mapped["DatasetInfo"] = relationship(backref="analysis_results")

    def __repr__(self) -> str:
        return f"<AnalysisResult {self.id} dataset={self.dataset_info_id}>"
