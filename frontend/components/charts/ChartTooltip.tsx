"use client";

type PayloadItem = {
  name?: string;
  value?: number | string;
  color?: string;
};

export function ChartTooltip({
  label,
  items,
  extra,
}: {
  label?: string;
  items: PayloadItem[];
  extra?: { label: string; value: string }[];
}) {
  if (!items.length && !extra?.length) return null;
  return (
    <div className="max-w-xs rounded-xl border border-border bg-[#0d1526]/95 px-3.5 py-2.5 shadow-2xl backdrop-blur">
      {label ? (
        <p className="mb-1.5 text-[11px] font-semibold uppercase tracking-wider text-muted">
          {label}
        </p>
      ) : null}
      <div className="space-y-1">
        {items.map((item, i) => (
          <div key={i} className="flex items-center justify-between gap-4 text-xs">
            <span className="flex items-center gap-1.5 text-slate-300">
              {item.color ? (
                <span
                  className="h-2 w-2 rounded-sm"
                  style={{ background: item.color }}
                />
              ) : null}
              {item.name}
            </span>
            <span className="font-mono font-semibold tabular-nums text-slate-100">
              {item.value}
            </span>
          </div>
        ))}
        {extra?.map((e, i) => (
          <div key={`x-${i}`} className="flex items-center justify-between gap-4 text-xs">
            <span className="text-slate-300">{e.label}</span>
            <span className="font-mono font-semibold tabular-nums text-emerald-300">
              {e.value}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}