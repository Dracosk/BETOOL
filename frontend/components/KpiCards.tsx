import type { Bet } from "@/lib/api";
import { Card } from "@/components/ui";

function fmt(v: number | null | undefined, digits = 2): string {
  if (v === null || v === undefined || Number.isNaN(Number(v))) return "—";
  return Number(v).toFixed(digits);
}

export function KpiCards({ bets }: { bets: Bet[] }) {
  const evs = bets.map((b) => Number(b.ev) || 0);
  const banks = bets.map((b) => Number(b.bank) || 0);
  const avgEv = evs.length ? evs.reduce((a, b) => a + b, 0) / evs.length : 0;
  const maxEv = evs.length ? Math.max(...evs) : 0;
  const totalBank = banks.reduce((a, b) => a + b, 0);

  const items = [
    { label: "Apuestas +EV", value: String(bets.length), accent: false },
    { label: "Mejor EV", value: `${fmt(maxEv)}%`, accent: true },
    { label: "EV medio", value: `${fmt(avgEv)}%`, accent: true },
    { label: "Bank total (%)", value: fmt(totalBank), accent: false },
  ];

  return (
    <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
      {items.map((item) => (
        <Card key={item.label} className="flex flex-col gap-1 !p-4">
          <span className="text-xs uppercase tracking-wider text-slate-400">
            {item.label}
          </span>
          <span
            className={
              item.accent
                ? "text-2xl font-bold text-emerald-400"
                : "text-2xl font-bold text-slate-100"
            }
          >
            {item.value}
          </span>
        </Card>
      ))}
    </div>
  );
}