export function fmt(v: number | null | undefined, digits = 2): string {
  if (v === null || v === undefined || Number.isNaN(Number(v))) return "—";
  return Number(v).toFixed(digits);
}

export function pct(v: number | null | undefined, digits = 1): string {
  if (v === null || v === undefined || Number.isNaN(Number(v))) return "—";
  return `${(Number(v) * 100).toFixed(digits)}%`;
}

export function dateOnly(s: string | null | undefined): string {
  return String(s ?? "").slice(0, 10);
}

export function dateLong(d: Date): string {
  return d.toLocaleDateString("es-ES", {
    weekday: "long",
    day: "numeric",
    month: "long",
  });
}

export type EvTier = "high" | "mid" | "low" | "none";

export function evTier(ev: number | null | undefined): EvTier {
  if (ev === null || ev === undefined || Number.isNaN(Number(ev))) return "none";
  if (ev >= 10) return "high";
  if (ev >= 6) return "mid";
  return "low";
}

export const evBadgeCls: Record<EvTier, string> = {
  high: "border-emerald-400/40 bg-emerald-400/10 text-emerald-300",
  mid: "border-lime-400/40 bg-lime-400/10 text-lime-300",
  low: "border-sky-400/40 bg-sky-400/10 text-sky-300",
  none: "border-slate-600 bg-slate-800/60 text-slate-400",
};

export const evBarCls: Record<EvTier, string> = {
  high: "from-emerald-400 to-teal-300",
  mid: "from-lime-400 to-green-300",
  low: "from-sky-400 to-cyan-300",
  none: "from-slate-500 to-slate-400",
};

export const evHex: Record<EvTier, string> = {
  high: "#34d399",
  mid: "#a3e635",
  low: "#38bdf8",
  none: "#64748b",
};