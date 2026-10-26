"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
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
  const highlight = (label: string) => label.startsWith(">");

  return (
    <Card className="rise-in">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold text-slate-100">Distribución de EV</h3>
          <p className="text-xs text-muted">cantidad de apuestas por rango de EV</p>
        </div>
      </div>
      <div className="mt-4 h-60">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 8, right: 8, left: -18, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1d2740" vertical={false} />
            <XAxis
              dataKey="label"
              tick={{ fill: "#8494b5", fontSize: 10 }}
              interval={1}
              axisLine={{ stroke: "#1d2740" }}
              tickLine={false}
            />
            <YAxis
              allowDecimals={false}
              tick={{ fill: "#8494b5", fontSize: 10 }}
              axisLine={false}
              tickLine={false}
            />
            <Bar
              dataKey="count"
              name="Apuestas"
              radius={[5, 5, 0, 0]}
              maxBarSize={34}
            >
              {data.map((entry, i) => (
                <Cell
                  key={i}
                  fill={highlight(entry.label) ? "#34d399" : "#38bdf8"}
                  fillOpacity={highlight(entry.label) ? 1 : 0.55}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
      <p className="mt-2 text-[11px] text-muted">
        <span className="mr-1 inline-block h-2 w-2 rounded-sm bg-[#38bdf8] align-middle" /> EV
        moderado &nbsp;·&nbsp;
        <span className="mr-1 inline-block h-2 w-2 rounded-sm bg-[#34d399] align-middle" /> EV alto
        (≥ 10%)
      </p>
    </Card>
  );
}