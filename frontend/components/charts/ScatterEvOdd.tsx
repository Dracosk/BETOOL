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
import { ChartTooltip } from "@/components/charts/ChartTooltip";
import { evHex, evTier } from "@/lib/format";

export function ScatterEvOdd({ stats }: { stats: StatsResponse | null }) {
  if (!stats || stats.empty || !stats.scatter.length) {
    return <EmptyState message="Sin apuestas para el gráfico probabilidad vs cuota." />;
  }

  const data = stats.scatter.map((s) => ({
    ...s,
    odd: Number(s.odd),
    model_prob: Number(s.model_prob) * 100,
    ev: Number(s.ev),
  }));

  return (
    <Card className="rise-in">
      <div>
        <h3 className="text-sm font-semibold text-slate-100">Probabilidad vs cuota</h3>
        <p className="text-xs text-muted">cada punto es una apuesta · color = EV</p>
      </div>
      <div className="mt-4 h-60">
        <ResponsiveContainer width="100%" height="100%">
          <ScatterChart margin={{ top: 8, right: 12, left: -12, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1d2740" />
            <XAxis
              type="number"
              dataKey="odd"
              name="Cuota"
              domain={[1, "auto"]}
              tick={{ fill: "#8494b5", fontSize: 10 }}
              axisLine={{ stroke: "#1d2740" }}
              tickLine={false}
              label={{ value: "Cuota", position: "insideBottom", offset: -2, fill: "#8494b5", fontSize: 10 }}
            />
            <YAxis
              type="number"
              dataKey="model_prob"
              name="Prob. modelo"
              domain={[0, 100]}
              tickFormatter={(v: number) => `${Math.round(v)}%`}
              tick={{ fill: "#8494b5", fontSize: 10 }}
              axisLine={false}
              tickLine={false}
            />
            <ReferenceLine x={2} stroke="#33415f" strokeDasharray="4 4" />
            <Tooltip
              cursor={{ strokeDasharray: "3 3", stroke: "#33415f" }}
              content={({ active, payload }) => {
                if (!active || !payload?.length) return null;
                const p = payload[0]?.payload as {
                  odd: number;
                  model_prob: number;
                  ev: number;
                  market?: string | null;
                };
                return (
                  <ChartTooltip
                    label="Apuesta"
                    items={[
                      { name: "Cuota", value: p.odd.toFixed(2) },
                      { name: "Prob. modelo", value: `${p.model_prob.toFixed(1)}%` },
                    ]}
                    extra={[{ label: p.market ?? "—", value: `+${p.ev.toFixed(2)}% EV` }]}
                  />
                );
              }}
            />
            <Scatter data={data}>
              {data.map((d, i) => (
                <Cell key={i} fill={evHex[evTier(d.ev)]} fillOpacity={0.85} />
              ))}
            </Scatter>
          </ScatterChart>
        </ResponsiveContainer>
      </div>
      <p className="mt-2 text-[11px] text-muted">
        <span className="mr-1 inline-block h-2 w-2 rounded-sm bg-[#38bdf8] align-middle" /> EV 0–6%
        &nbsp;·&nbsp;
        <span className="mr-1 inline-block h-2 w-2 rounded-sm bg-[#a3e635] align-middle" /> EV 6–10%
        &nbsp;·&nbsp;
        <span className="mr-1 inline-block h-2 w-2 rounded-sm bg-[#34d399] align-middle" /> EV ≥ 10%
      </p>
    </Card>
  );
}