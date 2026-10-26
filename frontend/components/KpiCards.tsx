"use client";

import {
  Activity,
  Banknote,
  Target,
  TrendingUp,
  type LucideIcon,
} from "lucide-react";
import type { Bet } from "@/lib/api";
import { Card } from "@/components/ui";
import { fmt } from "@/lib/format";

type Item = {
  label: string;
  value: string;
  icon: LucideIcon;
  accent: string;
  iconCls: string;
  hint?: string;
};

export function KpiCards({ bets }: { bets: Bet[] }) {
  const evs = bets.map((b) => Number(b.ev) || 0);
  const banks = bets.map((b) => Number(b.bank) || 0);
  const avgEv = evs.length ? evs.reduce((a, b) => a + b, 0) / evs.length : 0;
  const maxEv = evs.length ? Math.max(...evs) : 0;
  const totalBank = banks.reduce((a, b) => a + b, 0);

  const items: Item[] = [
    {
      label: "Apuestas +EV",
      value: String(bets.length),
      icon: Target,
      accent: "text-slate-100",
      iconCls: "from-emerald-400/20 to-teal-500/10 text-emerald-300 border-emerald-400/20",
      hint: bets.length ? "candidatas disponibles" : "sin predicciones",
    },
    {
      label: "Mejor apuesta",
      value: `+${fmt(maxEv)}%`,
      icon: TrendingUp,
      accent: "text-emerald-300",
      iconCls: "from-emerald-400/20 to-teal-500/10 text-emerald-300 border-emerald-400/20",
      hint: "máximo EV",
    },
    {
      label: "EV medio",
      value: `+${fmt(avgEv)}%`,
      icon: Activity,
      accent: "text-primary-2",
      iconCls: "from-sky-400/20 to-cyan-500/10 text-sky-300 border-sky-400/20",
      hint: "esperanza del portafolio",
    },
    {
      label: "Bank total",
      value: `${fmt(totalBank)}%`,
      icon: Banknote,
      accent: "text-gold",
      iconCls: "from-amber-400/20 to-orange-500/10 text-amber-300 border-amber-400/20",
      hint: "stake Kelly acumulado",
    },
  ];

  return (
    <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
      {items.map((item, i) => {
        const Icon = item.icon;
        return (
          <Card
            key={item.label}
            className="rise-in group relative overflow-hidden !p-5"
            style={{ animationDelay: `${i * 60}ms` }}
          >
            <div className="flex items-start justify-between">
              <div>
                <span className="text-xs font-medium uppercase tracking-wider text-muted">
                  {item.label}
                </span>
                <div className={`mt-2 text-[26px] font-bold tracking-tight ${item.accent}`}>
                  {item.value}
                </div>
                {item.hint ? (
                  <div className="mt-1 text-[11px] text-muted/70">{item.hint}</div>
                ) : null}
              </div>
              <span
                className={`grid h-10 w-10 place-items-center rounded-xl border bg-gradient-to-br ${item.iconCls}`}
              >
                <Icon className="h-[18px] w-[18px]" />
              </span>
            </div>
            <div className="pointer-events-none absolute -right-6 -top-6 h-20 w-20 rounded-full bg-gradient-to-br from-emerald-400/10 to-transparent blur-xl" />
          </Card>
        );
      })}
    </div>
  );
}