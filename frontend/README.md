# 客诉分析前端

Vite 承载的单页客诉分析系统，入口为 `index.html`。页面使用 Tailwind CSS 与
Chart.js，数据统一来自 Flask 的 `/api/v1` 分析接口；开发服务器会把 `/api`
代理到 `http://localhost:5000`。

```bash
npm install
npm run dev
```

生产构建执行 `npm run build`。
