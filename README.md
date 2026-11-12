# 原声数据 Agent

在原有客户原声分析平台上改造的对话式数据工作台。Vue 3 + TypeScript 前端，Flask + SQLAlchemy + PostgreSQL 后端。首页从固定看板切换为对话，原数据导入、录入、评价管理与经典看板保留。

## 已实现

- 多轮对话：模型自主选择工具，执行后将结果回传模型，最多 6 轮、12 次工具调用。
- 数据工具：查看数据说明、筛选原声、按维度统计、查看记录详情、受限算术计算。
- 可追溯结果：展示工具参数、返回值、耗时和错误；分布条形图、原声样本、原文引用可点击追问。
- 最近 10 个对话保存在当前浏览器，可切换、清空、导出 Markdown（包含工具记录）。后端不保存聊天。
- 显式演示模式：6 条虚构样本、固定规则，无需数据库和 Key。它不是大模型模式的静默降级。
- 前端按用户指定的 DeepFrontier 工作区设计适配：暖白与黑灰配色、可折叠侧栏、侧栏会话列表、居中输入区及可关闭的工具结果面板，见 [前端参考适配](docs/前端参考适配.md)。

## 快速体验（PowerShell）

需要 Python 3.11+，建议 Node.js 22.18+ 或 24.11+（现有前端依赖的引擎要求）。

终端一：

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
$env:AGENT_DEMO_MODE='true'
.\.venv\Scripts\python -m flask --app run run --host=127.0.0.1 --port=5000
```

终端二：

```powershell
cd frontend
npm ci
npm run dev
```

访问 http://localhost:5173 。可以尝试：

- 按品类统计客户原声，并查看典型反馈
- 查看京东的差评及原文
- 搜索包含“噪音”的原声
- 查看原声 #2
- 计算 (128 - 96) / 96 * 100

演示模式不提供业务数据导入、写入和经典看板。聊天内固定规则只支持示例中的平台、品类、评价等级、引号内关键词、记录 ID 和算术；任意自然语言及上下文追问应使用模型模式。

## 接入真实数据和模型

复制 `backend/.env.example` 为 `backend/.env`，填写现有 PostgreSQL 连接。数据库结构仍沿用 `backend/schema.sql` 和原应用工厂的迁移。

```dotenv
AGENT_DEMO_MODE=false
DB_HOST=127.0.0.1
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=你的数据库密码
DB_NAME=postgres
AGENT_API_KEY=你的模型Key
AGENT_BASE_URL=https://api.xiaomimimo.com/v1
AGENT_MODEL=mimo-v2.5-pro
```

Agent 也可复用已有 `MIMO_API_KEY / MIMO_BASE_URL / MIMO_MODEL`：不设置对应的 `AGENT_*` 项即可继承。其他模型服务必须支持 OpenAI 兼容的 Chat Completions `tools` 协议。Key 只在后端使用，不进入前端。

**如当前 PowerShell 已设置演示变量，先执行 `Remove-Item Env:AGENT_DEMO_MODE`，再重启后端，否则环境变量会覆盖 `.env`。**

模型模式下启动仍可用上面的 Flask 命令；前端不需修改。现有导入可能依赖额外的 `product_catalog` 数据库，见 `backend/README.md`。经典看板位于 `/legacy.html`，仍保留其原有 CDN 依赖。生产构建同时生成两个入口。

## 路由与代码

| 功能 | 入口 |
| --- | --- |
| 对话工作台 | `/` |
| 客户原声管理 | `/reviews` |
| 文件导入 / 单条录入 | `/import` / `/single` |
| 原系统状态 | `/status` |
| 原静态看板 | `/legacy.html` |
| Agent 配置状态（不返回 Key） | `GET /api/agent/status` |
| 对话请求 | `POST /api/agent/chat` |

Agent 服务位于 `backend/app/services/data_agent.py`，工具注册和查询位于 `agent_tools.py`，API 位于 `backend/app/routes/agent.py`，前端主页面位于 `frontend/src/views/AgentView.vue`。

## 验证

```powershell
cd backend
.\.venv\Scripts\python -m unittest discover -s tests -v
```

```powershell
cd frontend
npm run build
```

测试包含真实 ORM 查询的 SQLite 测试夹具、模型协议模拟、重复分析去重、筛选与分母、工具参数校验、异常恢复路径及计算限制。SQLite 夹具不替代 PostgreSQL 集成测试；真实模型连通性需要实际 Key 验证。

## 使用边界

这是本地或内网原型，沿用原项目的无鉴权接口。公开部署前需要补充账户、数据权限和限流。模型模式会将本轮查询结果与历史上下文发送给配置的模型服务；浏览器会保存对话和原文，处理敏感原声时需遵循你的数据使用要求。

当前不支持任意 SQL、任意代码、写库 Agent、服务器端持久会话、Token 流式输出或用户级权限。模型输出的数字与结论仍应通过右侧工具结果复核。工具执行受参数白名单、分页上限、计算 AST 限制、PostgreSQL 单语句超时（5 秒）及轮数预算约束。

详见 [Agent 需求与设计](docs/Agent设计.md)。原有分析标签与字段说明继续位于 `docs/`。

项目沿用原仓库 AGPL-3.0 许可证。
