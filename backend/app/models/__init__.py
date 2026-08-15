"""ORM 模型包。

在此处导入/定义业务模型，并在 create_app 中调用 db.create_all()
创建缺失的表结构（已存在的表不受影响）。
"""
from ..db import db
from .dataset_info import DatasetInfo
from .analysis_result import AnalysisResult

__all__ = ["db", "DatasetInfo", "AnalysisResult"]
