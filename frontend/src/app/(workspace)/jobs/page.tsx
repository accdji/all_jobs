import { Bookmark, Send } from "lucide-react";
import { PageIntro, Pill, SectionTitle, Surface } from "@/components/ui";
import { getJson } from "@/lib/api";
import { JobsResponse } from "@/lib/types";

export default async function JobsPage() {
  const data = await getJson<JobsResponse>("jobs");

  return (
    <div className="space-y-5">
      <PageIntro
        eyebrow="Job Pool"
        title="职位池"
        subtitle={`围绕 ${data.summary.keyword} 的自动抓取池，当前共发现 ${data.summary.count} 个候选岗位。`}
      />

      <div className="flex flex-wrap gap-2">
        {data.filters.map((filter) => (
          <Pill key={filter}>{filter}</Pill>
        ))}
      </div>

      <div className="grid gap-4 xl:grid-cols-[0.95fr_1.05fr]">
        <Surface className="space-y-3">
          <SectionTitle title="职位列表" subtitle="按匹配分和回应概率排序。" />
          {data.jobs.map((job) => (
            <div key={job.role} className="rounded-md bg-[var(--color-soft)] p-4">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <h3 className="font-headline text-2xl font-bold text-[var(--color-ink)]">{job.role}</h3>
                  <p className="mt-1 text-sm text-[var(--color-muted)]">
                    {job.company} · {job.location}
                  </p>
                </div>
                <Pill tone="soft">{job.score}%</Pill>
              </div>
              <div className="mt-4 flex flex-wrap gap-2">
                {job.tags.map((tag) => (
                  <Pill key={tag}>{tag}</Pill>
                ))}
                <Pill tone="soft">{job.salary}</Pill>
              </div>
              <p className="mt-4 text-sm leading-7 text-[var(--color-muted)]">{job.summary}</p>
            </div>
          ))}
        </Surface>

        <Surface className="space-y-4">
          <SectionTitle title={data.detail.role} subtitle={`${data.detail.company} · ${data.detail.salary}`} />
          <div className="flex flex-wrap gap-2">
            {data.detail.meta.map((meta) => (
              <Pill key={meta}>{meta}</Pill>
            ))}
          </div>
          <div className="space-y-3 rounded-md bg-[var(--color-soft)] p-5">
            <p className="text-xs uppercase tracking-[0.2em] text-[var(--color-muted)]">职位描述</p>
            <ul className="space-y-3 text-sm leading-7 text-[var(--color-ink)]">
              {data.detail.description.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </div>
          <div className="grid gap-3 md:grid-cols-2">
            <button className="inline-flex items-center justify-center gap-2 rounded-md border border-[var(--color-line)] bg-white px-4 py-3 text-sm font-semibold text-[var(--color-ink)]">
              <Bookmark className="h-4 w-4" />
              收藏职位
            </button>
            <button className="inline-flex items-center justify-center gap-2 rounded-md bg-[var(--color-primary)] px-4 py-3 text-sm font-semibold text-white">
              <Send className="h-4 w-4" />
              立即投递简历
            </button>
          </div>
        </Surface>
      </div>
    </div>
  );
}
