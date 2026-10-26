"use client";

import type { StatsResponse } from "@/lib/api";
import { EvHistogram } from "@/components/charts/EvHistogram";
import { ScatterEvOdd } from "@/components/charts/ScatterEvOdd";
import { MarketsBar } from "@/components/charts/MarketsBar";

export function ChartsSection({ stats }: { stats: StatsResponse | null }) {
  return (
    <div className="flex flex-col gap-4">
      <div className="grid gap-4 lg:grid-cols-2">
        <EvHistogram stats={stats} />
        <ScatterEvOdd stats={stats} />
      </div>
      <MarketsBar stats={stats} />
    </div>
  );
}