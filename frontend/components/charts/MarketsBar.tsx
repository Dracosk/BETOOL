"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { StatsResponse } from "@/lib/api";
import { Card, EmptyState } from "@/components/ui";
import { ChartTooltip } from "@/components/charts/ChartTooltip";

const COLORS = ["#34d399", "#38bdf8", "#a78bfa", "#fbbf24", "#fb7185", "#2dd4bf"];

export function MarketsBar({ stats }: { stats: StatsResponse | null }) {
  if (!stats || stats.empty || !stats.by_market.length) {
    return <EmptyState message="Sin datos por mercado todavía." />;
  }
  return (
    <Card className="rise-in">
      <div>
        <h3 className="text-sm font-semibold text-slate-100">Rendimiento por mercado</h3>
        <p className="text-xs text-muted">EV medio de las apuestas de cada mercado</p>
      </div>
      <div className="mt-4 h-64">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={stats.by_market} margin={{ top: 8, right: 8, left: -18, bottom: 40 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1d2740" vertical={false} />
            <XAxis
              dataKey="market"
              tick={{ fill: "#8494b5", fontSize: 10 }}
              interval={0}
              angle={-25}
              textAnchor="end"
              height={52}
              axisLine={{ stroke: "#1d2740" }}
              tickLine={false}
            />
            <YAxis tick={{ fill: "#8494b5", fontSize: 10 }} axisLine={false} tickLine={false} />
            <Tooltip
              cursor={{ fill: "rgba(148,163,184,0.06)" }}
              content={({ active, payload }) => {
                if (!active || !payload?.length) return null;
                const p = payload[0]?.payload as { market: string; count: number; avg_ev: number };
                return (
                  <ChartTooltip
                    label={p.market}
                    items={[{ name: "EV medio", value: `+${p.avg_ev.toFixed(2)}%` }]}
                    extra={[{ label: "Apuestas", value: String(p.count) }]}
                  />
                );
              }}
            />
            <Bar dataKey="avg_ev" name="EV medio" radius={[6, 6, 0, 0]} maxBarSize={52}>
              {stats.by_market.map((entry, i) => (
                <Cell key={entry.market} fill={COLORS[i % COLORS.length]} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
}