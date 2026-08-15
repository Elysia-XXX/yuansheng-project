# 原声分析平台

根据客户原声进行分析的 Web 应用。前后端分离架构：

- **前端**：Vue 3 + Vite + TypeScript + Element Plus（`frontend/`）
- **后端**：Python Flask + SQLAlchemy + PostgreSQL（`backend/`）

## 目录结构

```
original-soundtrack/
├── backend/                 # Flask 后端
│   ├── app/
│   │   ├── __init__.py      # 应用工厂 create_app()
│   │   ├── config.py        # 配置（从 .env 读取）
│   │   ├── db.py            # SQLAlchemy 实例
│   │   ├── models/          # ORM 模型
│   │   └── routes/          # API 蓝图（/api/health 等）
│   ├── .env                 # 数据库连接配置（不入库）
│   ├── requirements.txt
│   └── run.py               # 后端启动入口
└── frontend/                # Vue 前端
    └── src/
        ├── api/             # axios 封装
        ├── router/          # vue-router
        ├── views/           # 页面
        └── ...
```

## 快速开始

### 1. 启动后端（端口 5000）

```bash
cd backend
python -m venv .venv
.venv/Scripts/activate          # Windows；macOS/Linux 用 source .venv/bin/activate
pip install -r requirements.txt

# 数据库配置（默认：localhost:5432，用户 postgres，无密码，库 postgres）
cp .env.example .env           # 按需修改 .env

python run.py
```

验证：浏览器访问 <http://localhost:5000/api/health>，应返回 JSON，
其中 `database` 字段为 `ok` 表示 PostgreSQL 连接正常。

### 2. 启动前端（端口 5173）

```bash
cd frontend
npm install
npm run dev
```

浏览器访问 <http://localhost:5173>，首页「系统状态」卡片会显示后端与
数据库的连接状态。开发环境下 `/api` 请求由 Vite 代理转发到后端 5000 端口。

## 数据库

后端通过 `.env` 中的以下变量连接 PostgreSQL：

| 变量          | 默认值      | 说明       |
| ------------- | ----------- | ---------- |
| `DB_HOST`     | `localhost` | 数据库地址 |
| `DB_PORT`     | `5432`      | 端口       |
| `DB_USER`     | `postgres`  | 用户名     |
| `DB_PASSWORD` | 空          | 密码       |
| `DB_NAME`     | `postgres`  | 数据库名   |

## 常用命令

- 后端测试运行：`cd backend && .venv/Scripts/python run.py`
- 前端构建：`cd frontend && npm run build`
- 前端类型检查：`cd frontend && npm run type-check`
