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

export function BankrollCurve({ bankroll }: { bankroll: BankrollResponse | null }) {
  const data = bankroll?.curve ?? [];
  if (!data.length) {
    return <EmptyState message="Marca apuestas como ganadas/perdidas para ver la curva de P&L." />;
  }
  return (
    <Card>
      <h3 className="mb-4 text-sm font-semibold text-slate-200">
        P&L acumulado (unidades × bank)
      </h3>
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 8, right: 12, left: -12, bottom: 0 }}>
            <defs>
              <linearGradient id="plGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#22c55e" stopOpacity={0.35} />
                <stop offset="100%" stopColor="#22c55e" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
            <XAxis dataKey="game_date" tick={{ fill: "#94a3b8", fontSize: 11 }} />
            <YAxis tick={{ fill: "#94a3b8", fontSize: 11 }} />
            <Tooltip
              contentStyle={{
                background: "#0f172a",
                border: "1px solid #334155",
                borderRadius: 10,
                fontSize: 12,
              }}
            />
            <Area
              type="monotone"
              dataKey="pl"
              name="P&L"
              stroke="#22c55e"
              strokeWidth={2}
              fill="url(#plGradient)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
}