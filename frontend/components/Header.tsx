"use client";

import { useEffect, useState } from "react";
import { CalendarDays, RefreshCw } from "lucide-react";
import type { Section } from "@/components/ui";
import { Badge, Spinner, StatusPill } from "@/components/ui";
import { dateLong } from "@/lib/format";

const META: Record<Section, { title: string; subtitle: string }> = {
  apuestas: {
    title: "Apuestas de valor",
    subtitle: "Listado +EV generado por el modelo XGBoost con criterio de Kelly.",
  },
  graficas: {
    title: "Gráficas",
    subtitle: "Distribución de EV, probabilidad vs cuota y rendimiento por mercado.",
  },
  bankroll: {
    title: "Bankroll",
    subtitle: "Liquidación de apuestas de papel y evolución del capital.",
  },
  pipeline: {
    title: "Pipeline",
    subtitle: "Ejecuta los módulos de ingesta y predicción con log en vivo.",
  },
};

type Props = {
  active: Section;
  apiUp: boolean | null;
  onRefresh: () => void;
  refreshing: boolean;
  runningJob: string | null;
  showRefresh: boolean;
};

export function Header({
  active,
  apiUp,
  onRefresh,
  refreshing,
  runningJob,
  showRefresh,
}: Props) {
  const meta = META[active];
  const [today, setToday] = useState<Date | null>(null);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- fecha solo-cliente tras montar
    setToday(new Date());
  }, []);

  return (
    <header className="flex flex-wrap items-center justify-between gap-4 border-b border-border bg-background/50 px-4 py-5 backdrop-blur-xl sm:px-8">
      <div>
        <div className="flex items-center gap-3">
          <h1 className="text-xl font-bold tracking-tight text-slate-50">{meta.title}</h1>
          {runningJob ? (
            <Badge className="border-emerald-400/40 bg-emerald-400/10 text-emerald-300">
              <Spinner className="!h-3 !w-3" />
              {runningJob}
            </Badge>
          ) : null}
        </div>
        <p className="mt-0.5 text-sm text-muted">{meta.subtitle}</p>
      </div>

      <div className="flex items-center gap-3">
        {today ? (
          <Badge className="hidden border-border bg-surface-2 text-muted sm:inline-flex">
            <CalendarDays className="h-3.5 w-3.5 text-primary-2" />
            <span className="capitalize">{dateLong(today)}</span>
          </Badge>
        ) : null}
        <StatusPill
          label={apiUp === null ? "Conectando…" : apiUp ? "API conectada" : "API sin conexión"}
          tone={apiUp === null ? "unknown" : apiUp ? "online" : "offline"}
        />
        {showRefresh ? (
          <button
            onClick={onRefresh}
            disabled={refreshing}
            className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-b from-emerald-400 to-emerald-500 px-4 py-2 text-sm font-semibold text-emerald-950 shadow-[0_8px_20px_-8px_rgba(16,185,129,0.8)] transition-all hover:from-emerald-300 hover:to-emerald-400 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {refreshing ? <Spinner className="!h-3.5 !w-3.5 !border-emerald-900/40 !border-t-emerald-950" /> : <RefreshCw className="h-4 w-4" />}
            {refreshing ? "Actualizando…" : "Actualizar"}
          </button>
        ) : null}
      </div>
    </header>
  );
}