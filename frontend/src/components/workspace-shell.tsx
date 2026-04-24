import Link from "next/link";
import { ReactNode } from "react";
import {
  Bell,
  Bot,
  BriefcaseBusiness,
  CalendarCheck2,
  FileText,
  HelpCircle,
  LayoutDashboard,
  MessageSquareMore,
  Search,
  Settings2,
  SlidersHorizontal,
} from "lucide-react";

const navItems = [
  { href: "/", label: "控制面板", icon: LayoutDashboard },
  { href: "/chat", label: "聊天工作台", icon: MessageSquareMore },
  { href: "/jobs", label: "职位池", icon: BriefcaseBusiness },
  { href: "/ai-config", label: "AI 配置", icon: SlidersHorizontal },
  { href: "/interviews", label: "面试管理", icon: CalendarCheck2 },
  { href: "/resume-lab", label: "简历实验室", icon: FileText },
];

export function WorkspaceShell({
  pathname,
  children,
  searchPlaceholder = "搜索职位、会话或配置项...",
}: {
  pathname: string;
  children: ReactNode;
  searchPlaceholder?: string;
}) {
  return (
    <div className="min-h-screen bg-[var(--color-surface)] text-[var(--color-ink)]">
      <aside className="fixed inset-y-0 left-0 hidden w-72 flex-col bg-[var(--color-primary)] px-5 py-6 text-white lg:flex">
        <div>
          <p className="font-headline text-2xl font-extrabold tracking-tight">Career Curator AI</p>
          <p className="mt-1 text-sm text-blue-200/70">为 BOSS 自动沟通和求职运营而生</p>
        </div>

        <div className="mt-9 rounded-md bg-white/8 p-4">
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-md bg-white/10">
              <Bot className="h-5 w-5" />
            </div>
            <div>
              <p className="font-headline text-lg font-bold">Agent Alpha</p>
              <p className="text-xs uppercase tracking-[0.2em] text-cyan-100/60">在线扫描中</p>
            </div>
          </div>
        </div>

        <nav className="mt-8 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const active = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-3 rounded-md px-4 py-3 text-sm font-medium transition ${
                  active ? "bg-white/12 text-white" : "text-blue-100/64 hover:bg-white/6 hover:text-white"
                }`}
              >
                <Icon className="h-4 w-4" />
                {item.label}
              </Link>
            );
          })}
        </nav>

        <div className="mt-auto space-y-3">
          <Link
            href="/resume-lab"
            className="block w-full rounded-md bg-[var(--color-accent)] px-4 py-3 text-center text-sm font-semibold text-[var(--color-primary)]"
          >
            上传简历
          </Link>
          <div className="rounded-md border border-white/10 px-4 py-4">
            <p className="text-xs uppercase tracking-[0.22em] text-blue-100/60">Support</p>
            <p className="mt-2 text-sm text-blue-50/86">当前处于人工放行模式，自动回复已预留到后端服务层。</p>
          </div>
        </div>
      </aside>

      <div className="lg:pl-72">
        <header className="sticky top-0 z-30 border-b border-black/5 bg-[rgba(247,249,252,0.88)] backdrop-blur">
          <div className="flex items-center justify-between gap-4 px-4 py-4 lg:px-8">
            <div className="flex flex-1 items-center gap-3 rounded-md bg-white px-3 py-2 shadow-panel ring-1 ring-black/4">
              <Search className="h-4 w-4 text-slate-400" />
              <input
                className="w-full bg-transparent text-sm outline-none placeholder:text-slate-400"
                placeholder={searchPlaceholder}
              />
            </div>
            <div className="flex items-center gap-2">
              <button className="rounded-md bg-white p-2 shadow-panel ring-1 ring-black/4">
                <Bell className="h-4 w-4 text-[var(--color-primary)]" />
              </button>
              <button className="rounded-md bg-white p-2 shadow-panel ring-1 ring-black/4">
                <HelpCircle className="h-4 w-4 text-[var(--color-primary)]" />
              </button>
              <button className="rounded-md bg-white p-2 shadow-panel ring-1 ring-black/4">
                <Settings2 className="h-4 w-4 text-[var(--color-primary)]" />
              </button>
              <div className="flex h-10 w-10 items-center justify-center rounded-md bg-[var(--color-primary)] font-headline text-sm font-bold text-white">
                ZY
              </div>
            </div>
          </div>
        </header>
        <main className="px-4 py-5 lg:px-8">{children}</main>
      </div>
    </div>
  );
}
