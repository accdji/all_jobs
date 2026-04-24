# Boss Agent Workspace

## License

This project is licensed under the `Boss Agent Workspace Non-Commercial License 1.0 (BAW-NC-1.0)`.

- Non-commercial use only
- Commercial rights reserved by the copyright owner
- Attribution required for redistribution and modification

See [LICENSE](./LICENSE) for the full text.

## Open Source Safety

The public repository must not include any local privacy data or runtime memory.

- Do not commit `.env` or any real model keys
- Do not commit `.runtime/` runtime data
- Do not commit `browser_state/` or any Playwright browser profile
- Do not commit local RAG / knowledge data, chat transcripts, or interview memory exports
- Only commit `.env.example` as the public configuration template

Before pushing to GitHub, make sure your working tree does not include local runtime artifacts or generated knowledge content.

一个面向 BOSS 直聘场景的本地求职 Agent 工作台。

当前版本重点是：

- 前后端分离开发
- 浏览器端只暴露一个入口端口：`http://localhost:3000`
- 前端通过 Next.js 转发 `/api/*` 到 Python FastAPI
- 使用 Playwright Python 持久化浏览器会话，支持手动登录后复用
- 提供职位抓取、会话同步、回复生成、RAG 检索的本地 MVP

---

## 1. 当前能力

现在这版已经可以本地直接跑起来，并覆盖这几个核心动作：

- 打开持久化浏览器手动登录 BOSS
- 检测当前登录状态
- 抓取职位列表并写入本地状态
- 同步聊天列表摘要
- 通过 RAG + 规则生成 HR 回复草稿
- 在前端工作台里统一操作

当前仍然保守处理的部分：

- 自动发送消息仍保留在人机协同模式
- BOSS 页面 DOM 结构变化时，抓取选择器可能需要微调
- 向量存储当前默认使用内存实现，`pgvector` 只预留接口

---

## 2. 启动方式

根目录安装依赖并启动：

```bash
npm install
npm run playwright:install
npm run dev
```

启动后：

- 前端入口：`http://localhost:3000`
- Python 后端：内部运行在 `http://127.0.0.1:8000`
- 浏览器只需要访问 `3000`

说明：

- 前端通过 `frontend/next.config.ts` 中的 rewrite，把 `/api/*` 转发到 FastAPI
- 对使用者来说，前后端已经是“一个程序，一个入口端口”

---

## 3. 登录与使用流程

推荐使用顺序：

1. 打开 `http://localhost:3000`
2. 在首页右侧 `Live Ops` 面板点击“打开登录浏览器”
3. 在弹出的 Playwright 持久化浏览器里手动登录 BOSS
4. 回到首页点击“检测登录”
5. 输入关键词并点击“抓职位”
6. 点击“同步消息”
7. 进入 `/chat` 使用回复生成器

也可以使用命令行：

```bash
npm run backend:login
npm run backend:status
npm run backend:collect
npm run backend:sync
```

---

## 4. 架构体系

### 4.1 总体分层

项目按 4 层组织：

1. **Web Console**
   - Next.js + Tailwind
   - 负责工作台 UI、页面路由、操作面板
   - 对外统一暴露 `3000`

2. **API Layer**
   - FastAPI
   - 负责页面数据接口、聊天回复接口、自动化任务接口、RAG 接口

3. **Automation Worker**
   - Playwright Python
   - 使用持久化浏览器目录保存登录态
   - 负责登录检测、职位抓取、会话同步

4. **Knowledge / RAG Layer**
   - 当前：内存向量存储接口
   - 预留：`pgvector`
   - 用于简历、项目经历、历史对话、偏好信息的召回

---

### 4.2 单端口访问架构

```text
Browser
  -> http://localhost:3000
     -> Next.js UI
     -> /api/* rewrite
        -> http://127.0.0.1:8000/api/*
           -> FastAPI
              -> Playwright Worker / RAG / Local State
```

这样做的好处：

- 用户只记一个入口地址
- 前端不需要感知 Python 端口
- 后续部署时也更容易切换到反向代理或容器编排

---

### 4.3 后端模块边界

`backend/app` 目前的结构：

```text
backend/app/
  core/
    config.py              # 运行配置
  routers/
    dashboard.py           # 页面数据接口
    agent.py               # chat/rag/automation 接口
  services/
    browser_worker.py      # Playwright 持久化浏览器执行器
    automation.py          # 自动化任务服务
    chat.py                # 回复生成逻辑
    rag.py                 # 检索服务适配层
    knowledge.py           # 知识块写入/检索封装
    vector_store.py        # 向量存储抽象
  repositories.py          # 页面状态与任务仓库
  state.py                 # 本地 JSON 状态文件
  schemas.py               # Pydantic schema
  worker_cli.py            # 命令行入口
  main.py                  # FastAPI 装配入口
```

职责说明：

- `routers` 只负责 API 契约
- `services` 放业务逻辑
- `repositories` 管理页面态和任务态
- `state.py` 负责 `.runtime/agent-state.json`

---

### 4.4 前端模块边界

`frontend/src` 目前的结构：

```text
frontend/src/
  app/
    (workspace)/
      page.tsx             # 控制面板
      chat/page.tsx        # 聊天工作台
      jobs/page.tsx        # 职位池
      ai-config/page.tsx   # AI 配置
      interviews/page.tsx  # 面试管理
      resume-lab/page.tsx  # 简历实验室
  components/
    workspace-shell.tsx    # 整体布局壳
    automation-panel.tsx   # 首页自动化操作面板
    chat-reply-box.tsx     # 聊天页回复生成器
    ui.tsx                 # 通用 UI 组件
  lib/
    api.ts                 # 前端 API 请求封装
    types.ts               # 页面类型定义
  proxy.ts                 # 路径透传辅助
```

前端现在的原则：

- 页面数据走 FastAPI
- 操作按钮直接创建自动化任务
- 不直接持有浏览器自动化逻辑

---

## 5. 本地状态与数据流

当前状态文件：

- `.runtime/agent-state.json`

里面保存：

- 登录状态
- 抓到的职位
- 同步到的消息摘要
- 动态写入的知识块

数据流大致如下：

```text
手动登录
-> BrowserWorker 检测登录
-> collect_jobs
-> 写入 LocalStateStore
-> DashboardRepository 读取状态并投影到前端页面

HR 问题
-> /api/chat/reply
-> ChatAgentService
-> RAGService.search()
-> 返回 draft_reply
```

---

## 6. 关键接口

### 页面数据

- `GET /api/overview`
- `GET /api/chat`
- `GET /api/jobs`
- `GET /api/ai-config`
- `GET /api/interviews`
- `GET /api/resume-lab`

### RAG / Chat

- `POST /api/rag/search`
- `POST /api/rag/ingest`
- `POST /api/chat/reply`

### 自动化

- `GET /api/automation/worker`
- `GET /api/automation/tasks`
- `POST /api/automation/tasks`
- `GET /api/automation/tasks/{task_id}`

任务类型：

- `manual_login`
- `login_check`
- `collect_jobs`
- `sync_messages`
- `send_message`
- `refresh_rag`

---

## 7. 当前技术选型

### 前端

- Next.js
- TypeScript
- Tailwind CSS
- Stitch 导出页面二次还原

### 后端

- FastAPI
- Pydantic
- Playwright Python

### 当前存储

- 本地 JSON 状态文件
- 内存向量存储

### 预留升级

- PostgreSQL
- pgvector
- 更完整的消息执行链
- 更稳的 BOSS DOM 适配

---

## 8. 后续演进建议

最推荐的后续路线：

1. 接入 `PostgreSQL + pgvector`
2. 把 `KnowledgeService` 切到数据库实现
3. 把 `BrowserWorker.send_message()` 做成真实页面发送
4. 把聊天列表抓取从摘要升级到真实线程内容
5. 给自动化任务加状态机和重试机制

如果后面要上更正式的生产形态，可以继续拆：

- `worker` 进程单独部署
- `api` 与 `worker` 之间通过队列通信
- RAG 改为真正的 embedding 检索链

---

## 9. Git 说明

当前项目已经整理为**根目录单仓库**：

- 根目录为 git 仓库
- `frontend` 不再是独立仓库
- 前后端统一版本管理

- 可直接使用 `git log --oneline -n 5` 查看最近本地提交记录
