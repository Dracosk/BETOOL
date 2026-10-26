"use client";

import type { Bet } from "@/lib/api";
import { cn } from "@/lib/cn";
import { Badge, Card, EmptyState } from "@/components/ui";

function fmt(v: number | null | undefined, digits = 2): string {
  if (v === null || v === undefined || Number.isNaN(Number(v))) return "—";
  return Number(v).toFixed(digits);
}

function evBadge(ev: number | null | undefined) {
  if (ev === null || ev === undefined) return null;
  if (ev >= 10)
    return (
      <Badge className="border-emerald-500/50 bg-emerald-500/15 text-emerald-300">
        +{fmt(ev)}%
      </Badge>
    );
  if (ev >= 6)
    return (
      <Badge className="border-lime-500/50 bg-lime-500/15 text-lime-300">
        +{fmt(ev)}%
      </Badge>
    );
  return (
    <Badge className="border-sky-500/50 bg-sky-500/15 text-sky-300">
      +{fmt(ev)}%
    </Badge>
  );
}

export function BetsTable({ bets }: { bets: Bet[] }) {
  if (!bets.length) {
    return (
      <EmptyState message="No hay apuestas con este filtro. Ejecuta «Actualizar predicciones» para generar el listado +EV." />
    );
  }

  return (
    <Card className="!p-0 overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full min-w-[760px] text-sm">
          <thead>
            <tr className="border-b border-slate-800 text-left text-xs uppercase tracking-wider text-slate-400">
              <th className="px-4 py-3 font-medium">Fecha</th>
              <th className="px-4 py-3 font-medium">Partido</th>
              <th className="px-4 py-3 font-medium">Mercado</th>
              <th className="px-4 py-3 font-medium">Apuesta</th>
              <th className="px-4 py-3 text-right font-medium">Prob</th>
              <th className="px-4 py-3 text-right font-medium">Cuota</th>
              <th className="px-4 py-3 text-right font-medium">EV</th>
              <th className="px-4 py-3 text-right font-medium">Bank %</th>
            </tr>
          </thead>
          <tbody>
            {bets.map((b, i) => (
              <tr
                key={`${b.game_id ?? ""}-${i}`}
                className={cn(
                  "border-b border-slate-800/60 transition-colors hover:bg-slate-800/40",
                  i % 2 === 1 && "bg-slate-900/30",
                )}
              >
                <td className="px-4 py-3 text-slate-300 whitespace-nowrap">
                  {String(b.game_date ?? "").slice(0, 10)}
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2 font-medium text-slate-100">
                    <span>{b.home ?? "?"}</span>
                    <span className="text-slate-500">vs</span>
                    <span>{b.away ?? "?"}</span>
                  </div>
                </td>
                <td className="px-4 py-3 text-slate-300">{b.market ?? "—"}</td>
                <td className="px-4 py-3">
                  <Badge className="border-slate-700 bg-slate-800/70 text-slate-200">
                    {b.bet_name ?? "—"}
                  </Badge>
                </td>
                <td className="px-4 py-3 text-right tabular-nums text-slate-300">
                  {fmt((b.model_prob ?? 0) * 100, 1)}%
                </td>
                <td className="px-4 py-3 text-right tabular-nums text-amber-300">
                  {fmt(b.odd)}
                </td>
                <td className="px-4 py-3 text-right">{evBadge(b.ev)}</td>
                <td className="px-4 py-3 text-right tabular-nums text-slate-200">
                  {fmt(b.bank)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  );
}