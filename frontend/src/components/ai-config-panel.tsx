"use client";

import { useMemo, useState } from "react";
import {
  BadgeInfo,
  BellRing,
  CircleHelp,
  Download,
  FileText,
  IdCard,
  KeyRound,
  Mail,
  MessageSquareText,
  Plus,
  ShieldCheck,
  Trash2,
  Upload,
  View,
} from "lucide-react";
import { postJson, putJson } from "@/lib/api";
import { AiConfigResponse, AiConfigUpdateRequest, ChatReplyResponse } from "@/lib/types";

type Props = {
  initialData: AiConfigResponse;
};

function FieldLabel({ children }: { children: React.ReactNode }) {
  return <label className="px-1 text-sm font-semibold text-slate-600">{children}</label>;
}

function FileActionButton({ children }: { children: React.ReactNode }) {
  return (
    <button className="rounded-lg p-2 text-slate-400 transition-colors hover:bg-white hover:text-[var(--color-primary)]">
      {children}
    </button>
  );
}

export function AiConfigPanel({ initialData }: Props) {
  const [data, setData] = useState(initialData);
  const [apiKey, setApiKey] = useState("");
  const [provider, setProvider] = useState(initialData.provider);
  const [baseUrl, setBaseUrl] = useState(initialData.base_url);
  const [model, setModel] = useState(initialData.model);
  const [salaryMin, setSalaryMin] = useState(initialData.profile.desired_salary_min);
  const [salaryMax, setSalaryMax] = useState(initialData.profile.desired_salary_max);
  const [preferredLocation, setPreferredLocation] = useState(initialData.profile.preferred_location);
  const [skillsInput, setSkillsInput] = useState(initialData.profile.skills.join(", "));
  const [summary, setSummary] = useState(initialData.profile.summary);
  const [subscriptions, setSubscriptions] = useState(initialData.subscriptions);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");
  const [testPrompt, setTestPrompt] = useState("你现在对我的了解有多少？请从技能、偏好、岗位记录、面试经历四个方面总结。");
  const [testing, setTesting] = useState(false);
  const [testError, setTestError] = useState("");
  const [testReply, setTestReply] = useState<ChatReplyResponse | null>(null);

  const skillTags = useMemo(
    () =>
      skillsInput
        .split(",")
        .map((item) => item.trim())
        .filter(Boolean),
    [skillsInput]
  );

  const subscriptionIcons: Record<string, React.ReactNode> = {
    feishu: <MessageSquareText className="h-6 w-6" />,
    wechat: <MessageSquareText className="h-6 w-6" />,
    email: <Mail className="h-6 w-6" />,
  };

  async function handleSave() {
    setSaving(true);
    setMessage("");

    const payload: AiConfigUpdateRequest = {
      api_key: apiKey.trim() || null,
      provider,
      base_url: baseUrl.trim(),
      model: model.trim(),
      profile: {
        desired_salary_min: salaryMin.trim(),
        desired_salary_max: salaryMax.trim(),
        preferred_location: preferredLocation,
        skills: skillTags,
        summary: summary.trim(),
      },
      subscriptions,
    };

    try {
      const next = await putJson<AiConfigResponse>("ai-config", payload);
      setData(next);
      setApiKey("");
      setProvider(next.provider);
      setBaseUrl(next.base_url);
      setModel(next.model);
      setSalaryMin(next.profile.desired_salary_min);
      setSalaryMax(next.profile.desired_salary_max);
      setPreferredLocation(next.profile.preferred_location);
      setSkillsInput(next.profile.skills.join(", "));
      setSummary(next.profile.summary);
      setSubscriptions(next.subscriptions);
      setMessage("配置已保存");
    } catch {
      setMessage("保存失败，请稍后重试");
    } finally {
      setSaving(false);
    }
  }

  async function handleAiTest() {
    setTesting(true);
    setTestError("");

    try {
      const reply = await postJson<ChatReplyResponse>("chat/reply", {
        message: testPrompt.trim(),
      });
      setTestReply(reply);
    } catch {
      setTestError("AI 测试失败，请先确认 API Key、Base URL 和模型配置可用。");
    } finally {
      setTesting(false);
    }
  }

  return (
    <div className="space-y-8 px-1 pb-6 pt-1">
      <section className="flex flex-col gap-6 xl:flex-row xl:items-end xl:justify-between">
        <div className="space-y-3">
          <h1 className="font-headline text-[44px] font-extrabold tracking-tight text-[var(--color-primary)]">
            AI 智能配置中心
          </h1>
          <p className="max-w-3xl text-base leading-8 text-slate-500">
            欢迎进入数字策展空间。在这里，您可以精细化调整 AI 的面试逻辑，配置自己的模型密钥，并维护真实知识库。
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          {message ? <span className="text-sm text-slate-500">{message}</span> : null}
          <button className="rounded-lg border border-[#d2d7e2] bg-white px-6 py-2.5 text-sm font-semibold text-[var(--color-primary)] transition-colors hover:bg-[var(--color-soft)]">
            预览简历
          </button>
          <button
            className="rounded-lg bg-[var(--color-primary)] px-6 py-2.5 text-sm font-semibold text-white shadow-[0_14px_28px_rgba(0,25,68,0.18)] transition-transform hover:scale-[1.02] active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-70"
            disabled={saving}
            onClick={handleSave}
          >
            {saving ? "保存中..." : "保存所有配置"}
          </button>
        </div>
      </section>

      <div className="grid gap-8 xl:grid-cols-[minmax(380px,1fr)_minmax(540px,1.28fr)]">
        <div className="space-y-8">
          <section className="rounded-[24px] bg-white p-8 shadow-[0_18px_48px_rgba(0,25,68,0.06)]">
            <div className="mb-8 flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-[#dbe6ff] text-[var(--color-primary)]">
                <IdCard className="h-5 w-5" />
              </div>
              <div>
                <h2 className="font-headline text-[26px] font-bold text-[var(--color-ink)]">个人信息补充</h2>
                <p className="text-xs text-slate-400">完善关键数据，提升 AI 匹配精度</p>
              </div>
            </div>

            <form className="space-y-6" onSubmit={(event) => event.preventDefault()}>
              <div className="space-y-2">
                <FieldLabel>期望薪资范围</FieldLabel>
                <div className="grid gap-4 md:grid-cols-2">
                  <input
                    className="w-full rounded-lg border-none bg-[var(--color-soft)] px-4 py-3 text-sm text-[var(--color-ink)] outline-none ring-0 placeholder:text-slate-400 focus:ring-2 focus:ring-[rgba(0,25,68,0.08)]"
                    placeholder="最低 (k)"
                    type="text"
                    value={salaryMin}
                    onChange={(event) => setSalaryMin(event.target.value)}
                  />
                  <input
                    className="w-full rounded-lg border-none bg-[var(--color-soft)] px-4 py-3 text-sm text-[var(--color-ink)] outline-none ring-0 placeholder:text-slate-400 focus:ring-2 focus:ring-[rgba(0,25,68,0.08)]"
                    placeholder="最高 (k)"
                    type="text"
                    value={salaryMax}
                    onChange={(event) => setSalaryMax(event.target.value)}
                  />
                </div>
              </div>

              <div className="space-y-2">
                <FieldLabel>期望工作地点</FieldLabel>
                <select
                  className="w-full rounded-lg border-none bg-[var(--color-soft)] px-4 py-3 text-sm text-[var(--color-ink)] outline-none focus:ring-2 focus:ring-[rgba(0,25,68,0.08)]"
                  value={preferredLocation}
                  onChange={(event) => setPreferredLocation(event.target.value)}
                >
                  <option>北京</option>
                  <option>上海</option>
                  <option>深圳</option>
                  <option>杭州</option>
                  <option>远程办公</option>
                </select>
              </div>

              <div className="space-y-2">
                <FieldLabel>核心技能标签</FieldLabel>
                <div className="rounded-lg bg-[var(--color-soft)] p-4">
                  <div className="mb-3 flex min-h-[44px] flex-wrap gap-2">
                    {skillTags.map((tag) => (
                      <span
                        key={tag}
                        className="inline-flex items-center gap-2 rounded-md bg-[var(--color-primary)] px-3 py-1 text-xs font-medium text-white"
                      >
                        {tag}
                      </span>
                    ))}
                    {!skillTags.length ? (
                      <span className="text-xs text-slate-400">用英文逗号分隔多个技能标签</span>
                    ) : null}
                  </div>
                  <input
                    className="w-full rounded-lg border-none bg-white px-4 py-3 text-sm text-[var(--color-ink)] outline-none placeholder:text-slate-400 focus:ring-2 focus:ring-[rgba(0,25,68,0.08)]"
                    placeholder="例如：React, TypeScript, Three.js"
                    type="text"
                    value={skillsInput}
                    onChange={(event) => setSkillsInput(event.target.value)}
                  />
                </div>
              </div>

              <div className="space-y-2">
                <FieldLabel>自我介绍摘要</FieldLabel>
                <textarea
                  className="min-h-[136px] w-full resize-none rounded-lg border-none bg-[var(--color-soft)] px-4 py-3 text-sm text-[var(--color-ink)] outline-none placeholder:text-slate-400 focus:ring-2 focus:ring-[rgba(0,25,68,0.08)]"
                  placeholder="简述您的职业核心竞争力..."
                  value={summary}
                  onChange={(event) => setSummary(event.target.value)}
                />
              </div>
            </form>
          </section>

          <section className="rounded-[24px] bg-white p-8 shadow-[0_18px_48px_rgba(0,25,68,0.06)]">
            <div className="mb-6 flex items-center justify-between">
              <h2 className="font-headline text-xl font-bold text-[var(--color-ink)]">模型接入配置</h2>
              <span className="rounded bg-[#dbe6ff] px-2 py-1 text-xs font-bold text-[var(--color-primary)]">
                Live
              </span>
            </div>

            <div className="space-y-4">
              <div className="space-y-2">
                <FieldLabel>API Key</FieldLabel>
                <div className="rounded-lg bg-[var(--color-soft)] p-4">
                  <div className="mb-3 flex items-center gap-2 text-sm text-slate-500">
                    <KeyRound className="h-4 w-4 text-[var(--color-primary)]" />
                    <span>
                      {data.api_key_configured
                        ? `已从后端环境变量读取：${data.api_key_masked}`
                        : "后端环境变量中尚未配置可用的模型 Key"}
                    </span>
                  </div>
                  <input
                    className="w-full rounded-lg border-none bg-white px-4 py-3 text-sm text-[var(--color-ink)] outline-none placeholder:text-slate-400 focus:ring-2 focus:ring-[rgba(0,25,68,0.08)]"
                    placeholder="输入新的模型 Key；保存后会写入后端 .env，不会写入 agent-state.json"
                    type="password"
                    value={apiKey}
                    onChange={(event) => setApiKey(event.target.value)}
                  />
                </div>
              </div>

              <div className="space-y-2">
                <FieldLabel>供应商</FieldLabel>
                <select
                  className="w-full rounded-lg border-none bg-[var(--color-soft)] px-4 py-3 text-sm text-[var(--color-ink)] outline-none focus:ring-2 focus:ring-[rgba(0,25,68,0.08)]"
                  value={provider}
                  onChange={(event) => {
                    const nextProvider = event.target.value;
                    const preset = data.providers.find((item) => item.value === nextProvider);
                    setProvider(nextProvider);
                    if (preset) {
                      setBaseUrl(preset.default_base_url);
                      setModel(preset.default_model);
                    }
                  }}
                >
                  {data.providers.map((item) => (
                    <option key={item.value} value={item.value}>
                      {item.label}
                    </option>
                  ))}
                </select>
              </div>

              <div className="space-y-2">
                <FieldLabel>Base URL</FieldLabel>
                <input
                  className="w-full rounded-lg border-none bg-[var(--color-soft)] px-4 py-3 text-sm text-[var(--color-ink)] outline-none placeholder:text-slate-400 focus:ring-2 focus:ring-[rgba(0,25,68,0.08)]"
                  placeholder="https://api.openai.com/v1"
                  type="text"
                  value={baseUrl}
                  onChange={(event) => setBaseUrl(event.target.value)}
                />
              </div>

              <div className="space-y-2">
                <FieldLabel>模型</FieldLabel>
                <input
                  className="w-full rounded-lg border-none bg-[var(--color-soft)] px-4 py-3 text-sm text-[var(--color-ink)] outline-none placeholder:text-slate-400 focus:ring-2 focus:ring-[rgba(0,25,68,0.08)]"
                  list="ai-model-options"
                  placeholder="输入模型名称，例如 gpt-4.1-mini / gemini-2.5-flash / qwen-plus"
                  type="text"
                  value={model}
                  onChange={(event) => setModel(event.target.value)}
                />
                <datalist id="ai-model-options">
                  {data.available_models.map((item) => (
                    <option key={`${item.label}-${item.value}`} value={item.value} />
                  ))}
                  {data.providers.map((item) =>
                    item.default_model ? <option key={`${item.value}-default-model`} value={item.default_model} /> : null
                  )}
                </datalist>
              </div>
            </div>
          </section>
        </div>

        <div className="space-y-8">
          <section className="overflow-hidden rounded-[24px] bg-[linear-gradient(135deg,#0f172a_0%,#1e293b_48%,#0f766e_100%)] p-8 text-white shadow-[0_18px_48px_rgba(0,25,68,0.16)]">
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-xs font-bold uppercase tracking-[0.28em] text-cyan-100/72">AI Test</p>
                <h2 className="mt-3 font-headline text-[28px] font-bold">用同一套求职模型测试 AI 对你的了解</h2>
                <p className="mt-3 max-w-2xl text-sm leading-7 text-cyan-50/78">
                  这里调用的就是当前保存的求职模型配置，也会复用相同的知识库、岗位记录、会话摘要和面试信息。
                </p>
              </div>
              <div className="rounded-2xl border border-white/15 bg-white/10 px-4 py-3 text-right text-xs leading-6 text-cyan-50/78">
                <p>Provider：{provider}</p>
                <p>Model：{model}</p>
              </div>
            </div>

            <div className="mt-6 grid gap-6 xl:grid-cols-[minmax(260px,1.05fr)_minmax(280px,0.95fr)]">
              <div className="rounded-[20px] border border-white/12 bg-black/10 p-5 backdrop-blur-sm">
                <FieldLabel>测试问题</FieldLabel>
                <textarea
                  className="mt-3 min-h-[176px] w-full resize-none rounded-[18px] border border-white/10 bg-white/8 px-4 py-4 text-sm leading-7 text-white outline-none placeholder:text-cyan-50/40 focus:ring-2 focus:ring-white/20"
                  placeholder="你可以问：你了解我什么、你觉得我适合投什么岗位、我的求职短板是什么..."
                  value={testPrompt}
                  onChange={(event) => setTestPrompt(event.target.value)}
                />
                <div className="mt-4 flex items-center justify-between gap-4">
                  <div className="text-xs leading-6 text-cyan-50/68">
                    <p>会带入当前 AI 配置中的个人档案。</p>
                    <p>也会读取 RAG 中的岗位、会话、面试记忆。</p>
                  </div>
                  <button
                    className="rounded-xl bg-white px-5 py-3 text-sm font-semibold text-slate-900 transition-transform hover:scale-[1.02] active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-60"
                    disabled={testing || !testPrompt.trim()}
                    onClick={handleAiTest}
                  >
                    {testing ? "测试中..." : "开始测试"}
                  </button>
                </div>
                {testError ? <p className="mt-4 text-sm text-rose-200">{testError}</p> : null}
              </div>

              <div className="rounded-[20px] border border-white/12 bg-white/10 p-5 backdrop-blur-sm">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <p className="text-sm font-semibold text-white">模型回答</p>
                    <p className="mt-1 text-xs text-cyan-50/68">
                      {testReply ? `${testReply.provider} / ${testReply.model}` : "运行后会显示这次调用到的模型"}
                    </p>
                  </div>
                  <span className="rounded-full border border-white/12 bg-white/10 px-3 py-1 text-[11px] uppercase tracking-[0.2em] text-cyan-50/70">
                    {testReply ? `${Math.round(testReply.confidence * 100)}% confidence` : "ready"}
                  </span>
                </div>

                <div className="mt-5 rounded-[18px] bg-slate-950/36 p-4 text-sm leading-7 text-cyan-50/92">
                  {testReply ? (
                    <div className="space-y-4">
                      <p>{testReply.draft_reply}</p>
                      <div className="rounded-2xl border border-white/8 bg-white/5 p-4 text-xs leading-6 text-cyan-50/74">
                        <p>意图：{testReply.intent}</p>
                        <p>建议动作：{testReply.suggested_action}</p>
                        <p>命中知识片段：{testReply.retrieved.length}</p>
                      </div>
                    </div>
                  ) : (
                    <p>
                      这里会显示模型基于当前求职档案、RAG 和记忆给出的真实回答。最适合用来检查系统到底了解你多少，以及还有哪些信息没有进入知识库。
                    </p>
                  )}
                </div>

                <div className="mt-4 flex flex-wrap gap-2">
                  {(testReply?.retrieved ?? []).slice(0, 4).map((item) => (
                    <span
                      key={item.id}
                      className="rounded-full border border-white/12 bg-white/8 px-3 py-1 text-[11px] text-cyan-50/78"
                    >
                      {item.title}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </section>

          <section className="rounded-[24px] bg-white p-8 shadow-[0_18px_48px_rgba(0,25,68,0.06)]">
            <div className="mb-8 flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-[rgba(225,124,90,0.16)] text-[#a54b27]">
                <BellRing className="h-5 w-5" />
              </div>
              <div>
                <h2 className="font-headline text-[26px] font-bold text-[var(--color-ink)]">通知订阅</h2>
                <p className="text-xs text-slate-400">同步最新的求职动态至您的常用终端</p>
              </div>
            </div>

            <div className="grid gap-4 md:grid-cols-3">
              {subscriptions.map((item) => (
                <div
                  key={item.key}
                  className="rounded-[18px] border border-[#edf1f6] bg-white p-6 shadow-[0_10px_24px_rgba(0,25,68,0.04)]"
                >
                  <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-[var(--color-soft)] text-[var(--color-primary)]">
                    {subscriptionIcons[item.channel] ?? <BellRing className="h-6 w-6" />}
                  </div>
                  <div className="mt-5">
                    <h3 className="font-headline text-2xl font-bold text-[var(--color-ink)]">{item.label}</h3>
                    <p className="mt-1 text-sm text-slate-400">{item.description}</p>
                  </div>
                  <button
                    className={`mt-6 w-full rounded-lg px-4 py-3 text-sm font-semibold transition-colors ${
                      item.connected
                        ? "bg-[var(--color-primary)] text-white"
                        : "bg-[var(--color-soft)] text-[var(--color-ink)] hover:bg-[#dfe7f5]"
                    }`}
                    onClick={() =>
                      setSubscriptions((current) =>
                        current.map((subscription) =>
                          subscription.key === item.key
                            ? { ...subscription, connected: !subscription.connected }
                            : subscription
                        )
                      )
                    }
                  >
                    {item.connected ? "已连接" : "连接菜单"}
                  </button>
                </div>
              ))}
            </div>
          </section>

          <section className="rounded-[24px] bg-white p-8 shadow-[0_18px_48px_rgba(0,25,68,0.06)]">
            <div className="mb-8 flex items-start justify-between gap-4">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-[rgba(225,124,90,0.1)] text-[#e17c5a]">
                  <FileText className="h-5 w-5" />
                </div>
                <div>
                  <h2 className="font-headline text-[26px] font-bold text-[var(--color-ink)]">面试知识库管理</h2>
                  <p className="text-xs text-slate-400">这里展示已经进入本地 RAG 的真实知识片段</p>
                </div>
              </div>

              <button className="rounded-lg p-2 text-slate-400 transition-colors hover:text-[var(--color-primary)]">
                <CircleHelp className="h-5 w-5" />
              </button>
            </div>

            <div className="rounded-[24px] border-2 border-dashed border-[#d5d7e4] p-12 text-center transition-colors hover:border-[var(--color-primary)] hover:bg-[rgba(0,25,68,0.02)]">
              <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-[var(--color-soft)]">
                <Upload className="h-8 w-8 text-[var(--color-primary)]" />
              </div>
              <div className="mt-4 space-y-1">
                <p className="text-lg font-bold text-[var(--color-primary)]">点击或拖拽文件至此处上传</p>
                <p className="text-sm text-slate-400">上传链路下一步接入；当前右侧列表是已进入知识库的真实数据</p>
              </div>
              <p className="mx-auto mt-4 inline-flex rounded-full bg-[rgba(225,124,90,0.08)] px-3 py-1 text-xs text-[#e17c5a]">
                建议上传：简历、项目复盘、证书、偏好说明
              </p>
            </div>

            <div className="mt-10">
              <div className="mb-4 flex items-center justify-between px-1">
                <h3 className="font-headline text-lg font-bold text-slate-700">
                  已上传文件 ({data.knowledge_files.length})
                </h3>
                <button className="inline-flex items-center gap-2 text-sm font-medium text-[var(--color-primary)] hover:underline">
                  <Plus className="h-4 w-4" />
                  批量导出
                </button>
              </div>

              <div className="space-y-3">
                {data.knowledge_files.length ? (
                  data.knowledge_files.map((file) => (
                    <div
                      key={file.id}
                      className="group flex items-center justify-between rounded-xl p-4 transition-colors hover:bg-[var(--color-soft)]"
                    >
                      <div className="flex items-center gap-4">
                        <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-slate-100 text-[var(--color-primary)]">
                          <FileText className="h-6 w-6" />
                        </div>
                        <div>
                          <p className="text-[15px] font-semibold text-slate-800">{file.title}</p>
                          <p className="mt-1 text-xs text-slate-400">
                            类型：{file.kind} {file.tags.length ? `· 标签：${file.tags.join(", ")}` : ""}
                          </p>
                        </div>
                      </div>

                      <div className="flex items-center gap-2 opacity-0 transition-opacity group-hover:opacity-100">
                        <FileActionButton>
                          <View className="h-4 w-4" />
                        </FileActionButton>
                        <FileActionButton>
                          <Download className="h-4 w-4" />
                        </FileActionButton>
                        <button className="rounded-lg p-2 text-slate-400 transition-colors hover:bg-white hover:text-rose-500">
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="rounded-xl bg-[var(--color-soft)] p-6 text-sm text-slate-500">
                    还没有真实知识文件。先在系统里导入简历或项目资料，这里就会出现。
                  </div>
                )}
              </div>
            </div>
          </section>

          <div className="grid gap-8 md:grid-cols-2">
            <section className="relative overflow-hidden rounded-[24px] bg-[#10357e] p-6 text-white">
              <div className="relative z-10">
                <p className="mb-1 text-xs font-bold uppercase tracking-[0.24em] text-blue-100/70">
                  已用存储空间
                </p>
                <h3 className="font-headline text-[34px] font-black">
                  {data.storage_used_label} <span className="text-sm font-normal opacity-70">/ {data.storage_limit_label}</span>
                </h3>
                <div className="mt-4 h-1.5 w-full overflow-hidden rounded-full bg-white/20">
                  <div
                    className="h-full rounded-full bg-[#6b95f3]"
                    style={{
                      width: `${Math.min(
                        100,
                        (Number(data.storage_used_label || "0") / Number(data.storage_limit_label || "100")) * 100
                      )}%`,
                    }}
                  />
                </div>
              </div>
              <BadgeInfo className="absolute -bottom-3 -right-1 h-20 w-20 text-white/10" />
            </section>

            <section className="flex min-h-[152px] flex-col justify-between rounded-[24px] bg-[#e6e8eb] p-6">
              <div className="flex items-center gap-2 text-[var(--color-primary)]">
                <ShieldCheck className="h-4 w-4" />
                <span className="text-xs font-bold uppercase tracking-[0.24em]">安全状态</span>
              </div>
              <div>
                <h3 className="font-headline text-2xl font-bold text-[var(--color-primary)]">
                  {data.encryption_enabled ? "端到端加密已启用" : "尚未启用加密"}
                </h3>
                <p className="mt-2 text-xs leading-6 text-slate-500">
                  您的 API 配置和知识片段均保存在本地状态文件中
                </p>
              </div>
            </section>
          </div>
        </div>
      </div>
    </div>
  );
}
