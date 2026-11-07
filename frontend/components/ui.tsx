"use client";

import type { ReactNode } from "react";
import { Activity, AlertTriangle, SearchX } from "lucide-react";
import { cn } from "@/lib/cn";

export type Section = "apuestas" | "graficas" | "bankroll" | "pipeline";

export function Card({
  className,
  children,
  style,
}: {
  className?: string;
  children: ReactNode;
  style?: React.CSSProperties;
}) {
  return (
    <div
      style={style}
      className={cn(
        "rounded-2xl border border-border bg-surface/80 shadow-[0_1px_0_0_rgba(255,255,255,0.03)_inset,0_20px_40px_-24px_rgba(0,0,0,0.7)] backdrop-blur",
        className,
      )}
    >
      {children}
    </div>
  );
}

export function Badge({
  className,
  children,
}: {
  className?: string;
  children: ReactNode;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 whitespace-nowrap rounded-full border px-2.5 py-0.5 text-xs font-medium",
        className,
      )}
    >
      {children}
    </span>
  );
}

export function Spinner({ className }: { className?: string }) {
  return (
    <span
      className={cn(
        "inline-block h-4 w-4 animate-spin rounded-full border-2 border-slate-500 border-t-primary-2",
        className,
      )}
      role="status"
      aria-label="Cargando"
    />
  );
}

export function Skeleton({ className }: { className?: string }) {
  return (
    <div
      className={cn(
        "animate-pulse rounded-lg bg-slate-800/60",
        className,
      )}
    />
  );
}

export function SectionTitle({
  title,
  subtitle,
  icon,
}: {
  title: string;
  subtitle?: string;
  icon?: ReactNode;
}) {
  return (
    <div className="flex items-center gap-3">
      {icon ? (
        <span className="grid h-9 w-9 place-items-center rounded-xl border border-border bg-surface-2 text-primary-2">
          {icon}
        </span>
      ) : null}
      <div>
        <h2 className="text-base font-semibold tracking-tight text-slate-100">{title}</h2>
        {subtitle ? <p className="text-sm text-muted">{subtitle}</p> : null}
      </div>
    </div>
  );
}

export function EmptyState({
  title = "Sin datos",
  message,
  icon = <SearchX className="h-6 w-6" />,
  action,
}: {
  title?: string;
  message: string;
  icon?: ReactNode;
  action?: ReactNode;
}) {
  return (
    <Card className="flex flex-col items-center justify-center gap-3 px-6 py-16 text-center">
      <span className="grid h-14 w-14 place-items-center rounded-2xl border border-border bg-surface-2 text-slate-400">
        {icon}
      </span>
      <div>
        <p className="text-sm font-semibold text-slate-200">{title}</p>
        <p className="mx-auto mt-1 max-w-md text-sm leading-relaxed text-muted">{message}</p>
      </div>
      {action ? <div className="mt-1">{action}</div> : null}
    </Card>
  );
}

export function ErrorBanner({
  message,
  onClose,
}: {
  message: string;
  onClose?: () => void;
}) {
  return (
    <div className="flex items-start gap-3 rounded-xl border border-danger/40 bg-danger/10 px-4 py-3 text-sm text-rose-200">
      <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-danger" />
      <div className="flex-1">{message}</div>
      {onClose ? (
        <button onClick={onClose} className="text-rose-300/70 transition-colors hover:text-rose-200">
          ✕
        </button>
      ) : null}
    </div>
  );
}

export function StatusPill({
  label,
  tone,
}: {
  label: string;
  tone: "online" | "offline" | "unknown";
}) {
  const dot =
    tone === "online"
      ? "bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.8)]"
      : tone === "offline"
        ? "bg-red-400"
        : "bg-slate-400";
  return (
    <Badge
      className={cn(
        "border-border bg-surface-2 text-muted",
        tone === "online" && "text-emerald-300",
        tone === "offline" && "text-red-300",
      )}
    >
      <span className={cn("h-1.5 w-1.5 rounded-full", dot)} />
      {label}
    </Badge>
  );
}

export function LoaderPane({ lines = 4 }: { lines?: number }) {
  return (
    <div className="flex flex-col gap-4">
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} className="h-24 rounded-2xl" />
        ))}
      </div>
      {Array.from({ length: lines }).map((_, i) => (
        <Skeleton key={i} className="h-14 rounded-xl" />
      ))}
      <div className="mt-2 flex items-center justify-center gap-2 py-8 text-sm text-muted">
        <Activity className="h-4 w-4 animate-pulse text-primary-2" />
        Cargando datos de la API…
      </div>
    </div>
  );
}