"use client";

import { useEffect, useRef, useState } from "react";
import type { PipelineLogs, Scope } from "@/lib/api";
import { cn } from "@/lib/cn";
import { Badge, Card, Spinner } from "@/components/ui";

const MODULES = [
  { key: "fixtures", label: "Fixtures", desc: "Calendario" },
  { key: "results", label: "Results", desc: "Resultados" },
  { key: "odds", label: "Odds", desc: "Cuotas" },
  { key: "leagues", label: "Leagues", desc: "Ligas" },
  { key: "teams", label: "Teams", desc: "Equipos" },
  { key: "daily", label: "Daily", desc: "Cadena diaria" },
  { key: "bot", label: "Bot", desc: "Generar apuestas" },
] as const;

type Props = {
  logs: PipelineLogs | null;
  onStart: (module: string, scope: Scope) => Promise<void>;
};

export function PipelinePanel({ logs, onStart }: Props) {
  const [scope, setScope] = useState<Scope>("all");
  const [starting, setStarting] = useState<string | null>(null);
  const preRef = useRef<HTMLPreElement>(null);

  const running = logs?.status?.running ?? null;
  const status = logs?.status?.status ?? "idle";
  const error = logs?.status?.error ?? null;

  useEffect(() => {
    const el = preRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [logs?.logs.length]);

  async function handleStart(module: string) {
    setStarting(module);
    try {
      await onStart(module, scope);
    } finally {
      setStarting(null);
    }
  }

  return (
    <div className="grid gap-4 lg:grid-cols-[320px_1fr]">
      <Card className="flex flex-col gap-3">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold text-slate-200">Módulos del pipeline</h3>
          {running ? (
            <Badge className="border-emerald-500/50 bg-emerald-500/10 text-emerald-300">
              <Spinner className="!h-3 !w-3" /> {running}
            </Badge>
          ) : status === "error" ? (
            <Badge className="border-red-500/50 bg-red-500/10 text-red-300">Error</Badge>
          ) : (
            <Badge className="border-slate-700 bg-slate-800 text-slate-300">Inactivo</Badge>
          )}
        </div>

        {starting === "bot" && (
          <div className="flex items-center gap-2 rounded-lg border border-slate-800 bg-slate-900 p-2">
            <span className="text-xs text-slate-400">Alcance del bot:</span>
            {(["all", "3d", "today"] as Scope[]).map((s) => (
              <button
                key={s}
                onClick={() => setScope(s)}
                className={cn(
                  "rounded px-2 py-1 text-xs font-medium",
                  scope === s
                    ? "bg-emerald-500 text-emerald-950"
                    : "text-slate-300 hover:text-white",
                )}
              >
                {s === "all" ? "Todas" : s === "3d" ? "3 días" : "Hoy"}
              </button>
            ))}
          </div>
        )}

        <div className="grid grid-cols-1 gap-2">
          {MODULES.map((m) => (
            <button
              key={m.key}
              onClick={() => handleStart(m.key)}
              disabled={Boolean(running) || starting === m.key}
              className={cn(
                "flex items-center justify-between rounded-lg border border-slate-800 bg-slate-900 px-3 py-2 text-left transition-colors",
                "hover:border-emerald-500/50 hover:bg-slate-800",
                "disabled:cursor-not-allowed disabled:opacity-50",
              )}
            >
              <div>
                <div className="text-sm font-medium text-slate-100">{m.label}</div>
                <div className="text-xs text-slate-500">{m.desc}</div>
              </div>
              {starting === m.key ? <Spinner /> : <span className="text-emerald-400">▶</span>}
            </button>
          ))}
        </div>
      </Card>

      <Card className="!p-0 flex flex-col overflow-hidden">
        <div className="flex items-center justify-between border-b border-slate-800 px-4 py-3">
          <h3 className="text-sm font-semibold text-slate-200">Log en vivo</h3>
          <span className="text-xs text-slate-500">
            {running ? "ejecutando…" : status === "error" ? "falló" : status === "done" ? "completado" : "esperando"}
          </span>
        </div>
        {error ? (
          <div className="border-b border-red-500/30 bg-red-500/10 px-4 py-2 text-sm text-red-300">
            ⚠ {error}
          </div>
        ) : null}
        <pre
          ref={preRef}
          className="h-[420px] flex-1 overflow-auto whitespace-pre-wrap break-words bg-black/40 px-4 py-3 font-mono text-xs leading-relaxed text-slate-300"
        >
          {logs && logs.logs.length ? logs.logs.join("\n") : "(sin logs todavía — pulsa un módulo)"}
        </pre>
      </Card>
    </div>
  );
}