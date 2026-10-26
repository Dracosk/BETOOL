"use client";

import { useMemo } from "react";
import { Filter, RefreshCw } from "lucide-react";
import type { Bet, Scope } from "@/lib/api";
import { cn } from "@/lib/cn";
import { Spinner } from "@/components/ui";
import { dateOnly } from "@/lib/format";

type Props = {
  scope: Scope;
  setScope: (s: Scope) => void;
  market: string;
  setMarket: (m: string) => void;
  bets: Bet[];
  onRefresh: () => void;
  refreshing: boolean;
  updatedAt: number | null;
  disabled?: boolean;
};

const SCOPES: { key: Scope; label: string; hint: string }[] = [
  { key: "all", label: "Todas", hint: "todas las candidatas" },
  { key: "3d", label: "Próximos 3 días", hint: "hoy + 3 días" },
  { key: "today", label: "Hoy", hint: "solo hoy" },
];

export function FilterBar({
  scope,
  setScope,
  market,
  setMarket,
  bets,
  onRefresh,
  refreshing,
  updatedAt,
  disabled = false,
}: Props) {
  const availableMarkets = useMemo(
    () => Array.from(new Set((bets ?? []).map((b) => b.market ?? "otros"))).sort(),
    [bets],
  );

  const current = SCOPES.find((s) => s.key === scope);

  return (
    <div className="flex flex-wrap items-center justify-between gap-3">
      <div className="flex flex-wrap items-center gap-3">
        <div className="flex items-center gap-1 rounded-xl border border-border bg-surface p-1">
          {SCOPES.map((s) => (
            <button
              key={s.key}
              onClick={() => setScope(s.key)}
              title={s.hint}
              className={cn(
                "rounded-lg px-3.5 py-1.5 text-sm font-semibold transition-all",
                scope === s.key
                  ? "bg-gradient-to-b from-emerald-400 to-emerald-500 text-emerald-950 shadow-[0_4px_14px_-4px_rgba(16,185,129,0.7)]"
                  : "text-muted hover:text-slate-100",
              )}
            >
              {s.label}
            </button>
          ))}
        </div>

        <label className="relative inline-flex items-center">
          <Filter className="pointer-events-none absolute left-3 h-3.5 w-3.5 text-muted" />
          <select
            value={market}
            onChange={(e) => setMarket(e.target.value)}
            className="cursor-pointer appearance-none rounded-xl border border-border bg-surface py-2 pl-9 pr-8 text-sm font-medium text-slate-200 outline-none transition-colors focus:border-emerald-400/50"
          >
            <option value="">Todos los mercados</option>
            {availableMarkets.map((m) => (
              <option key={m} value={m}>
                {m}
              </option>
            ))}
          </select>
          <span className="pointer-events-none absolute right-3 text-xs text-muted">▾</span>
        </label>
      </div>

      <div className="flex items-center gap-3 text-xs text-muted">
        {updatedAt ? (
          <span className="hidden sm:inline">
            Última actualización · {dateOnly(new Date(updatedAt * 1000).toISOString())} —
            {new Date(updatedAt * 1000).toLocaleTimeString("es-ES", {
              hour: "2-digit",
              minute: "2-digit",
            })}
          </span>
        ) : null}
        <button
          onClick={onRefresh}
          disabled={refreshing || disabled}
          className="inline-flex items-center gap-2 rounded-xl border border-border bg-surface px-4 py-2 text-sm font-semibold text-slate-200 transition-all hover:border-emerald-400/40 hover:text-emerald-300 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {refreshing ? <Spinner className="!h-3.5 !w-3.5" /> : <RefreshCw className="h-3.5 w-3.5" />}
          {refreshing ? "Calculando…" : "Recalcular predicciones"}
        </button>
        <span className="hidden capitalize lg:inline">{current?.hint}</span>
      </div>
    </div>
  );
}