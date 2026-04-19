import { ReactNode } from "react";

export function PageIntro({
  eyebrow,
  title,
  subtitle,
  aside,
}: {
  eyebrow: string;
  title: string;
  subtitle: string;
  aside?: ReactNode;
}) {
  return (
    <section className="grid gap-4 rounded-md bg-[linear-gradient(135deg,rgba(0,25,68,0.96),rgba(7,40,102,0.9))] px-6 py-6 text-white lg:grid-cols-[1.2fr_0.8fr]">
      <div>
        <p className="text-xs uppercase tracking-[0.26em] text-cyan-100/72">{eyebrow}</p>
        <h1 className="mt-3 font-headline text-4xl font-extrabold tracking-tight">{title}</h1>
        <p className="mt-3 max-w-2xl text-sm leading-7 text-blue-100/78">{subtitle}</p>
      </div>
      {aside ? <div className="lg:justify-self-end">{aside}</div> : null}
    </section>
  );
}

export function StatCard({
  label,
  value,
  hint,
}: {
  label: string;
  value: string;
  hint: string;
}) {
  return (
    <div className="rounded-md bg-[var(--color-panel)] p-5 shadow-panel ring-1 ring-black/4">
      <p className="text-xs uppercase tracking-[0.2em] text-[var(--color-muted)]">{label}</p>
      <p className="mt-3 font-headline text-3xl font-extrabold tracking-tight text-[var(--color-ink)]">
        {value}
      </p>
      <p className="mt-2 text-sm text-[var(--color-muted)]">{hint}</p>
    </div>
  );
}

export function Surface({
  children,
  className = "",
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <section
      className={`rounded-md bg-[var(--color-panel)] p-5 shadow-panel ring-1 ring-black/4 ${className}`}
    >
      {children}
    </section>
  );
}

export function SectionTitle({
  title,
  subtitle,
  action,
}: {
  title: string;
  subtitle?: string;
  action?: ReactNode;
}) {
  return (
    <div className="flex flex-wrap items-end justify-between gap-4">
      <div>
        <h2 className="font-headline text-2xl font-extrabold tracking-tight text-[var(--color-ink)]">
          {title}
        </h2>
        {subtitle ? <p className="mt-1 text-sm text-[var(--color-muted)]">{subtitle}</p> : null}
      </div>
      {action}
    </div>
  );
}

export function Pill({
  children,
  tone = "default",
}: {
  children: ReactNode;
  tone?: "default" | "strong" | "soft";
}) {
  const styles = {
    default: "bg-[var(--color-soft)] text-[var(--color-ink)]",
    strong: "bg-[var(--color-primary)] text-white",
    soft: "bg-cyan-50 text-cyan-900",
  }[tone];

  return <span className={`inline-flex rounded-md px-2 py-1 text-xs font-medium ${styles}`}>{children}</span>;
}

export function Toggle({ enabled }: { enabled: boolean }) {
  return (
    <span
      className={`relative inline-flex h-6 w-11 items-center rounded-full transition ${
        enabled ? "bg-[var(--color-primary)]" : "bg-slate-300"
      }`}
    >
      <span
        className={`inline-block h-4 w-4 rounded-full bg-white transition ${
          enabled ? "translate-x-6" : "translate-x-1"
        }`}
      />
    </span>
  );
}
