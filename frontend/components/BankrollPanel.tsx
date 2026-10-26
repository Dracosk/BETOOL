"use client";

import {
  Banknote,
  CheckCircle2,
  CircleDashed,
  MinusCircle,
  XCircle,
} from "lucide-react";
import type { BankrollBet, BankrollResponse } from "@/lib/api";
import { cn } from "@/lib/cn";
import { Badge, Card, EmptyState } from "@/components/ui";
import { BankrollCurve } from "@/components/charts/BankrollCurve";
import { dateOnly, fmt } from "@/lib/format";

type Props = {
  bankroll: BankrollResponse | null;
  onSettle: (bet: BankrollBet, status: string) => Promise<void>;
  settling: { filename: string; index: number } | null;
};

const STATUS_META: Record<string, { label: string; icon: typeof CircleDashed; cls: string; active: string }> = {
  pending: {
    label: "Pendiente",
    icon: CircleDashed,
    cls: "border-border bg-surface-2 text-muted",
    active: "ring-2 ring-slate-400/70",
  },
  won: {
    label: "Ganada",
    icon: CheckCircle2,
    cls: "border-emerald-400/40 bg-emerald-400/10 text-emerald-300",
    active: "ring-2 ring-emerald-400",
  },
  lost: {
    label: "Perdida",
    icon: XCircle,
    cls: "border-red-400/40 bg-red-400/10 text-red-300",
    active: "ring-2 ring-red-400",
  },
  void: {
    label: "Nula",
    icon: MinusCircle,
    cls: "border-amber-400/40 bg-amber-400/10 text-amber-300",
    active: "ring-2 ring-amber-400",
  },
};

export function BankrollPanel({ bankroll, onSettle, settling }: Props) {
  if (!bankroll || !bankroll.bets.length) {
    return (
      <EmptyState
        title="Aún no hay apuestas de papel"
        message="Ejecuta el módulo «Bot» del pipeline para generar el paper_bets CSV y empezar a liquidar tu bankroll."
        icon={<Banknote className="h-6 w-6" />}
      />
    );
  }

  const totals = bankroll.totals;
  const settledPct = totals.bets ? Math.round((totals.settled / totals.bets) * 100) : 0;

  const stats = [
    { label: "Apuestas", value: String(totals.bets), icon: Banknote, tone: "text-slate-100" },
    { label: "Liquidadas", value: `${totals.settled}/${totals.bets}`, icon: CheckCircle2, tone: "text-info" },
    { label: "EV potencial", value: `+${totals.potential_ev.toFixed(1)}%`, icon: CircleDashed, tone: "text-emerald-300" },
    { label: "Bank total", value: `${totals.bank.toFixed(2)}%`, icon: MinusCircle, tone: "text-gold" },
  ];

  return (
    <div className="flex flex-col gap-4">
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        {stats.map((s, i) => {
          const Icon = s.icon;
          return (
            <Card key={s.label} className="rise-in !p-5" style={{ animationDelay: `${i * 60}ms` }}>
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-xs font-medium uppercase tracking-wider text-muted">{s.label}</div>
                  <div className={cn("mt-2 text-2xl font-bold tracking-tight", s.tone)}>{s.value}</div>
                </div>
                <span className="grid h-9 w-9 place-items-center rounded-xl border border-border bg-surface-2 text-slate-400">
                  <Icon className="h-4 w-4" />
                </span>
              </div>
            </Card>
          );
        })}
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <BankrollCurve bankroll={bankroll} />
        <Card className="rise-in">
          <div>
            <h3 className="text-sm font-semibold text-slate-100">Progreso de liquidación</h3>
            <p className="text-xs text-muted">{settledPct}% de las apuestas resueltas</p>
          </div>
          <div className="mt-4 h-56">
            <div className="flex h-3 w-full overflow-hidden rounded-full bg-slate-800">
              {(["won", "lost", "void"] as const).map((st) => {
                const count = bankroll.bets.filter((b) => b.settlement === st).length;
                if (!count) return null;
                const color =
                  st === "won" ? "#34d399" : st === "lost" ? "#fb7185" : "#fbbf24";
                return (
                  <div
                    key={st}
                    style={{ width: `${(count / totals.bets) * 100}%`, background: color }}
                    title={`${STATUS_META[st].label}: ${count}`}
                  />
                );
              })}
            </div>
            <div className="mt-6 flex flex-col gap-3">
              {(["won", "lost", "void"] as const).map((st) => {
                const count = bankroll.bets.filter((b) => b.settlement === st).length;
                const Icon = STATUS_META[st].icon;
                return (
                  <div key={st} className="flex items-center justify-between text-sm">
                    <span className="flex items-center gap-2 text-slate-300">
                      <Icon className={cn("h-4 w-4", STATUS_META[st].cls.split(" ").at(-1))} />
                      {STATUS_META[st].label}
                    </span>
                    <span className="font-mono font-semibold tabular-nums text-slate-100">{count}</span>
                  </div>
                );
              })}
            </div>
          </div>
        </Card>
      </div>

      <Card className="rise-in !p-0 overflow-hidden">
        <div className="flex items-center justify-between border-b border-border px-5 py-4">
          <h3 className="text-sm font-semibold text-slate-100">Apuestas de papel</h3>
          <div className="flex gap-2">
            {bankroll.files.map((f) => (
              <Badge key={f.filename} className="border-border bg-surface-2 text-muted">
                {f.filename}
              </Badge>
            ))}
          </div>
        </div>
        <div className="max-h-[540px] overflow-auto">
          <table className="w-full min-w-[900px] text-sm">
            <thead className="sticky top-0 z-10 bg-surface">
              <tr className="border-b border-border text-left text-[11px] font-semibold uppercase tracking-widest text-muted">
                <th className="px-5 py-3 font-medium">Fecha</th>
                <th className="px-4 py-3 font-medium">Partido</th>
                <th className="px-4 py-3 font-medium">Mercado</th>
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
                      "group border-b border-border/60 transition-colors hover:bg-surface-2/50",
                      i % 2 === 1 && "bg-surface/40",
                    )}
                  >
                    <td className="whitespace-nowrap px-5 py-3.5 text-slate-300">{dateOnly(bet.game_date)}</td>
                    <td className="px-4 py-3.5 font-semibold text-slate-100">
                      {bet.home ?? "?"} <span className="mx-1 text-muted">vs</span> {bet.away ?? "?"}
                    </td>
                    <td className="px-4 py-3.5 text-[13px] text-slate-300">{bet.market ?? "—"}</td>
                    <td className="px-4 py-3.5">
                      <Badge className="border-border bg-surface-2 text-slate-200">{bet.bet_name ?? "—"}</Badge>
                    </td>
                    <td className="px-4 py-3.5 text-right font-mono tabular-nums text-amber-300">
                      {fmt(bet.odd)}
                    </td>
                    <td className="px-4 py-3.5 text-right font-mono tabular-nums text-emerald-300">
                      +{fmt(bet.ev)}%
                    </td>
                    <td className="px-4 py-3.5 text-right font-mono tabular-nums text-slate-200">
                      {fmt(bet.bank)}
                    </td>
                    <td className="px-4 py-3.5">
                      <div className="flex flex-wrap gap-1">
                        {Object.entries(STATUS_META).map(([key, m]) => {
                          const Icon = m.icon;
                          return (
                            <button
                              key={key}
                              disabled={isSettling}
                              onClick={() => onSettle(bet, key)}
                              title={`Marcar como ${m.label.toLowerCase()}`}
                              className={cn(
                                "inline-flex items-center gap-1 rounded-full border px-2.5 py-1 text-xs font-medium transition-all",
                                m.cls,
                                bet.settlement === key && m.active,
                                (isSettling || bet.settlement === key) && "pointer-events-none",
                              )}
                            >
                              <Icon className="h-3 w-3" />
                              {m.label}
                            </button>
                          );
                        })}
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