"use client";

import { useMemo } from "react";
import type { Bet, Scope } from "@/lib/api";
import { cn } from "@/lib/cn";
import { Spinner } from "@/components/ui";

type Props = {
  scope: Scope;
  setScope: (s: Scope) => void;
  market: string;
  setMarket: (m: string) => void;
  bets: Bet[];
  onRefresh: () => void;
  refreshing: boolean;
  updatedAt: number | null;
};

const SCOPES: { key: Scope; label: string }[] = [
  { key: "all", label: "Todas" },
  { key: "3d", label: "Próximos 3 días" },
  { key: "today", label: "Hoy" },
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
}: Props) {
  const availableMarkets = useMemo(
    () => Array.from(new Set((bets ?? []).map((b) => b.market ?? "otros"))).sort(),
    [bets],
  );

  return (
    <div className="flex flex-wrap items-center justify-between gap-3">
      <div className="flex flex-wrap items-center gap-2">
        <div className="flex rounded-lg border border-slate-800 bg-slate-900 p-1">
          {SCOPES.map((s) => (
            <button
              key={s.key}
              onClick={() => setScope(s.key)}
              className={cn(
                "rounded-md px-3 py-1.5 text-sm font-medium transition-colors",
                scope === s.key
                  ? "bg-emerald-500 text-emerald-950"
                  : "text-slate-300 hover:text-white",
              )}
            >
              {s.label}
            </button>
          ))}
        </div>

        <select
          value={market}
          onChange={(e) => setMarket(e.target.value)}
          className="rounded-lg border border-slate-800 bg-slate-900 px-3 py-2 text-sm text-slate-200 outline-none focus:border-emerald-500"
        >
          <option value="">Todos los mercados</option>
          {availableMarkets.map((m) => (
            <option key={m} value={m}>
              {m}
            </option>
          ))}
        </select>
      </div>

      <div className="flex items-center gap-3">
        {updatedAt ? (
          <span className="text-xs text-slate-500">
            Actualizado: {new Date(updatedAt * 1000).toLocaleString("es-ES")}
          </span>
        ) : null}
        <button
          onClick={onRefresh}
          disabled={refreshing}
          className="flex items-center gap-2 rounded-lg bg-emerald-500 px-4 py-2 text-sm font-semibold text-emerald-950 transition-colors hover:bg-emerald-400 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {refreshing ? <Spinner className="!h-3.5 !w-3.5" /> : <span>⟳</span>}
          {refreshing ? "Actualizando…" : "Actualizar predicciones"}
        </button>
      </div>
    </div>
  );
}