"use client";

import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { BankrollResponse } from "@/lib/api";
import { Card, EmptyState } from "@/components/ui";
import { ChartTooltip } from "@/components/charts/ChartTooltip";

function waveColor(pl: number) {
  return pl >= 0
    ? { stroke: "#34d399", glow: "rgba(52,211,153,0.25)" }
    : { stroke: "#fb7185", glow: "rgba(251,113,133,0.25)" };
}

export function BankrollCurve({ bankroll }: { bankroll: BankrollResponse | null }) {
  const data = bankroll?.curve ?? [];
  if (!data.length) {
    return (
      <EmptyState
        title="Curva de P&L disponible cuando liquides apuestas"
        message="Marca cada apuesta como ganada o perdida en la tabla inferior para ver la evolución acumulada del bankroll."
      />
    );
  }
  const color = waveColor(data[data.length - 1].pl);
  const gradientId = color.stroke === "#34d399" ? "plUp" : "plDown";

  return (
    <Card className="rise-in">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold text-slate-100">P&L acumulado</h3>
          <p className="text-xs text-muted">unidades × bank (criterio de Kelly)</p>
        </div>
        <span
          className="rounded-lg border px-2.5 py-1 font-mono text-sm font-bold tabular-nums"
          style={{
            color: color.stroke,
            borderColor: `${color.stroke}55`,
            background: `${color.stroke}11`,
          }}
        >
          {data[data.length - 1].pl >= 0 ? "+" : ""}
          {data[data.length - 1].pl.toFixed(2)}
        </span>
      </div>
      <div className="mt-4 h-56">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 8, right: 8, left: -12, bottom: 0 }}>
            <defs>
              <linearGradient id="plUp" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#34d399" stopOpacity={0.35} />
                <stop offset="100%" stopColor="#34d399" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="plDown" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#fb7185" stopOpacity={0.35} />
                <stop offset="100%" stopColor="#fb7185" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#1d2740" vertical={false} />
            <XAxis
              dataKey="game_date"
              tick={{ fill: "#8494b5", fontSize: 10 }}
              axisLine={{ stroke: "#1d2740" }}
              tickLine={false}
            />
            <YAxis tick={{ fill: "#8494b5", fontSize: 10 }} axisLine={false} tickLine={false} />
            <Tooltip
              content={({ active, payload }) => {
                if (!active || !payload?.length) return null;
                const p = payload[0]?.payload as {
                  game_date: string;
                  label: string;
                  settlement: string;
                  pl: number;
                };
                return (
                  <ChartTooltip
                    label={p.game_date}
                    items={[{ name: "P&L acumulado", value: p.pl.toFixed(2) }]}
                    extra={[{ label: p.settlement, value: p.label }]}
                  />
                );
              }}
            />
            <Area
              type="monotone"
              dataKey="pl"
              name="P&L"
              stroke={color.stroke}
              strokeWidth={2.5}
              fill={`url(#${gradientId})`}
              dot={false}
              activeDot={{ r: 4, fill: color.stroke, stroke: "#0b111c", strokeWidth: 2 }}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
}