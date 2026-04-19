"use client";

import { useEffect, useState } from "react";

type WorkerStatus = {
  base_url: string;
  state_dir: string;
  state_exists: boolean;
  headless: boolean;
  engine: string;
  mode: string;
  vector_store_backend: string;
};

type Task = {
  id: string;
  task_type: string;
  status: string;
  result: Record<string, unknown>;
};

export function AutomationPanel() {
  const [worker, setWorker] = useState<WorkerStatus | null>(null);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [keyword, setKeyword] = useState("前端");
  const [pending, setPending] = useState<string | null>(null);

  async function refresh() {
    const [workerResponse, tasksResponse] = await Promise.all([
      fetch(`/api/automation/worker`).then((res) => res.json()),
      fetch(`/api/automation/tasks`).then((res) => res.json()),
    ]);
    setWorker(workerResponse);
    setTasks(tasksResponse);
  }

  async function runTask(taskType: string, payload: Record<string, unknown> = {}) {
    setPending(taskType);
    try {
      await fetch(`/api/automation/tasks`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          task_type: taskType,
          payload,
        }),
      });
      await refresh();
    } finally {
      setPending(null);
    }
  }

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void refresh();
    }, 0);

    return () => window.clearTimeout(timer);
  }, []);

  return (
    <div className="rounded-md bg-white/10 p-5 ring-1 ring-white/15">
      <p className="text-xs uppercase tracking-[0.2em] text-cyan-100/72">Live Ops</p>
      <div className="mt-3 space-y-2 text-sm text-blue-50/86">
        <p>引擎：{worker?.engine ?? "读取中..."}</p>
        <p>会话目录：{worker?.state_dir ?? "-"}</p>
        <p>登录态文件：{worker?.state_exists ? "已存在" : "还没有"}</p>
      </div>

      <div className="mt-4 space-y-3">
        <button
          onClick={() => void runTask("manual_login")}
          className="w-full rounded-md bg-white px-4 py-3 text-sm font-semibold text-[var(--color-primary)]"
        >
          {pending === "manual_login" ? "等待登录完成..." : "打开登录浏览器"}
        </button>
        <button
          onClick={() => void runTask("login_check")}
          className="w-full rounded-md border border-white/20 px-4 py-3 text-sm font-semibold text-white"
        >
          {pending === "login_check" ? "检测中..." : "检测登录"}
        </button>
        <div className="flex gap-2">
          <input
            value={keyword}
            onChange={(event) => setKeyword(event.target.value)}
            className="w-full rounded-md bg-white/10 px-3 py-3 text-sm text-white outline-none placeholder:text-blue-100/50"
            placeholder="前端 / AI 产品"
          />
          <button
            onClick={() => void runTask("collect_jobs", { keyword })}
            className="rounded-md bg-cyan-200 px-4 py-3 text-sm font-semibold text-[var(--color-primary)]"
          >
            {pending === "collect_jobs" ? "抓取中" : "抓职位"}
          </button>
        </div>
        <button
          onClick={() => void runTask("sync_messages")}
          className="w-full rounded-md border border-white/20 px-4 py-3 text-sm font-semibold text-white"
        >
          {pending === "sync_messages" ? "同步中..." : "同步消息"}
        </button>
      </div>

      <div className="mt-4 rounded-md bg-black/15 p-3 text-xs leading-6 text-blue-100/78">
        {tasks[0] ? JSON.stringify(tasks[0].result) : "还没有执行记录"}
      </div>
    </div>
  );
}
