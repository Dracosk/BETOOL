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

const COLORS = ["#22c55e", "#38bdf8", "#a78bfa", "#f59e0b", "#f472b6", "#34d399"];

export function MarketsBar({ stats }: { stats: StatsResponse | null }) {
  if (!stats || stats.empty || !stats.by_market.length) {
    return <EmptyState message="Sin datos por mercado todavía." />;
  }
  return (
    <Card>
      <h3 className="mb-4 text-sm font-semibold text-slate-200">
        Apuestas por mercado (EV medio)
      </h3>
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={stats.by_market} margin={{ top: 4, right: 8, left: -20, bottom: 24 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
            <XAxis
              dataKey="market"
              tick={{ fill: "#94a3b8", fontSize: 10 }}
              interval={0}
              angle={-22}
              textAnchor="end"
            />
            <YAxis tick={{ fill: "#94a3b8", fontSize: 11 }} />
            <Tooltip
              contentStyle={{
                background: "#0f172a",
                border: "1px solid #334155",
                borderRadius: 10,
                fontSize: 12,
              }}
              formatter={(value) => [`${Number(value).toFixed(2)}%`, "EV medio"]}
            />
            <Bar dataKey="avg_ev" radius={[6, 6, 0, 0]}>
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