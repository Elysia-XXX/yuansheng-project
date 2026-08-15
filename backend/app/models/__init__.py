"""ORM 模型包。

在此处导入/定义业务模型，并在 create_app 中调用 db.create_all()
或使用 Flask-Migrate 管理表结构。当前框架阶段暂不定义业务表。
"""
from ..db import db

__all__ = ["db"]
