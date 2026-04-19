# Boss Agent Workspace

前后端分离的求职 Agent 工作台：

- `frontend/`: Next.js + Tailwind，承接 Stitch 还原页面
- `backend/`: FastAPI，提供聊天、职位、AI 配置、面试与简历实验室接口

## 启动

```bash
npm install
npm run dev
```

前端默认在 `http://localhost:3000`  
后端默认在 `http://localhost:8000`

## 开发结构

- 首页：自动化总览
- `/chat`：对话工作台
- `/jobs`：职位池
- `/ai-config`：AI 配置中心
- `/interviews`：面试管理
- `/resume-lab`：简历与话术实验室

## 后续接入

- Playwright Python 执行器
- PostgreSQL + pgvector
- RAG 检索链路
- BOSS 消息自动跟进
