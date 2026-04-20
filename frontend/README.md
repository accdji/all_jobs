# Frontend

Next.js 工作台前端，负责：

- 控制面板
- 聊天工作台
- 职位池
- AI 配置
- 面试管理
- 简历实验室

## 启动

```bash
npm run dev
```

默认端口：

- `http://localhost:3000`

## 单端口说明

前端中所有 `/api/*` 请求都会由 Next.js rewrite 到 Python FastAPI：

```text
/api/* -> http://127.0.0.1:8000/api/*
```

所以浏览器侧只需要访问 `3000`。
