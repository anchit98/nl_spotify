import type { ReactNode } from "react";

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen flex bg-background text-on-surface">
      {children}
    </div>
  );
}

export function PageHeader({
  title,
  subtitle,
  meta,
  actions,
}: {
  title: string;
  subtitle?: string;
  meta?: ReactNode;
  actions?: ReactNode;
}) {
  return (
    <header className="mb-10 flex flex-col md:flex-row md:items-end justify-between gap-6">
      <div>
        <div className="flex items-center gap-3 mb-2">
          <h1 className="text-[24px] md:text-[32px] font-semibold tracking-tight text-on-surface">
            {title}
          </h1>
          <span className="px-2 py-1 rounded bg-surface-high border border-border-subtle text-[12px] font-semibold uppercase tracking-wider text-text-muted flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-primary-container animate-pulse" />
            Live
          </span>
        </div>
        {subtitle && (
          <p className="text-[18px] font-medium leading-relaxed text-on-surface-variant max-w-2xl">
            {subtitle}
          </p>
        )}
        {meta && <div className="flex items-center gap-4 mt-4 text-[13px] text-text-muted">{meta}</div>}
      </div>
      {actions && <div className="flex items-center gap-3 shrink-0">{actions}</div>}
    </header>
  );
}

export function GlassCard({
  children,
  className = "",
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <div className={`glass-panel rounded-xl ${className}`}>{children}</div>
  );
}

export function EmptyState({
  icon,
  title,
  description,
  action,
}: {
  icon: string;
  title: string;
  description: string;
  action?: ReactNode;
}) {
  return (
    <div className="glass-panel rounded-xl p-12 text-center max-w-lg mx-auto">
      <span className="material-symbols-outlined text-5xl text-text-muted mb-4 block">{icon}</span>
      <h2 className="text-[20px] font-semibold mb-2">{title}</h2>
      <p className="text-[15px] text-on-surface-variant mb-6">{description}</p>
      {action}
    </div>
  );
}

export function AuditFooter({ runId, model }: { runId?: string; model?: string }) {
  if (!runId) return null;
  return (
    <footer className="mt-12 pt-4 border-t border-border-subtle text-[12px] text-text-muted flex flex-wrap gap-4">
      <span>Run ID: {runId.slice(0, 8)}…</span>
      {model && <span>Model: {model}</span>}
    </footer>
  );
}
