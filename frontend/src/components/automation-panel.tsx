"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

type WorkerStatus = {
  base_url: string;
  state_dir: string;
  state_exists: boolean;
  login_status: string;
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

type OverviewResponse = {
  hero: {
    status: string;
  };
  threads: Array<{
    company: string;
    time: string;
  }>;
};

function formatTaskMessage(task: Task | null) {
  if (!task) {
    return "等待下一次操作";
  }

  const note = typeof task.result.note === "string" ? task.result.note : null;
  const nextStep = typeof task.result.next_step === "string" ? task.result.next_step : null;
  return note ?? nextStep ?? "任务已完成";
}

function getTaskCount(task: Task | null, key: string) {
  const value = task?.result[key];
  return typeof value === "number" ? value : null;
}

function getTaskText(task: Task | null, key: string) {
  const value = task?.result[key];
  return typeof value === "string" ? value : "";
}

export function AutomationPanel() {
  const router = useRouter();
  const [worker, setWorker] = useState<WorkerStatus | null>(null);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [overview, setOverview] = useState<OverviewResponse | null>(null);
  const [keyword, setKeyword] = useState("前端");
  const [pending, setPending] = useState<string | null>(null);

  async function refresh() {
    const [workerResponse, tasksResponse, overviewResponse] = await Promise.all([
      fetch("/api/automation/worker").then((res) => res.json()),
      fetch("/api/automation/tasks").then((res) => res.json()),
      fetch("/api/overview", { cache: "no-store" }).then((res) => res.json()),
    ]);

    setWorker(workerResponse);
    setTasks(tasksResponse);
    setOverview(overviewResponse);
  }

  async function createTask(taskType: string, payload: Record<string, unknown> = {}) {
    await fetch("/api/automation/tasks", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        task_type: taskType,
        payload,
      }),
    });
  }

  async function runTask(taskType: string, payload: Record<string, unknown> = {}) {
    setPending(taskType);
    try {
      await createTask(taskType, payload);
      await refresh();
      router.refresh();
    } finally {
      setPending(null);
    }
  }

  useEffect(() => {
    const initialTimer = window.setTimeout(() => {
      void refresh();
    }, 0);

    return () => window.clearTimeout(initialTimer);
  }, []);

  useEffect(() => {
    let cancelled = false;

    const tick = async () => {
      await refresh();

      if (!cancelled && pending === null && worker?.login_status === "logged_in") {
        await createTask("sync_messages");
        await refresh();
      }

      if (!cancelled) {
        router.refresh();
      }
    };

    const pollTimer = window.setInterval(() => {
      void tick();
    }, 8000);

    return () => {
      cancelled = true;
      window.clearInterval(pollTimer);
    };
  }, [pending, router, worker?.login_status]);

  const latestTask = tasks[0] ?? null;
  const latestLoginTask = tasks.find((task) => task.task_type === "manual_login") ?? null;
  const latestSyncTask = tasks.find((task) => task.task_type === "sync_messages") ?? null;
  const latestApplyTask = tasks.find((task) => task.task_type === "collect_jobs") ?? null;
  const threadCount = getTaskCount(latestSyncTask, "threads_synced") ?? overview?.threads.length ?? 0;
  const applyCount = getTaskCount(latestApplyTask, "collected") ?? 0;
  const appliedCount = getTaskCount(latestApplyTask, "applied_count") ?? 0;
  const latestApplyMessage = getTaskText(latestApplyTask, "note");
  const loginStatus = worker?.login_status === "logged_in" ? "已登录" : "未登录";
  const loginHint =
    worker?.login_status === "logged_in"
      ? formatTaskMessage(latestLoginTask)
      : "浏览器关闭后登录状态会立即失效，重新打开需要重新登录。";

  return (
    <div className="rounded-md bg-white/10 p-5 ring-1 ring-white/15">
      <div className="flex items-center justify-between gap-3">
        <p className="text-xs uppercase tracking-[0.2em] text-cyan-100/72">Live Ops</p>
        <span className="rounded-full bg-white/12 px-2 py-1 text-[10px] uppercase tracking-[0.18em] text-cyan-50/80">
          8s auto sync
        </span>
      </div>

      <div className="mt-4 grid gap-3 text-sm text-blue-50/88">
        <div className="rounded-md bg-black/15 p-3">
          <p className="text-[11px] uppercase tracking-[0.18em] text-cyan-100/64">登录状态</p>
          <p className="mt-2 text-base font-semibold text-white">{loginStatus}</p>
          <p className="mt-1 text-xs text-blue-100/72">{loginHint}</p>
        </div>

        <div className="grid gap-3 sm:grid-cols-2">
          <div className="rounded-md bg-black/15 p-3">
            <p className="text-[11px] uppercase tracking-[0.18em] text-cyan-100/64">同步会话</p>
            <p className="mt-2 text-base font-semibold text-white">{threadCount} 条</p>
            <p className="mt-1 text-xs text-blue-100/72">
              {worker?.login_status === "logged_in" ? formatTaskMessage(latestSyncTask) : "登录成功后自动同步"}
            </p>
          </div>
          <div className="rounded-md bg-black/15 p-3">
            <p className="text-[11px] uppercase tracking-[0.18em] text-cyan-100/64">浏览器会话</p>
            <p className="mt-2 text-base font-semibold text-white">{worker?.state_exists ? "当前在线" : "未连接"}</p>
            <p className="mt-1 text-xs text-blue-100/72">{worker?.state_dir ?? "-"}</p>
          </div>
        </div>

        <div className="rounded-md bg-black/15 p-3 text-xs leading-6 text-blue-100/74">
          <p>引擎：{worker?.engine ?? "读取中..."}</p>
          <p>模式：{worker?.mode ?? "-"}</p>
          <p>向量库：{worker?.vector_store_backend ?? "-"}</p>
        </div>
      </div>

      <div className="mt-4 space-y-3">
        <button
          onClick={() => void runTask("manual_login")}
          className="w-full rounded-md bg-white px-4 py-3 text-sm font-semibold text-[var(--color-primary)]"
        >
          {pending === "manual_login" ? "等待登录完成..." : "打开登录浏览器"}
        </button>

        <div className="flex gap-2">
          <input
            value={keyword}
            onChange={(event) => setKeyword(event.target.value)}
            className="w-full rounded-md bg-white/10 px-3 py-3 text-sm text-white outline-none placeholder:text-blue-100/50"
            placeholder="前端 / AI 产品 / 设计工程"
          />
          <button
            onClick={() => void runTask("collect_jobs", { keyword, auto_apply_limit: 1 })}
            className="rounded-md bg-cyan-200 px-4 py-3 text-sm font-semibold text-[var(--color-primary)]"
          >
            {pending === "collect_jobs" ? "进行中..." : "开始应聘"}
          </button>
        </div>
      </div>

      <div className="mt-4 rounded-md bg-black/15 p-3 text-xs leading-6 text-blue-100/78">
        <p>最新任务：{latestTask?.task_type ?? "暂无"}</p>
        <p>状态说明：{formatTaskMessage(latestTask)}</p>
        <p>本次抓到职位数：{applyCount}</p>
        <p>本次自动发起沟通数：{appliedCount}</p>
        <p>最近应聘结果：{latestApplyMessage || "暂无"}</p>
      </div>
    </div>
  );
}
