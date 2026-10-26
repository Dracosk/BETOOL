"use client";

import {
  CartesianGrid,
  Cell,
  ReferenceLine,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { StatsResponse } from "@/lib/api";
import { Card, EmptyState } from "@/components/ui";

function evColor(ev: number | null | undefined): string {
  if (ev === null || ev === undefined) return "#64748b";
  if (ev >= 10) return "#22c55e";
  if (ev >= 6) return "#84cc16";
  return "#38bdf8";
}

export function ScatterEvOdd({ stats }: { stats: StatsResponse | null }) {
  if (!stats || stats.empty || !stats.scatter.length) {
    return <EmptyState message="Sin apuestas para el gráfico probabilidad vs cuota." />;
  }
  const data = stats.scatter.map((s) => ({ ...s, odd: Number(s.odd), model_prob: Number(s.model_prob), ev: Number(s.ev) }));

  return (
    <Card>
      <h3 className="mb-4 text-sm font-semibold text-slate-200">
        Probabilidad del modelo vs cuota (color = EV)
      </h3>
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <ScatterChart margin={{ top: 8, right: 12, left: -12, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
            <XAxis
              type="number"
              dataKey="odd"
              name="Cuota"
              domain={[1, "auto"]}
              tick={{ fill: "#94a3b8", fontSize: 11 }}
              label={{ value: "Cuota", position: "insideBottom", offset: -2, fill: "#94a3b8", fontSize: 11 }}
            />
            <YAxis
              type="number"
              dataKey="model_prob"
              name="Prob. modelo"
              tickFormatter={(v: number) => `${Math.round(v * 100)}%`}
              tick={{ fill: "#94a3b8", fontSize: 11 }}
            />
            <ReferenceLine x={2} stroke="#475569" strokeDasharray="4 4" />
            <Tooltip
              contentStyle={{
                background: "#0f172a",
                border: "1px solid #334155",
                borderRadius: 10,
                fontSize: 12,
              }}
              formatter={(value, name) => [
                name === "Cuota" ? Number(value).toFixed(2) : `${(Number(value) * 100).toFixed(1)}%`,
                name,
              ]}
            />
            <Scatter data={data}>
              {data.map((d, i) => (
                <Cell key={i} fill={evColor(d.ev)} />
              ))}
            </Scatter>
          </ScatterChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
}