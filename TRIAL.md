# 试用指南｜凌玑 AI 企业客诉智能分析系统

> MINMAX 黑客松提交材料第②项「可登录打开、可试用的作品」
> 最后更新：2026-11-10

## 一、体验链接与访问方式

| 用途 | 链接 | 说明 |
| --- | --- | --- |
| **主体验链接（推荐）** | <https://lingji-complaint-trial.app.workbuddy.host/?sharecode=LYWUTZVEQB> | 免 Key 评委体验版，带登录页，内置真实演示数据快照，打开即可试用 |
| 线上正式版（备用） | <http://20.43.87.214> | 连接 Flask + PostgreSQL 的正式演示环境；**AI 洞察依赖服务端大模型 Key，该 Key 已失效**（实测 `401 Invalid API Key`），看板与数据浏览仍可用 |
| 源码 | <https://github.com/Elysia-XXX/yuansheng-project> | 可自备 Key 本地部署，体验完整大模型能力 |

**访问方式**：任意现代浏览器（推荐 Chrome / Edge）直接打开链接，无需安装客户端、无需 VPN。
首次访问请使用带 `sharecode` 的完整链接，以便加载静态资源。

**测试账号**

| 项目 | 值 |
| --- | --- |
| 账号 | `demo` |
| 密码 | `Lingji2026` |
| 快捷进入 | 链接后加 `?autologin=1`（仍使用同一测试账号） |

## 二、免 Key 体验版能试什么

- 经营首页：客诉趋势、渠道/品类分布、总量指标
- 品类分析：一级/二级品类看板、问题排序、客诉原文下钻
- 8 个分析维度看板：生产、部件、功能、客户、生命周期、订单、语义、品牌
- 品牌风险分析：风险判断、证据链、待审核行动任务
- 客诉详情：原声、来源渠道、用户画像、分类路径
- AI 智能分析按钮：由**本地规则引擎**生成可解释洞察，界面明确标注「本地规则演示，未调用大模型」
- 筛选、搜索、图表交互与数据导出

> 说明：免 Key 体验版使用线上公开演示接口在 2026-11-10 抓取的数据快照，不含任何密钥；
> 不写入数据库，因此 Excel 导入会给出明确提示。它保证评委在任何情况下都能打开、登录、点得动。

## 三、自备 Key 试用真实大模型（本地部署）

线上正式版的服务端 Key 可能过期或额度用尽。如需体验真实大模型分析，请按以下步骤用自己的 Key 启动：

### 1. 准备后端

```bash
git clone https://github.com/Elysia-XXX/yuansheng-project.git
cd yuansheng-project/backend
python -m venv .venv
.venv/Scripts/activate          # Windows；macOS/Linux 用 source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

编辑 `backend/.env`，只填自己的密钥：

```ini
MIMO_API_KEY=你的密钥
MIMO_BASE_URL=https://api.xiaomimimo.com/v1
MIMO_MODEL=mimo-v2.5-pro
```

> 数据库为 PostgreSQL，按需修改 `DB_HOST` / `DB_PORT` / `DB_USER` / `DB_PASSWORD` / `DB_NAME`。
> 即使不填 Key，看板、图表与原声检索仍可用；只有 AI 洞察/批量分析会提示未配置。

启动后端并验证：

```bash
python run.py
# 浏览器访问 http://localhost:5000/api/health，应返回 database: ok
```

### 2. 启动前端

```bash
cd ../frontend
npm install
npm run dev
```

访问 <http://localhost:5173>，Vite 会把 `/api` 代理到后端 5000 端口。

### 3. 常用接口

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/health` | 服务与数据库连通性 |
| GET | `/api/v1/dashboard/home` | 经营首页统计 |
| GET | `/api/v1/analysis/<dimension>/dashboard` | 分析维度看板 |
| GET | `/api/v1/analysis/<dimension>/complaints` | 分析维度客诉树 |
| POST | `/api/analysis/insights` | 聚合 AI 洞察（需有效 Key） |
| POST | `/api/analysis/run` | 批量结构化分析（需有效 Key） |

## 四、密钥安全约定（重要）

- 本仓库**不包含任何真实或已失效的 API Key**。已核验全部 6 个提交、92 个 blob：
  仅存在 `MIMO_API_KEY` / `DEEPSEEK_API_KEY` 等**变量名**与空值模板，没有密钥值。
- 真实密钥只允许写在 `backend/.env`（已被 `.gitignore` 忽略），**禁止提交到 Git**，
  也**禁止写进商业计划书、提交邮件、演示视频、README 或任何提交材料**。
- 克隆仓库后运行一次 `sh scripts/setup-hooks.sh` 启用随仓库分发的 pre-commit 密钥扫描钩子，
  它会在提交时拦截 `.env` 和常见密钥格式。
- 若曾把密钥提交进历史，仅删除当前文件不够，必须清理 Git 历史并**立即在服务商侧吊销该密钥**。

## 五、目录说明

```
backend/    Flask + SQLAlchemy + PostgreSQL，AI 分析通过 OpenAI 兼容接口调用 MiMo
frontend/   Vite 单页客诉分析系统（Tailwind CSS / Chart.js / SheetJS）
docs/       字段清单、架构与流程图
.githooks/  提交前密钥扫描钩子
```
