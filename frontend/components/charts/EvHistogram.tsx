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

export function EvHistogram({ stats }: { stats: StatsResponse | null }) {
  if (!stats || stats.empty) {
    return <EmptyState message="Sin datos de EV todavía." />;
  }
  const data = stats.ev_histogram;
  return (
    <Card>
      <h3 className="mb-4 text-sm font-semibold text-slate-200">
        Distribución de EV (apuestas)
      </h3>
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
            <XAxis dataKey="label" tick={{ fill: "#94a3b8", fontSize: 11 }} interval={1} />
            <YAxis allowDecimals={false} tick={{ fill: "#94a3b8", fontSize: 11 }} />
            <Tooltip
              cursor={{ fill: "rgba(148,163,184,0.08)" }}
              contentStyle={{
                background: "#0f172a",
                border: "1px solid #334155",
                borderRadius: 10,
                fontSize: 12,
              }}
            />
            <Bar dataKey="count" radius={[6, 6, 0, 0]}>
              {data.map((entry) => (
                <Cell
                  key={entry.label}
                  fill={entry.label.startsWith(">") ? "#22c55e" : "#38bdf8"}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
}