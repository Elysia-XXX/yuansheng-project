# 后端（Flask + PostgreSQL）

「原声分析平台」的 Flask 后端，提供 JSON API。

## 技术栈

- Python 3.11 + Flask 3 + Flask-SQLAlchemy
- PostgreSQL（本机默认连接，psycopg2 驱动）

## 启动

```bash
python -m venv .venv
.venv/Scripts/activate          # Windows；macOS/Linux 用 source .venv/bin/activate
pip install -r requirements.txt

# 数据库配置（复制模板并按需修改）
cp .env.example .env

python run.py                   # 监听 0.0.0.0:5000
```

## 接口

| 方法 | 路径          | 说明                     |
| ---- | ------------- | ------------------------ |
| GET  | `/api/health` | 服务与数据库连通性检查   |

`/api/health` 返回示例（数据库正常时）：

```json
{
  "status": "ok",
  "service": "original-soundtrack-backend",
  "database": "ok",
  "database_error": null
}
```

若数据库连接失败，`database` 为 `error`，`database_error` 携带详细错误信息，
服务本身仍正常返回（便于前端展示问题，而不是整体崩溃）。

## 目录说明

```
app/
├── __init__.py       # 应用工厂 create_app()，注册蓝图、CORS、SQLAlchemy
├── config.py         # 配置：从 .env 读取数据库连接参数
├── db.py             # SQLAlchemy 实例
├── models/           # ORM 模型（框架阶段未定义业务表）
└── routes/           # API 蓝图
    └── health.py     # /api/health
```

新增业务接口时，在 `app/routes/` 下新建蓝图文件并在
`app/__init__.py` 中注册即可；业务表在 `app/models/` 中定义。
