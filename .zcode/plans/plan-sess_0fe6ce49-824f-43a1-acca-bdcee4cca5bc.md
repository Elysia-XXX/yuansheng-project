## 目标
在 `D:\桌面\shunde\original-soundtrack`（当前空项目）搭建前后端分离全栈框架：
- **前端**：Vue 3 + Vite + TypeScript + Element Plus + vue-router + axios
- **后端**：Python Flask + Flask-SQLAlchemy + psycopg2，连接本机 PostgreSQL（postgresql-x64-18 已在 5432 监听）
- **数据库配置**：用户名默认 `postgres`、**无密码**、库名 `postgres`（通过 `.env` 可随时修改）

## 目录结构
```
original-soundtrack/
├── backend/
│   ├── app/
│   │   ├── __init__.py       # 应用工厂 create_app()
│   │   ├── config.py         # 从 .env/环境变量读数据库配置（默认无密码连接）
│   │   ├── db.py             # SQLAlchemy 实例
│   │   ├── models/__init__.py
│   │   └── routes/
│   │       ├── __init__.py
│   │       └── health.py     # GET /api/health（含数据库连通性检查）
│   ├── .env.example          # DB_HOST/DB_PORT/DB_USER/DB_PASSWORD/DB_NAME
│   ├── requirements.txt      # Flask, Flask-SQLAlchemy, Flask-CORS, psycopg2-binary, python-dotenv
│   ├── run.py                # 启动入口（端口 5000）
│   └── README.md
├── frontend/                 # Vite 脚手架 vue-ts + 定制
│   ├── src/{main.ts, App.vue, router/, api/, views/HomeView.vue}
│   ├── vite.config.ts        # dev 代理 /api -> http://localhost:5000
│   └── package.json
└── README.md
```

## 实施步骤
1. **后端**：venv 虚拟环境 + 安装依赖；应用工厂/蓝图结构；config 从 `.env` 读取，无密码时用 `postgresql+psycopg2://postgres@localhost:5432/postgres` 形式；`/api/health` 执行 `SELECT 1` 检查 DB；Flask-CORS 放开跨域。
2. **数据库连接验证**：用无密码配置实际连接本机 pgsql。
   - **若连接失败：按你的要求向你报告问题与错误信息，不自行尝试修复。**
3. **前端**：`npm create vite@latest frontend -- --template vue-ts` 生成脚手架；安装 element-plus / vue-router / axios；配置 `/api` 代理；Home 页面调用 `/api/health` 用 Element Plus 展示后端与数据库状态。
4. **收尾**：更新根 .gitignore（node_modules/.venv/.env/dist）、写 README 启动步骤。

## 验证
- 后端 `python run.py` 可启动，`/api/health` 返回 JSON（含 database 状态）
- 前端 `npm run dev` 可启动，首页成功调用后端接口