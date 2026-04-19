import { ArrowUpRight, FileUp, WandSparkles } from "lucide-react";
import { PageIntro, Pill, SectionTitle, Surface } from "@/components/ui";
import { getJson } from "@/lib/api";
import { ResumeLabResponse } from "@/lib/types";

export default async function ResumeLabPage() {
  const data = await getJson<ResumeLabResponse>("resume-lab");

  return (
    <div className="space-y-5">
      <PageIntro
        eyebrow="Resume & Pitch Lab"
        title="简历与话术实验室"
        subtitle="这里先承接 Stitch 的上传、评分、话术生成和进度结构，后面自然可以接上 RAG 和岗位定制版本。"
      />

      <div className="grid gap-4 xl:grid-cols-[0.9fr_1.1fr_0.8fr]">
        <Surface className="space-y-4">
          <SectionTitle title="上传最新简历" subtitle="支持 PDF 与 DOCX，后端会接解析与向量化流程。" />
          <div className="grid min-h-56 place-items-center rounded-md border border-dashed border-[var(--color-line)] bg-[var(--color-soft)] p-6 text-center">
            <div>
              <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-md bg-white ring-1 ring-black/4">
                <FileUp className="h-5 w-5 text-[var(--color-primary)]" />
              </div>
              <p className="mt-4 font-headline text-xl font-bold text-[var(--color-ink)]">拖拽简历到这里</p>
              <p className="mt-2 text-sm text-[var(--color-muted)]">让 AI 自动分析行业竞争力并给出优化建议。</p>
            </div>
          </div>
          <div className="rounded-md bg-[var(--color-primary)] p-5 text-white">
            <p className="text-xs uppercase tracking-[0.22em] text-cyan-100/72">AI 简历评分</p>
            <p className="mt-3 font-headline text-5xl font-extrabold">{data.score}</p>
            <p className="mt-2 text-lg">{data.quality}</p>
            <p className="mt-4 text-sm leading-7 text-blue-100/82">{data.analysis}</p>
          </div>
        </Surface>

        <Surface className="space-y-4">
          <SectionTitle title="AI 行业投递话术" subtitle="根据角色与行业切换不同开场策略。" />
          <div className="space-y-3">
            {data.pitches.map((pitch) => (
              <div key={pitch.label} className="rounded-md bg-[var(--color-soft)] p-4">
                <div className="flex items-center justify-between gap-3">
                  <Pill tone="soft">{pitch.label}</Pill>
                  <button className="inline-flex items-center gap-2 text-sm font-semibold text-[var(--color-primary)]">
                    使用这版
                    <ArrowUpRight className="h-4 w-4" />
                  </button>
                </div>
                <p className="mt-4 text-sm leading-7 text-[var(--color-ink)]">{pitch.content}</p>
              </div>
            ))}
          </div>
        </Surface>

        <div className="space-y-4">
          <Surface className="space-y-4">
            <SectionTitle title="版本库" />
            {data.variants.map((variant) => (
              <div key={variant.name} className="rounded-md bg-[var(--color-soft)] p-4">
                <p className="font-headline text-lg font-bold text-[var(--color-ink)]">{variant.name}</p>
                <p className="mt-1 text-sm text-[var(--color-muted)]">{variant.tag}</p>
              </div>
            ))}
          </Surface>

          <Surface className="space-y-4">
            <div className="flex items-center gap-2 text-[var(--color-primary)]">
              <WandSparkles className="h-4 w-4" />
              <span className="text-sm font-semibold">解析进度</span>
            </div>
            <div className="rounded-md bg-[var(--color-soft)] p-4">
              <div className="flex items-center justify-between text-sm text-[var(--color-muted)]">
                <span>正在比对高薪 JD</span>
                <span>{data.progress}%</span>
              </div>
              <div className="mt-3 h-2 rounded-full bg-white">
                <div className="h-2 rounded-full bg-[var(--color-primary)]" style={{ width: `${data.progress}%` }} />
              </div>
            </div>
          </Surface>
        </div>
      </div>
    </div>
  );
}
