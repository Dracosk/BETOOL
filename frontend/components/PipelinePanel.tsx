"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import {
  Bot,
  CalendarDays,
  ClipboardCheck,
  Percent,
  Play,
  RefreshCcw,
  TerminalSquare,
  Trophy,
  UsersRound,
  type LucideIcon,
} from "lucide-react";
import type { PipelineLogs, Scope } from "@/lib/api";
import { cn } from "@/lib/cn";
import { Badge, Card, Spinner } from "@/components/ui";

const MODULES: {
  key: string;
  label: string;
  desc: string;
  icon: LucideIcon;
  tone: string;
}[] = [
  {
    key: "fixtures",
    label: "Fixtures",
    desc: "Calendario de partidos",
    icon: CalendarDays,
    tone: "from-sky-400/20 to-cyan-500/10 text-sky-300 border-sky-400/20",
  },
  {
    key: "results",
    label: "Results",
    desc: "Resultados finales",
    icon: ClipboardCheck,
    tone: "from-violet-400/20 to-fuchsia-500/10 text-violet-300 border-violet-400/20",
  },
  {
    key: "odds",
    label: "Odds",
    desc: "Cuotas limpadas",
    icon: Percent,
    tone: "from-amber-400/20 to-orange-500/10 text-amber-300 border-amber-400/20",
  },
  {
    key: "leagues",
    label: "Leagues",
    desc: "Ligas y competiciones",
    icon: Trophy,
    tone: "from-emerald-400/20 to-teal-500/10 text-emerald-300 border-emerald-400/20",
  },
  {
    key: "teams",
    label: "Teams",
    desc: "Equipos y plantillas",
    icon: UsersRound,
    tone: "from-rose-400/20 to-pink-500/10 text-rose-300 border-rose-400/20",
  },
  {
    key: "daily",
    label: "Daily",
    desc: "Cadena diaria completa",
    icon: RefreshCcw,
    tone: "from-indigo-400/20 to-blue-500/10 text-indigo-300 border-indigo-400/20",
  },
  {
    key: "bot",
    label: "Bot",
    desc: "Generar apuestas de valor",
    icon: Bot,
    tone: "from-emerald-400/25 to-teal-600/15 text-emerald-300 border-emerald-400/30",
  },
];

type Props = {
  logs: PipelineLogs | null;
  onStart: (module: string, scope: Scope) => Promise<void>;
};

const SCOPES: { key: Scope; label: string }[] = [
  { key: "all", label: "Todas" },
  { key: "3d", label: "3 días" },
  { key: "today", label: "Hoy" },
];

function LogLine({ line }: { line: string }) {
  const cls = useMemo(() => {
    const lower = line.toLowerCase();
    if (line.startsWith("$ ")) return "text-sky-300";
    if (lower.includes("[backend]")) return "text-slate-500 italic";
    if (/error|fail|traceback|exception/i.test(lower)) return "text-rose-400";
    if (/✓|✔|complet|done|ok\b|success/i.test(lower)) return "text-emerald-400";
    if (lower.includes("warning")) return "text-amber-400";
    return "text-slate-300";
  }, [line]);

  return (
    <div className={cn("whitespace-pre-wrap break-words leading-relaxed", cls)}>
      {line || "\u00A0"}
    </div>
  );
}

export function PipelinePanel({ logs, onStart }: Props) {
  const [scope, setScope] = useState<Scope>("all");
  const [starting, setStarting] = useState<string | null>(null);
  const preRef = useRef<HTMLDivElement>(null);

  const running = logs?.status?.running ?? null;
  const status = logs?.status?.status ?? "idle";
  const error = logs?.status?.error ?? null;

  const lines = useMemo(() => (logs?.logs ?? []).join("\n").split("\n"), [logs]);

  useEffect(() => {
    const el = preRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [lines.length]);

  async function handleStart(module: string) {
    setStarting(module);
    try {
      await onStart(module, scope);
    } finally {
      setStarting(null);
    }
  }

  return (
    <div className="grid gap-4 lg:grid-cols-[340px_1fr]">
      <Card className="flex flex-col gap-4 !p-5">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-sm font-semibold text-slate-100">Módulos del pipeline</h3>
            <p className="text-xs text-muted">una tarea en ejecución cada vez</p>
          </div>
          {running ? (
            <Badge className="border-emerald-400/40 bg-emerald-400/10 text-emerald-300">
              <Spinner className="!h-3 !w-3" /> {running}
            </Badge>
          ) : status === "error" ? (
            <Badge className="border-red-400/40 bg-red-400/10 text-red-300">Error</Badge>
          ) : status === "done" ? (
            <Badge className="border-emerald-400/40 bg-emerald-400/10 text-emerald-300">
              Completado
            </Badge>
          ) : (
            <Badge className="border-border bg-surface-2 text-muted">Inactivo</Badge>
          )}
        </div>

        <div className="flex flex-col gap-2">
          {MODULES.map((m) => {
            const Icon = m.icon;
            const isRunning = running === m.key;
            const isStarting = starting === m.key;
            return (
              <button
                key={m.key}
                onClick={() => handleStart(m.key)}
                disabled={Boolean(running) || isStarting}
                className={cn(
                  "group flex items-center gap-3 rounded-xl border border-border bg-surface-2/60 px-3 py-2.5 text-left transition-all",
                  "hover:border-emerald-400/40 hover:bg-surface-2",
                  "disabled:cursor-not-allowed disabled:opacity-50",
                  isRunning && "border-emerald-400/50 bg-emerald-400/5",
                )}
              >
                <span
                  className={cn(
                    "grid h-9 w-9 shrink-0 place-items-center rounded-lg border bg-gradient-to-br",
                    m.tone,
                  )}
                >
                  {isRunning || isStarting ? (
                    <Spinner className="!h-4 !w-4" />
                  ) : (
                    <Icon className="h-4 w-4" />
                  )}
                </span>
                <span className="min-w-0 flex-1">
                  <span className="block text-sm font-semibold text-slate-100">{m.label}</span>
                  <span className="block truncate text-[11px] text-muted">{m.desc}</span>
                </span>
                {!isRunning && !isStarting ? (
                  <Play className="h-3.5 w-3.5 text-muted transition-colors group-hover:text-emerald-300" />
                ) : null}
              </button>
            );
          })}
        </div>

        <div className="rounded-xl border border-border bg-surface-2/50 p-3">
          <div className="mb-2 flex items-center justify-between">
            <span className="text-[11px] font-semibold uppercase tracking-widest text-muted">
              Alcance del bot
            </span>
            <Bot className="h-3.5 w-3.5 text-muted" />
          </div>
          <div className="flex gap-1 rounded-lg border border-border bg-surface p-1">
            {SCOPES.map((s) => (
              <button
                key={s.key}
                onClick={() => setScope(s.key)}
                disabled={Boolean(running)}
                className={cn(
                  "flex-1 rounded-md px-2 py-1.5 text-xs font-semibold transition-all disabled:opacity-60",
                  scope === s.key
                    ? "bg-gradient-to-b from-emerald-400 to-emerald-500 text-emerald-950"
                    : "text-muted hover:text-slate-100",
                )}
              >
                {s.label}
              </button>
            ))}
          </div>
        </div>
      </Card>

      <Card className="!p-0 flex min-h-[420px] flex-col overflow-hidden">
        <div className="flex items-center justify-between border-b border-border bg-surface-2/40 px-4 py-3">
          <h3 className="flex items-center gap-2 text-sm font-semibold text-slate-100">
            <TerminalSquare className="h-4 w-4 text-primary-2" />
            Log en vivo
          </h3>
          <span
            className={cn(
              "rounded-full px-2.5 py-0.5 text-[11px] font-medium",
              running
                ? "bg-emerald-400/10 text-emerald-300"
                : status === "error"
                  ? "bg-red-400/10 text-red-300"
                  : status === "done"
                    ? "bg-emerald-400/10 text-emerald-300"
                    : "bg-surface-2 text-muted",
            )}
          >
            {running ? "ejecutando…" : status === "error" ? "falló" : status === "done" ? "completado" : "esperando"}
          </span>
        </div>

        {error ? (
          <div className="flex items-center gap-2 border-b border-red-400/30 bg-red-400/10 px-4 py-2.5 text-sm text-red-300">
            <span className="font-bold">✕</span> {error}
          </div>
        ) : null}

        <div
          ref={preRef}
          className="grid-overlay h-[420px] flex-1 overflow-auto bg-[#04070d]/80 px-4 py-3 font-mono text-xs"
        >
          {lines.length ? (
            <div className="flex flex-col gap-0.5">
              {lines.map((line, i) => (
                <LogLine key={i} line={line} />
              ))}
            </div>
          ) : (
            <div className="flex h-full items-center justify-center text-center text-xs text-muted">
              Sin logs todavía — pulsa un módulo para arrancar la ingesta.
            </div>
          )}
        </div>

        <div className="flex items-center gap-3 border-t border-border bg-surface-2/30 px-4 py-2 text-[11px] text-muted">
          <span className="flex items-center gap-1.5">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" /> en línea
          </span>
          <span className="flex items-center gap-1.5">
            <span className="h-1.5 w-1.5 rounded-full bg-sky-400" /> comando
          </span>
          <span className="flex items-center gap-1.5">
            <span className="h-1.5 w-1.5 rounded-full bg-rose-400" /> error
          </span>
          <span className="ml-auto hidden sm:inline">puerto 8000 · FastAPI</span>
        </div>
      </Card>
    </div>
  );
}