import { BriefcaseBusiness, Sparkles } from "lucide-react";
import { ChatReplyBox } from "@/components/chat-reply-box";
import { PageIntro, Pill, SectionTitle, Surface } from "@/components/ui";
import { getJson } from "@/lib/api";
import { ChatResponse } from "@/lib/types";

export default async function ChatPage() {
  const data = await getJson<ChatResponse>("chat");

  return (
    <div className="space-y-5">
      <PageIntro
        eyebrow="Conversation Studio"
        title="聊天工作台"
        subtitle="把自动筛岗、RAG 召回、首轮沟通和人工放行放在同一个界面里。"
      />

      <div className="grid gap-4 xl:grid-cols-[280px_1fr_300px]">
        <Surface className="space-y-4">
          <SectionTitle title="历史对话" />
          <div className="space-y-2">
            {data.history.map((item) => (
              <div
                key={item.title}
                className={`rounded-md p-4 ${
                  item.active ? "bg-white ring-1 ring-black/5" : "bg-[var(--color-soft)]"
                }`}
              >
                <p className="font-headline text-lg font-bold text-[var(--color-ink)]">{item.title}</p>
                <p className="mt-2 text-sm leading-6 text-[var(--color-muted)]">{item.preview}</p>
                <p className="mt-3 text-xs text-[var(--color-muted)]">{item.time}</p>
              </div>
            ))}
          </div>
        </Surface>

        <Surface className="space-y-5">
          <div className="flex items-center gap-3 border-b border-black/5 pb-4">
            <div className="flex h-10 w-10 items-center justify-center rounded-md bg-[var(--color-primary)] text-white">
              <Sparkles className="h-5 w-5" />
            </div>
            <div>
              <h2 className="font-headline text-xl font-bold text-[var(--color-ink)]">资深前端职位助推</h2>
              <p className="text-xs uppercase tracking-[0.22em] text-emerald-600">实时分析中</p>
            </div>
          </div>

          <div className="space-y-4">
            {data.messages.map((message) => (
              <div
                key={`${message.time}-${message.speaker}`}
                className={`max-w-3xl rounded-md px-4 py-4 text-sm leading-7 ${
                  message.speaker === "assistant"
                    ? "bg-[var(--color-primary)] text-white"
                    : "bg-[var(--color-soft)] text-[var(--color-ink)]"
                }`}
              >
                <p>{message.content}</p>
                <p
                  className={`mt-2 text-xs ${
                    message.speaker === "assistant" ? "text-cyan-100/70" : "text-[var(--color-muted)]"
                  }`}
                >
                  {message.time}
                </p>
              </div>
            ))}
          </div>

          <div className="grid gap-3 md:grid-cols-2">
            {data.recommendations.map((job) => (
              <div key={job.title} className="rounded-md border border-black/5 bg-[var(--color-soft)] p-4">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="font-headline text-xl font-bold text-[var(--color-ink)]">{job.title}</p>
                    <p className="mt-1 text-sm text-[var(--color-muted)]">{job.company}</p>
                  </div>
                  <Pill tone="soft">{job.score}% 匹配</Pill>
                </div>
                <div className="mt-4 flex flex-wrap gap-2">
                  {job.tags.map((tag) => (
                    <Pill key={tag}>{tag}</Pill>
                  ))}
                </div>
                <button className="mt-5 inline-flex items-center gap-2 text-sm font-semibold text-[var(--color-primary)]">
                  <BriefcaseBusiness className="h-4 w-4" />
                  查看详情
                </button>
              </div>
            ))}
          </div>

          <div>
            <div className="mb-3 flex flex-wrap gap-2">
              <Pill tone="soft">优化简历</Pill>
              <Pill>面试模拟</Pill>
              <Pill>薪资分析</Pill>
            </div>
            <ChatReplyBox />
          </div>
        </Surface>

        <Surface className="space-y-4">
          <SectionTitle title="能力雷达" subtitle="RAG 会从简历、项目和历史对话里拼这个视图。" />
          <div className="rounded-md bg-[var(--color-soft)] p-5">
            <div className="mx-auto grid h-48 w-48 place-items-center rounded-[28px] border border-[var(--color-line)]">
              <div className="grid h-36 w-36 place-items-center rounded-[24px] border border-[var(--color-line)]">
                <div className="grid h-24 w-24 place-items-center rounded-[18px] border border-[var(--color-line)]">
                  <span className="font-headline text-3xl font-bold text-[var(--color-primary)]">@</span>
                </div>
              </div>
            </div>
            <div className="mt-5 grid grid-cols-2 gap-3 text-sm text-[var(--color-muted)]">
              {data.radar.axes.map((axis) => (
                <div key={axis} className="rounded-md bg-white px-3 py-2 text-center ring-1 ring-black/4">
                  {axis}
                </div>
              ))}
            </div>
          </div>

          <div className="rounded-md bg-[var(--color-soft)] p-4">
            <p className="text-xs uppercase tracking-[0.2em] text-[var(--color-muted)]">综合匹配度</p>
            <p className="mt-2 font-headline text-4xl font-extrabold text-[var(--color-primary)]">
              {data.radar.score}%
            </p>
            <div className="mt-4 h-2 rounded-full bg-white">
              <div className="h-2 w-[94%] rounded-full bg-[var(--color-primary)]" />
            </div>
          </div>

          <div className="rounded-md border border-[rgba(217,116,80,0.18)] bg-[rgba(255,245,240,0.9)] p-4 text-sm leading-7 text-[var(--color-muted)]">
            <p className="font-semibold text-[var(--color-primary)]">优化建议</p>
            <p className="mt-2">{data.radar.tip}</p>
          </div>
        </Surface>
      </div>
    </div>
  );
}
