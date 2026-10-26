"use client";

import { useCallback, useEffect, useState } from "react";
import {
  api,
  errorMessage,
  type BankrollBet,
  type BankrollResponse,
  type BetsResponse,
  type PipelineLogs,
  type Scope,
  type StatsResponse,
} from "@/lib/api";
import { cn } from "@/lib/cn";
import { KpiCards } from "@/components/KpiCards";
import { FilterBar } from "@/components/FilterBar";
import { BetsTable } from "@/components/BetsTable";
import { ChartsSection } from "@/components/ChartsSection";
import { BankrollPanel } from "@/components/BankrollPanel";
import { PipelinePanel } from "@/components/PipelinePanel";
import { Badge, EmptyState } from "@/components/ui";

type Tab = "apuestas" | "graficas" | "bankroll" | "pipeline";

const TABS: { key: Tab; label: string }[] = [
  { key: "apuestas", label: "Apuestas" },
  { key: "graficas", label: "Gráficas" },
  { key: "bankroll", label: "Bankroll" },
  { key: "pipeline", label: "Pipeline" },
];

export default function Home() {
  const [tab, setTab] = useState<Tab>("apuestas");
  const [scope, setScope] = useState<Scope>("all");
  const [market, setMarket] = useState("");

  const [betsData, setBetsData] = useState<BetsResponse | null>(null);
  const [stats, setStats] = useState<StatsResponse | null>(null);
  const [bankroll, setBankroll] = useState<BankrollResponse | null>(null);
  const [logs, setLogs] = useState<PipelineLogs | null>(null);

  const [apiUp, setApiUp] = useState<boolean | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [settling, setSettling] = useState<{ filename: string; index: number } | null>(null);
  const [error, setError] = useState<string | null>(null);

  const loadBets = useCallback(async () => {
    try {
      setBetsData(await api.getBets(scope, market || undefined));
    } catch (err) {
      setError(errorMessage(err));
    }
  }, [scope, market]);

  const loadStats = useCallback(async () => {
    try {
      setStats(await api.getStats());
    } catch {
      /* ok */
    }
  }, []);

  const loadBankroll = useCallback(async () => {
    try {
      setBankroll(await api.getBankroll());
    } catch {
      /* ok */
    }
  }, []);

  const loadLogs = useCallback(async () => {
    try {
      setLogs(await api.getPipelineLogs());
    } catch {
      /* ok */
    }
  }, []);

  const refreshAll = useCallback(async () => {
    await loadBets();
    await Promise.all([loadStats(), loadBankroll()]);
  }, [loadBets, loadStats, loadBankroll]);

  useEffect(() => {
    api
      .health()
      .then(() => setApiUp(true))
      .catch(() => setApiUp(false));
    /* eslint-disable react-hooks/set-state-in-effect */
    loadBets();
    loadStats();
    loadBankroll();
    loadLogs();
    /* eslint-enable react-hooks/set-state-in-effect */
  }, [loadBets, loadStats, loadBankroll, loadLogs]);

  // Polling mientras haya una tarea en ejecución.
  const runningName = logs?.status?.running ?? null;
  useEffect(() => {
    if (!runningName) return;
    let cancelled = false;
    const id = setInterval(async () => {
      try {
        const fresh = await api.getPipelineLogs();
        if (cancelled) return;
        setLogs(fresh);
        if (!fresh.status.running) {
          clearInterval(id);
          await refreshAll();
        }
      } catch {
        /* reintentar */
      }
    }, 2000);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, [runningName, refreshAll]);

  async function handleRefresh() {
    setRefreshing(true);
    setError(null);
    try {
      const res = await api.refreshPredictions();
      setLogs({ logs: logs?.logs ?? [], status: res.status });
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setRefreshing(false);
    }
  }

  async function handleStartPipeline(module: string, s: Scope) {
    setError(null);
    try {
      const res = await api.startPipeline(module, s);
      await loadLogs();
      if (!res.started) setError("La tarea no se inició.");
    } catch (err) {
      setError(errorMessage(err));
    }
  }

  async function handleSettle(bet: BankrollBet, status: string) {
    setSettling({ filename: bet.filename, index: bet.index });
    setError(null);
    try {
      await api.settle(bet.filename, bet.index, status);
      await loadBankroll();
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setSettling(null);
    }
  }

  return (
    <main className="mx-auto flex w-full max-w-7xl flex-1 flex-col gap-6 px-4 py-8 sm:px-6 lg:px-8">
      {/* Cabecera */}
      <header className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="flex items-center gap-3 text-2xl font-bold tracking-tight text-slate-50">
            <span className="grid h-9 w-9 place-items-center rounded-xl bg-emerald-500 text-lg font-black text-emerald-950">
              B
            </span>
            BETOOL
            <span className="text-sm font-medium text-emerald-400">+EV</span>
          </h1>
          <p className="mt-1 text-sm text-slate-400">
            Motor XGBoost de apuestas de valor · {betsData?.total ?? 0} candidatas disponibles
          </p>
        </div>
        <Badge
          className={
            apiUp === null
              ? "border-slate-700 bg-slate-800 text-slate-300"
              : apiUp
                ? "border-emerald-500/50 bg-emerald-500/10 text-emerald-300"
                : "border-red-500/50 bg-red-500/10 text-red-300"
          }
        >
          <span
            className={cn(
              "h-1.5 w-1.5 rounded-full",
              apiUp === null ? "bg-slate-400" : apiUp ? "bg-emerald-400" : "bg-red-400",
            )}
          />
          {apiUp === null ? "Conectando API…" : apiUp ? "API conectada" : "API sin conexión"}
        </Badge>
      </header>

      {error ? (
        <div className="rounded-xl border border-red-500/40 bg-red-500/10 px-4 py-3 text-sm text-red-300">
          ⚠ {error}
        </div>
      ) : null}

      {/* Navegación */}
      <nav className="flex gap-1 rounded-xl border border-slate-800 bg-slate-900/70 p-1.5">
        {TABS.map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={cn(
              "flex-1 rounded-lg px-4 py-2 text-sm font-semibold transition-colors sm:flex-none sm:px-6",
              tab === t.key
                ? "bg-emerald-500 text-emerald-950 shadow"
                : "text-slate-300 hover:bg-slate-800 hover:text-white",
            )}
          >
            {t.label}
          </button>
        ))}
      </nav>

      {/* Contenido */}
      {tab === "apuestas" && (
        <div className="flex flex-col gap-4">
          <FilterBar
            scope={scope}
            setScope={setScope}
            market={market}
            setMarket={setMarket}
            bets={betsData?.bets ?? []}
            onRefresh={handleRefresh}
            refreshing={refreshing}
            updatedAt={betsData?.updated_at ?? null}
          />
          <KpiCards bets={betsData?.bets ?? []} />
          {!betsData?.cached ? (
            <EmptyState message="Aún no hay predicciones. Pulsa «Actualizar predicciones» para generar el listado de apuestas +EV (puede tardar un par de minutos, descarga modelos y consulta Athena)." />
          ) : (
            <BetsTable bets={betsData?.bets ?? []} />
          )}
        </div>
      )}

      {tab === "graficas" && <ChartsSection stats={stats} />}

      {tab === "bankroll" && (
        <BankrollPanel bankroll={bankroll} onSettle={handleSettle} settling={settling} />
      )}

      {tab === "pipeline" && <PipelinePanel logs={logs} onStart={handleStartPipeline} />}
    </main>
  );
}