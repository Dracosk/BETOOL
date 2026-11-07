"use client";

import { useMemo, useState } from "react";
import { ArrowDown, ArrowUp, ChevronsUpDown, CircleDot } from "lucide-react";
import type { Bet } from "@/lib/api";
import { Badge, Card } from "@/components/ui";
import { cn } from "@/lib/cn";
import { dateOnly, evBadgeCls, evBarCls, evTier, fmt, pct } from "@/lib/format";

type Props = {
  bets: Bet[];
};

type SortKey = "ev" | "date";
type SortDir = "asc" | "desc";

function dateValue(bet: Bet): number {
  const raw = String(bet.game_date ?? "").trim();
  if (!raw) return Number.POSITIVE_INFINITY;
  const iso = raw.includes("T") ? raw : raw.replace(" ", "T");
  const parsed = Date.parse(iso);
  if (!Number.isNaN(parsed)) return parsed;
  const fallback = Date.parse(`${raw.slice(0, 10)}T00:00:00`);
  return Number.isNaN(fallback) ? Number.POSITIVE_INFINITY : fallback;
}

function SortIcon({ active, dir }: { active: boolean; dir: SortDir }) {
  const Icon = !active ? ChevronsUpDown : dir === "asc" ? ArrowUp : ArrowDown;
  return (
    <Icon
      aria-hidden="true"
      className={cn(
        "h-3 w-3 shrink-0 transition-colors",
        active ? "text-emerald-300" : "text-muted/50 group-hover/sort:text-muted",
      )}
    />
  );
}

export function BetsTable({ bets }: Props) {
  const [sort, setSort] = useState<{ key: SortKey; dir: SortDir }>({ key: "ev", dir: "desc" });

  function toggleSort(key: SortKey) {
    setSort((prev) =>
      prev.key === key
        ? { key, dir: prev.dir === "asc" ? "desc" : "asc" }
        : { key, dir: key === "date" ? "asc" : "desc" },
    );
  }

  const sortedBets = useMemo(() => {
    const rows = [...bets];
    rows.sort((a, b) => {
      if (sort.key === "date") {
        const da = dateValue(a);
        const db = dateValue(b);
        const aMissing = !Number.isFinite(da);
        const bMissing = !Number.isFinite(db);
        // Las apuestas sin fecha válida van siempre al final.
        if (aMissing || bMissing) {
          if (aMissing && bMissing) return (Number(b.ev) || 0) - (Number(a.ev) || 0);
          return aMissing ? 1 : -1;
        }
        if (da !== db) return sort.dir === "asc" ? da - db : db - da;
        return (Number(b.ev) || 0) - (Number(a.ev) || 0);
      }
      const ea = Number(a.ev) || 0;
      const eb = Number(b.ev) || 0;
      if (ea !== eb) return sort.dir === "asc" ? ea - eb : eb - ea;
      const da = dateValue(a);
      const db = dateValue(b);
      if (!Number.isFinite(da) || !Number.isFinite(db)) {
        return da === db ? 0 : Number.isFinite(da) ? -1 : 1;
      }
      return da - db;
    });
    return rows;
  }, [bets, sort]);

  const orderLabel =
    sort.key === "date"
      ? `ordenadas por fecha (${sort.dir === "asc" ? "más próximas primero" : "más lejanas primero"})`
      : `ordenadas por EV (${sort.dir === "asc" ? "menor primero" : "mayor primero"})`;

  const ariaSort = (key: SortKey) =>
    sort.key === key ? (sort.dir === "asc" ? "ascending" : "descending") : "none";

  return (
    <Card className="rise-in !p-0 overflow-hidden">
      <div className="flex items-center justify-between border-b border-border px-5 py-4">
        <div>
          <h3 className="text-sm font-semibold text-slate-100">Candidatas de valor</h3>
          <p className="text-xs text-muted">
            {bets.length} apuestas · {orderLabel}
          </p>
        </div>
        <Badge className="border-emerald-400/30 bg-emerald-400/5 text-emerald-300">
          <CircleDot className="h-3 w-3" />
          +EV &gt; 0
        </Badge>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full min-w-[860px] border-collapse text-sm">
          <thead>
            <tr className="border-b border-border text-left text-[11px] font-semibold uppercase tracking-widest text-muted">
              <th aria-sort={ariaSort("date")} className="px-5 py-3 font-medium">
                <button
                  type="button"
                  onClick={() => toggleSort("date")}
                  title="Ordenar por fecha"
                  className={cn(
                    "group/sort -mx-1 inline-flex items-center gap-1.5 rounded-md px-1 py-0.5 transition-colors hover:text-slate-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400/60",
                    sort.key === "date" && "text-slate-100",
                  )}
                >
                  Fecha
                  <SortIcon active={sort.key === "date"} dir={sort.dir} />
                </button>
              </th>
              <th className="px-4 py-3 font-medium">Partido</th>
              <th className="px-4 py-3 font-medium">Mercado</th>
              <th className="px-4 py-3 font-medium">Apuesta</th>
              <th className="px-4 py-3 font-medium">Probabilidad</th>
              <th className="px-4 py-3 text-right font-medium">Cuota</th>
              <th aria-sort={ariaSort("ev")} className="px-4 py-3 text-right font-medium">
                <button
                  type="button"
                  onClick={() => toggleSort("ev")}
                  title="Ordenar por EV"
                  className={cn(
                    "group/sort -mx-1 inline-flex items-center gap-1.5 rounded-md px-1 py-0.5 transition-colors hover:text-slate-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400/60",
                    sort.key === "ev" && "text-slate-100",
                  )}
                >
                  EV
                  <SortIcon active={sort.key === "ev"} dir={sort.dir} />
                </button>
              </th>
              <th className="px-4 py-3 text-right font-medium">Bank %</th>
            </tr>
          </thead>
          <tbody>
            {sortedBets.map((bet, i) => {
              const tier = evTier(bet.ev);
              const prob = Math.max(0, Math.min(100, (Number(bet.model_prob) || 0) * 100));
              return (
                <tr
                  key={`${bet.game_id ?? ""}-${i}`}
                  className={cn(
                    "group border-b border-border/60 transition-colors hover:bg-surface-2/50",
                    i % 2 === 1 && "bg-surface/40",
                  )}
                >
                  <td className="whitespace-nowrap px-5 py-3.5 text-slate-300">
                    <div className="text-[13px] font-medium">{dateOnly(bet.game_date)}</div>
                    <div className="text-[11px] text-muted">partido</div>
                  </td>

                  <td className="px-4 py-3.5">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-slate-100">{bet.home ?? "—"}</span>
                      <span className="grid h-6 w-6 shrink-0 place-items-center rounded-md border border-border bg-surface-2 text-[10px] font-bold text-muted">
                        VS
                      </span>
                      <span className="font-semibold text-slate-100">{bet.away ?? "—"}</span>
                    </div>
                  </td>

                  <td className="px-4 py-3.5">
                    <span className="text-[13px] text-slate-300">{bet.market ?? "—"}</span>
                  </td>

                  <td className="px-4 py-3.5">
                    <Badge className="border-border bg-surface-2 text-slate-200">
                      {bet.bet_name ?? "—"}
                    </Badge>
                  </td>

                  <td className="px-4 py-3.5">
                    <div className="flex items-center gap-2">
                      <div className="h-1.5 w-20 overflow-hidden rounded-full bg-slate-800">
                        <div
                          className={cn("h-full rounded-full bg-gradient-to-r", evBarCls[tier])}
                          style={{ width: `${prob}%` }}
                        />
                      </div>
                      <span className="w-11 text-right tabular-nums text-slate-300">
                        {pct(bet.model_prob)}
                      </span>
                    </div>
                  </td>

                  <td className="px-4 py-3.5 text-right">
                    <span className="inline-block rounded-lg border border-amber-400/20 bg-amber-400/10 px-2 py-0.5 font-mono font-semibold tabular-nums text-amber-300">
                      {fmt(bet.odd)}
                    </span>
                  </td>

                  <td className="px-4 py-3.5 text-right">
                    <Badge className={cn("font-semibold tabular-nums", evBadgeCls[tier])}>
                      +{fmt(bet.ev)}%
                    </Badge>
                  </td>

                  <td className="px-4 py-3.5 text-right font-mono font-semibold tabular-nums text-slate-200">
                    {fmt(bet.bank)}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </Card>
  );
}