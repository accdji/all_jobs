import { CalendarClock, X } from "lucide-react";
import { PageIntro, Pill, SectionTitle, Surface } from "@/components/ui";
import { getJson } from "@/lib/api";
import { InterviewsResponse } from "@/lib/types";

export default async function InterviewsPage() {
  const data = await getJson<InterviewsResponse>("interviews");

  return (
    <div className="space-y-5">
      <PageIntro
        eyebrow="Interview Hall"
        title="面试确认大厅"
        subtitle={`Agent Alpha 捕获到 ${data.pending_count} 个新的面试机会，建议先从高匹配和高确定性岗位开始。`}
      />

      <div className="grid gap-4 xl:grid-cols-[1.15fr_0.85fr]">
        <Surface className="space-y-4">
          <SectionTitle title="待处理确认" subtitle={`${data.pending_count} 个新面试邀请`} />
          {data.cards.map((card) => (
            <div key={card.company} className="grid gap-4 rounded-md bg-[var(--color-soft)] p-4 md:grid-cols-[0.8fr_1.2fr]">
              <div>
                <div className="flex h-16 w-16 items-center justify-center rounded-md bg-white font-headline text-xl font-extrabold text-[var(--color-primary)] ring-1 ring-black/4">
                  {card.company.slice(0, 1)}
                </div>
                <h3 className="mt-4 font-headline text-2xl font-bold text-[var(--color-ink)]">{card.role}</h3>
                <p className="mt-1 text-sm text-[var(--color-muted)]">{card.company}</p>
                <div className="mt-4 space-y-2 text-sm text-[var(--color-muted)]">
                  <p>{card.time}</p>
                  <p>{card.mode}</p>
                </div>
              </div>
              <div className="space-y-4">
                <div className="rounded-md bg-white p-4 ring-1 ring-black/4">
                  <Pill tone="soft">AI 推荐理由</Pill>
                  <p className="mt-3 text-sm leading-7 text-[var(--color-ink)]">“{card.reason}”</p>
                </div>
                <div className="rounded-md border border-black/5 bg-white p-4">
                  <p className="text-xs uppercase tracking-[0.2em] text-[var(--color-muted)]">对方消息</p>
                  <p className="mt-2 text-sm leading-7 text-[var(--color-ink)]">{card.excerpt}</p>
                </div>
                <div className="flex flex-wrap gap-3">
                  <button className="rounded-md bg-[var(--color-primary)] px-4 py-3 text-sm font-semibold text-white">
                    确认参加
                  </button>
                  <button className="rounded-md border border-[var(--color-line)] bg-white px-4 py-3 text-sm font-semibold text-[var(--color-ink)]">
                    改时间
                  </button>
                  <button className="inline-flex items-center gap-2 rounded-md px-1 py-3 text-sm font-semibold text-rose-600">
                    <X className="h-4 w-4" />
                    拒绝
                  </button>
                </div>
              </div>
            </div>
          ))}
        </Surface>

        <div className="space-y-4">
          <Surface className="space-y-5 bg-[var(--color-primary)] text-white">
            <SectionTitle title="面试进度看板" />
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-xs uppercase tracking-[0.2em] text-cyan-100/60">本周面试</p>
                <p className="mt-2 font-headline text-5xl font-extrabold">{data.board.weekly}</p>
              </div>
              <div>
                <p className="text-xs uppercase tracking-[0.2em] text-cyan-100/60">匹配率</p>
                <p className="mt-2 font-headline text-5xl font-extrabold">{data.board.match}</p>
              </div>
            </div>
            <div>
              <div className="flex items-center justify-between text-sm text-cyan-100/70">
                <span>简历解析进度</span>
                <span>{data.board.resume_progress}</span>
              </div>
              <div className="mt-2 h-2 rounded-full bg-white/10">
                <div className="h-2 w-full rounded-full bg-cyan-200" />
              </div>
            </div>
          </Surface>

          <Surface className="space-y-4">
            <SectionTitle title="即将到来" />
            {data.board.upcoming.map((item) => (
              <div key={item.title} className="flex items-center gap-4 rounded-md bg-[var(--color-soft)] p-4">
                <div className="rounded-md bg-white px-3 py-3 text-center ring-1 ring-black/4">
                  <p className="text-sm font-semibold text-[var(--color-muted)]">{item.date}</p>
                </div>
                <div>
                  <p className="font-headline text-lg font-bold text-[var(--color-ink)]">{item.title}</p>
                  <p className="mt-1 text-sm text-[var(--color-muted)]">{item.time}</p>
                </div>
              </div>
            ))}
          </Surface>

          <Surface className="space-y-3">
            <div className="flex items-center gap-2 text-[var(--color-primary)]">
              <CalendarClock className="h-4 w-4" />
              <span className="text-sm font-semibold">待办提醒</span>
            </div>
            <p className="text-sm leading-7 text-[var(--color-muted)]">{data.board.tip}</p>
          </Surface>
        </div>
      </div>
    </div>
  );
}
