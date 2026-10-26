"use client";

import { CircleDot } from "lucide-react";
import type { Bet } from "@/lib/api";
import { Badge, Card } from "@/components/ui";
import { cn } from "@/lib/cn";
import { dateOnly, evBadgeCls, evBarCls, evTier, fmt, pct } from "@/lib/format";

type Props = {
  bets: Bet[];
};

export function BetsTable({ bets }: Props) {
  return (
    <Card className="rise-in !p-0 overflow-hidden">
      <div className="flex items-center justify-between border-b border-border px-5 py-4">
        <div>
          <h3 className="text-sm font-semibold text-slate-100">Candidatas de valor</h3>
          <p className="text-xs text-muted">{bets.length} apuestas · ordenadas por EV</p>
        </div>
        <Badge className="border-emerald-400/30 bg-emerald-400/5 text-emerald-300">
          <CircleDot className="h-3 w-3" />
          +EV &gt; 0
        </Badge>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full min-w-[860px] border-collapse text-sm">
          <thead>
            <tr className="border-b border-border text-left text-[11px] font-semibold uppercase tracking-widest text-muted">
              <th className="px-5 py-3 font-medium">Fecha</th>
              <th className="px-4 py-3 font-medium">Partido</th>
              <th className="px-4 py-3 font-medium">Mercado</th>
              <th className="px-4 py-3 font-medium">Apuesta</th>
              <th className="px-4 py-3 font-medium">Probabilidad</th>
              <th className="px-4 py-3 text-right font-medium">Cuota</th>
              <th className="px-4 py-3 text-right font-medium">EV</th>
              <th className="px-4 py-3 text-right font-medium">Bank %</th>
            </tr>
          </thead>
          <tbody>
            {bets.map((bet, i) => {
              const tier = evTier(bet.ev);
              const prob = Math.max(0, Math.min(100, (Number(bet.model_prob) || 0) * 100));
              return (
                <tr
                  key={`${bet.game_id ?? ""}-${i}`}
                  className={cn(
                    "group border-b border-border/60 transition-colors hover:bg-surface-2/50",
                    i % 2 === 1 && "bg-surface/40",
                  )}
                >
                  <td className="whitespace-nowrap px-5 py-3.5 text-slate-300">
                    <div className="text-[13px] font-medium">{dateOnly(bet.game_date)}</div>
                    <div className="text-[11px] text-muted">partido</div>
                  </td>

                  <td className="px-4 py-3.5">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-slate-100">{bet.home ?? "—"}</span>
                      <span className="grid h-6 w-6 shrink-0 place-items-center rounded-md border border-border bg-surface-2 text-[10px] font-bold text-muted">
                        VS
                      </span>
                      <span className="font-semibold text-slate-100">{bet.away ?? "—"}</span>
                    </div>
                  </td>

                  <td className="px-4 py-3.5">
                    <span className="text-[13px] text-slate-300">{bet.market ?? "—"}</span>
                  </td>

                  <td className="px-4 py-3.5">
                    <Badge className="border-border bg-surface-2 text-slate-200">
                      {bet.bet_name ?? "—"}
                    </Badge>
                  </td>

                  <td className="px-4 py-3.5">
                    <div className="flex items-center gap-2">
                      <div className="h-1.5 w-20 overflow-hidden rounded-full bg-slate-800">
                        <div
                          className={cn("h-full rounded-full bg-gradient-to-r", evBarCls[tier])}
                          style={{ width: `${prob}%` }}
                        />
                      </div>
                      <span className="w-11 text-right tabular-nums text-slate-300">
                        {pct(bet.model_prob)}
                      </span>
                    </div>
                  </td>

                  <td className="px-4 py-3.5 text-right">
                    <span className="inline-block rounded-lg border border-amber-400/20 bg-amber-400/10 px-2 py-0.5 font-mono font-semibold tabular-nums text-amber-300">
                      {fmt(bet.odd)}
                    </span>
                  </td>

                  <td className="px-4 py-3.5 text-right">
                    <Badge className={cn("font-semibold tabular-nums", evBadgeCls[tier])}>
                      +{fmt(bet.ev)}%
                    </Badge>
                  </td>

                  <td className="px-4 py-3.5 text-right font-mono font-semibold tabular-nums text-slate-200">
                    {fmt(bet.bank)}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </Card>
  );
}