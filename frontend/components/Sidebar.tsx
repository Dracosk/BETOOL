"use client";

import type { ReactNode } from "react";
import {
  BarChart3,
  Terminal,
  TrendingUp,
  Wallet,
} from "lucide-react";
import type { Section } from "@/components/ui";
import { cn } from "@/lib/cn";

const NAV: { key: Section; label: string; icon: typeof TrendingUp }[] = [
  { key: "apuestas", label: "Apuestas", icon: TrendingUp },
  { key: "graficas", label: "Gráficas", icon: BarChart3 },
  { key: "bankroll", label: "Bankroll", icon: Wallet },
  { key: "pipeline", label: "Pipeline", icon: Terminal },
];

export function Logo({ compact = false }: { compact?: boolean }) {
  return (
    <div className="flex items-center gap-3">
      <span className="relative grid h-10 w-10 place-items-center rounded-xl bg-gradient-to-br from-emerald-400 to-teal-600 text-lg font-black text-emerald-950 shadow-[0_8px_24px_-8px_rgba(16,185,129,0.7)]">
        B
        <span className="absolute -right-0.5 -top-0.5 h-2.5 w-2.5 rounded-full border-2 border-surface bg-emerald-400" />
      </span>
      {!compact ? (
        <div className="leading-tight">
          <div className="text-[15px] font-bold tracking-tight text-slate-50">
            BETOOL
            <span className="ml-1.5 rounded-md bg-emerald-400/15 px-1.5 py-0.5 align-middle text-[10px] font-black text-emerald-300">
              +EV
            </span>
          </div>
          <div className="text-[11px] text-muted">Apuestas de valor · XGBoost</div>
        </div>
      ) : null}
    </div>
  );
}

export function Sidebar({
  active,
  onSelect,
  children,
}: {
  active: Section;
  onSelect: (s: Section) => void;
  children?: ReactNode;
}) {
  return (
    <aside className="fixed inset-y-0 left-0 z-30 hidden w-64 flex-col border-r border-border bg-surface/60 backdrop-blur-xl md:flex">
      <div className="flex h-20 items-center px-6">
        <Logo />
      </div>

      <nav className="flex-1 space-y-1 px-3">
        <p className="px-3 pb-2 pt-1 text-[11px] font-semibold uppercase tracking-widest text-muted/70">
          Panel
        </p>
        {NAV.map((item) => {
          const Icon = item.icon;
          const isActive = active === item.key;
          return (
            <button
              key={item.key}
              onClick={() => onSelect(item.key)}
              className={cn(
                "group flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-all",
                isActive
                  ? "bg-gradient-to-r from-emerald-400/15 to-transparent text-emerald-300"
                  : "text-muted hover:bg-surface-2 hover:text-slate-100",
              )}
            >
              <span
                className={cn(
                  "grid h-8 w-8 place-items-center rounded-lg border transition-colors",
                  isActive
                    ? "border-emerald-400/30 bg-emerald-400/10 text-emerald-300"
                    : "border-border bg-surface-2 text-muted group-hover:text-slate-200",
                )}
              >
                <Icon className="h-4 w-4" />
              </span>
              <span className="flex-1 text-left">{item.label}</span>
              {isActive ? (
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.9)]" />
              ) : null}
            </button>
          );
        })}
      </nav>

      <div className="border-t border-border p-4">{children}</div>
    </aside>
  );
}

export function MobileNav({
  active,
  onSelect,
}: {
  active: Section;
  onSelect: (s: Section) => void;
}) {
  return (
    <div className="sticky top-0 z-20 border-b border-border bg-background/80 backdrop-blur-xl md:hidden">
      <div className="flex h-16 items-center justify-between px-4">
        <Logo />
      </div>
      <nav className="flex gap-1 overflow-x-auto px-3 pb-2">
        {NAV.map((item) => {
          const Icon = item.icon;
          const isActive = active === item.key;
          return (
            <button
              key={item.key}
              onClick={() => onSelect(item.key)}
              className={cn(
                "flex shrink-0 items-center gap-2 rounded-lg px-3 py-1.5 text-xs font-semibold transition-colors",
                isActive
                  ? "bg-emerald-400/15 text-emerald-300"
                  : "text-muted hover:bg-surface-2 hover:text-slate-100",
              )}
            >
              <Icon className="h-3.5 w-3.5" />
              {item.label}
            </button>
          );
        })}
      </nav>
    </div>
  );
}