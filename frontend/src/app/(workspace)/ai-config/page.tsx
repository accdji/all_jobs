import { KeyRound, PlugZap } from "lucide-react";
import { PageIntro, SectionTitle, Surface, Toggle } from "@/components/ui";
import { getJson } from "@/lib/api";
import { AiConfigResponse } from "@/lib/types";

export default async function AiConfigPage() {
  const data = await getJson<AiConfigResponse>("ai-config");

  return (
    <div className="space-y-5">
      <PageIntro
        eyebrow="AI Config"
        title="AI 智能配置中心"
        subtitle="把消息分类、RAG 检索、沟通策略和自动化执行拆成单独服务后，这里就是你的控制台入口。"
      />

      <div className="grid gap-4 xl:grid-cols-[1.05fr_0.95fr]">
        <Surface className="space-y-5">
          <SectionTitle title="核心 API 设置" subtitle="第一版先保留模型与行为策略位。" />
          <div className="grid gap-3 md:grid-cols-3">
            {data.models.map((model) => (
              <div
                key={model.name}
                className={`rounded-md p-4 ${
                  model.active
                    ? "bg-[var(--color-primary)] text-white"
                    : "bg-[var(--color-soft)] text-[var(--color-ink)]"
                }`}
              >
                <p className={`text-xs uppercase tracking-[0.2em] ${model.active ? "text-cyan-100/70" : "text-[var(--color-muted)]"}`}>
                  {model.provider}
                </p>
                <p className="mt-3 font-headline text-xl font-extrabold">{model.name}</p>
              </div>
            ))}
          </div>

          <div className="grid gap-3 md:grid-cols-2">
            <div className="rounded-md bg-[var(--color-soft)] p-4">
              <div className="flex items-center gap-2 text-[var(--color-primary)]">
                <KeyRound className="h-4 w-4" />
                <span className="text-sm font-semibold">API 密钥</span>
              </div>
              <div className="mt-4 rounded-md bg-white px-3 py-3 text-sm text-slate-400 ring-1 ring-black/4">
                •••••••••••••••••••••••••
              </div>
            </div>
            <div className="rounded-md bg-[var(--color-soft)] p-4">
              <div className="flex items-center gap-2 text-[var(--color-primary)]">
                <PlugZap className="h-4 w-4" />
                <span className="text-sm font-semibold">Base URL</span>
              </div>
              <div className="mt-4 rounded-md bg-white px-3 py-3 text-sm text-slate-400 ring-1 ring-black/4">
                https://api.openai.com/v1
              </div>
            </div>
          </div>

          <div className="space-y-3">
            <SectionTitle title="自动化策略逻辑" />
            {data.toggles.map((toggle) => (
              <div key={toggle.title} className="flex items-center justify-between gap-4 rounded-md bg-[var(--color-soft)] p-4">
                <div>
                  <p className="font-headline text-lg font-bold text-[var(--color-ink)]">{toggle.title}</p>
                  <p className="mt-1 text-sm leading-7 text-[var(--color-muted)]">{toggle.description}</p>
                </div>
                <Toggle enabled={toggle.enabled} />
              </div>
            ))}
          </div>
        </Surface>

        <div className="space-y-4">
          <Surface className="space-y-4 bg-[var(--color-primary)] text-white">
            <SectionTitle title="推送订阅设置" subtitle="客服机器人式回复建议从这里往外分发。" />
            {data.push.map((item) => (
              <div key={item.label} className="flex items-center justify-between gap-4 rounded-md bg-white/10 px-4 py-3">
                <span className="text-sm">{item.label}</span>
                <Toggle enabled={item.enabled} />
              </div>
            ))}
            <button className="mt-2 w-full rounded-md bg-white px-4 py-3 text-sm font-semibold text-[var(--color-primary)]">
              测试连接
            </button>
          </Surface>

          <Surface className="space-y-4">
            <SectionTitle title="系统状态" />
            <div className="space-y-3 text-sm text-[var(--color-muted)]">
              <div className="flex items-center justify-between">
                <span>代理负载</span>
                <span className="font-semibold text-[var(--color-ink)]">{data.status.load}</span>
              </div>
              <div className="flex items-center justify-between">
                <span>可用额度</span>
                <span className="font-semibold text-[var(--color-ink)]">{data.status.credits}</span>
              </div>
              <div className="rounded-md bg-[var(--color-soft)] p-4 leading-7">{data.status.window}</div>
            </div>
          </Surface>
        </div>
      </div>
    </div>
  );
}
