import { ArrowRight, Sparkles } from "lucide-react";
import { AutomationPanel } from "@/components/automation-panel";
import { PageIntro, SectionTitle, StatCard, Surface } from "@/components/ui";
import { getJson } from "@/lib/api";
import { OverviewResponse } from "@/lib/types";

export default async function DashboardPage() {
  const data = await getJson<OverviewResponse>("overview");

  return (
    <div className="space-y-5">
      <PageIntro
        eyebrow="Automation Dashboard"
        title={data.hero.title}
        subtitle={data.hero.subtitle}
        aside={<AutomationPanel />}
      />

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {data.stats.map((stat) => (
          <StatCard key={stat.label} label={stat.label} value={stat.value} hint={stat.delta} />
        ))}
      </div>

      <div className="grid gap-4 xl:grid-cols-[1.2fr_0.8fr]">
        <Surface className="space-y-4">
          <SectionTitle
            title="自动投递流水"
            subtitle="这里会显示最新抓到的 BOSS 职位和首轮沟通建议。"
          />
          <div className="space-y-3">
            {data.pipeline.map((item) => (
              <div key={`${item.company}-${item.role}`} className="grid gap-4 rounded-md bg-[var(--color-soft)] p-4 md:grid-cols-[1fr_1.2fr]">
                <div>
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <h3 className="font-headline text-xl font-bold text-[var(--color-ink)]">
                        {item.role}
                      </h3>
                      <p className="mt-1 text-sm text-[var(--color-muted)]">{item.company}</p>
                    </div>
                    <span className="rounded-md bg-cyan-50 px-2 py-1 text-xs font-medium text-cyan-900">
                      {item.salary}
                    </span>
                  </div>
                  <p className="mt-4 text-xs uppercase tracking-[0.2em] text-[var(--color-muted)]">
                    {item.stage}
                  </p>
                  <p className="mt-2 text-sm leading-7 text-[var(--color-muted)]">{item.summary}</p>
                </div>
                <div className="rounded-md bg-white p-4 ring-1 ring-black/4">
                  <p className="text-xs uppercase tracking-[0.2em] text-[var(--color-muted)]">AI 投递话术</p>
                  <p className="mt-3 text-sm leading-7 text-[var(--color-ink)]">“{item.message}”</p>
                </div>
              </div>
            ))}
          </div>
        </Surface>

        <Surface className="space-y-4">
          <SectionTitle title="AI 直连对话" subtitle="同步到的 HR 会话和建议回复会先出现在这里。" />
          <div className="space-y-4">
            {data.threads.map((thread) => (
              <div key={`${thread.company}-${thread.time}`} className="rounded-md bg-[var(--color-soft)] p-4">
                <div className="flex items-center justify-between gap-3">
                  <p className="font-headline text-lg font-bold text-[var(--color-ink)]">{thread.company}</p>
                  <span className="text-xs text-[var(--color-muted)]">{thread.time}</span>
                </div>
                <div className="mt-4 rounded-md bg-white p-4 ring-1 ring-black/4">
                  <p className="text-xs uppercase tracking-[0.2em] text-[var(--color-muted)]">HR 来信</p>
                  <p className="mt-2 text-sm leading-7 text-[var(--color-ink)]">{thread.incoming}</p>
                </div>
                <div className="mt-3 rounded-md bg-[var(--color-primary)] p-4 text-white">
                  <p className="text-xs uppercase tracking-[0.2em] text-cyan-100/72">AI 草稿</p>
                  <p className="mt-2 text-sm leading-7 text-blue-50">{thread.reply}</p>
                </div>
              </div>
            ))}
          </div>
        </Surface>
      </div>

      <section className="rounded-md bg-[linear-gradient(135deg,#0d1f4f,#224ea8)] px-6 py-6 text-white">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <div className="flex items-center gap-2 text-cyan-100/80">
              <Sparkles className="h-4 w-4" />
              <span className="text-xs uppercase tracking-[0.24em]">Strategy Insight</span>
            </div>
            <p className="mt-3 max-w-4xl text-lg leading-8 text-blue-50/94">{data.insight}</p>
          </div>
          <button className="inline-flex items-center gap-2 rounded-md bg-white px-4 py-3 text-sm font-semibold text-[var(--color-primary)]">
            进入简历实验室
            <ArrowRight className="h-4 w-4" />
          </button>
        </div>
      </section>
    </div>
  );
}
