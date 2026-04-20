# Backend

FastAPI 后端，负责：

- 页面数据接口
- RAG 检索与知识写入
- 聊天回复生成
- 自动化任务接口
- Playwright worker 封装

## 启动

```bash
uvicorn backend.app.main:app --reload --port 8000
```

## 关键文件

- `app/main.py`
- `app/routers/`
- `app/services/`
- `app/repositories.py`
- `app/state.py`
- `app/worker_cli.py`

## CLI

```bash
python -m backend.app.worker_cli status
python -m backend.app.worker_cli login
python -m backend.app.worker_cli collect --keyword 前端
python -m backend.app.worker_cli sync-messages
```
