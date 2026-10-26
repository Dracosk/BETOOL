"use client";

import type { BankrollResponse, BankrollBet } from "@/lib/api";
import { cn } from "@/lib/cn";
import { Badge, Card, EmptyState } from "@/components/ui";
import { BankrollCurve } from "@/components/charts/BankrollCurve";

type Props = {
  bankroll: BankrollResponse | null;
  onSettle: (bet: BankrollBet, status: string) => Promise<void>;
  settling: { filename: string; index: number } | null;
};

const STATUS_META: Record<string, { label: string; cls: string; active: string }> = {
  pending: { label: "Pendiente", cls: "border-slate-700 bg-slate-800 text-slate-300", active: "ring-2 ring-slate-400" },
  won: { label: "Ganada", cls: "border-emerald-500/50 bg-emerald-500/15 text-emerald-300", active: "ring-2 ring-emerald-400" },
  lost: { label: "Perdida", cls: "border-red-500/50 bg-red-500/15 text-red-300", active: "ring-2 ring-red-400" },
  void: { label: "Nula", cls: "border-amber-500/50 bg-amber-500/15 text-amber-300", active: "ring-2 ring-amber-400" },
};

export function BankrollPanel({ bankroll, onSettle, settling }: Props) {
  if (!bankroll || !bankroll.bets.length) {
    return (
      <EmptyState message="Aún no hay paper_bets*.csv. Ejecuta el «Bot» para generar tus apuestas de papel." />
    );
  }

  const totals = bankroll.totals;

  return (
    <div className="flex flex-col gap-4">
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <Card className="!p-4">
          <div className="text-xs uppercase tracking-wider text-slate-400">Apuestas</div>
          <div className="mt-1 text-2xl font-bold text-slate-100">{totals.bets}</div>
        </Card>
        <Card className="!p-4">
          <div className="text-xs uppercase tracking-wider text-slate-400">Liquidadas</div>
          <div className="mt-1 text-2xl font-bold text-sky-300">
            {totals.settled}
            <span className="ml-1 text-sm font-normal text-slate-500">/{totals.bets}</span>
          </div>
        </Card>
        <Card className="!p-4">
          <div className="text-xs uppercase tracking-wider text-slate-400">EV potencial</div>
          <div className="mt-1 text-2xl font-bold text-emerald-400">+{totals.potential_ev.toFixed(1)}%</div>
        </Card>
        <Card className="!p-4">
          <div className="text-xs uppercase tracking-wider text-slate-400">Bank total (%)</div>
          <div className="mt-1 text-2xl font-bold text-slate-100">{totals.bank.toFixed(2)}</div>
        </Card>
      </div>

      <BankrollCurve bankroll={bankroll} />

      <Card className="!p-0 overflow-hidden">
        <div className="border-b border-slate-800 px-4 py-3 text-sm font-semibold text-slate-200">
          Apuestas de papel ({bankroll.files.map((f) => f.filename).join(", ")})
        </div>
        <div className="max-h-[520px] overflow-auto">
          <table className="w-full min-w-[860px] text-sm">
            <thead className="sticky top-0 bg-slate-900">
              <tr className="border-b border-slate-800 text-left text-xs uppercase tracking-wider text-slate-400">
                <th className="px-4 py-3 font-medium">Fecha</th>
                <th className="px-4 py-3 font-medium">Partido</th>
                <th className="px-4 py-3 font-medium">Apuesta</th>
                <th className="px-4 py-3 text-right font-medium">Cuota</th>
                <th className="px-4 py-3 text-right font-medium">EV</th>
                <th className="px-4 py-3 text-right font-medium">Bank %</th>
                <th className="px-4 py-3 font-medium">Liquidación</th>
              </tr>
            </thead>
            <tbody>
              {bankroll.bets.map((bet, i) => {
                const isSettling =
                  settling?.filename === bet.filename && settling?.index === bet.index;
                return (
                  <tr
                    key={`${bet.filename}-${bet.index}`}
                    className={cn(
                      "border-b border-slate-800/60",
                      i % 2 === 1 && "bg-slate-900/30",
                    )}
                  >
                    <td className="px-4 py-3 text-slate-300 whitespace-nowrap">
                      {String(bet.game_date ?? "").slice(0, 10)}
                    </td>
                    <td className="px-4 py-3 font-medium text-slate-100">
                      {bet.home ?? "?"} <span className="text-slate-500">vs</span> {bet.away ?? "?"}
                    </td>
                    <td className="px-4 py-3">
                      <span className="text-slate-300">{bet.market ?? "—"}</span>{" "}
                      <Badge className="border-slate-700 bg-slate-800 text-slate-300">
                        {bet.bet_name ?? "—"}
                      </Badge>
                    </td>
                    <td className="px-4 py-3 text-right tabular-nums text-amber-300">
                      {bet.odd?.toFixed(2) ?? "—"}
                    </td>
                    <td className="px-4 py-3 text-right tabular-nums text-emerald-400">
                      +{bet.ev?.toFixed(2) ?? "—"}%
                    </td>
                    <td className="px-4 py-3 text-right tabular-nums text-slate-200">
                      {bet.bank?.toFixed(2) ?? "—"}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex flex-wrap gap-1">
                        {Object.entries(STATUS_META).map(([key, m]) => (
                          <button
                            key={key}
                            disabled={isSettling}
                            onClick={() => onSettle(bet, key)}
                            className={cn(
                              "rounded-full border px-2 py-0.5 text-xs font-medium transition-all",
                              m.cls,
                              bet.settlement === key && m.active,
                              isSettling && "opacity-50",
                            )}
                          >
                            {m.label}
                          </button>
                        ))}
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}