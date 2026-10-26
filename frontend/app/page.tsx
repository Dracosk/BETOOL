"use client";

import { useCallback, useEffect, useState } from "react";
import { RefreshCw, ServerCrash, Target } from "lucide-react";
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
import type { Section } from "@/components/ui";
import { Card, EmptyState, ErrorBanner, LoaderPane, StatusPill } from "@/components/ui";
import { Sidebar, MobileNav } from "@/components/Sidebar";
import { Header } from "@/components/Header";
import { KpiCards } from "@/components/KpiCards";
import { FilterBar } from "@/components/FilterBar";
import { BetsTable } from "@/components/BetsTable";
import { ChartsSection } from "@/components/ChartsSection";
import { BankrollPanel } from "@/components/BankrollPanel";
import { PipelinePanel } from "@/components/PipelinePanel";

export default function Home() {
  const [active, setActive] = useState<Section>("apuestas");
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
    <div className="min-h-screen">
      <Sidebar active={active} onSelect={setActive}>
        <div className="flex flex-col gap-2">
          <StatusPill
            label={apiUp === null ? "Conectando API…" : apiUp ? "API conectada" : "API sin conexión"}
            tone={apiUp === null ? "unknown" : apiUp ? "online" : "offline"}
          />
          <p className="text-[11px] leading-relaxed text-muted/70">
            Backend FastAPI local · puerto 8000
          </p>
        </div>
      </Sidebar>

      <div className="md:pl-64">
        <MobileNav active={active} onSelect={setActive} />

        <Header
          active={active}
          apiUp={apiUp}
          onRefresh={handleRefresh}
          refreshing={refreshing}
          runningJob={runningName}
          showRefresh={active !== "apuestas"}
        />

        <main className="mx-auto w-full max-w-7xl px-4 py-8 sm:px-8">
          {error ? (
            <div className="mb-6">
              <ErrorBanner message={error} onClose={() => setError(null)} />
            </div>
          ) : null}

          {active === "apuestas" && (
            <div className="flex flex-col gap-4">
              {apiUp === false ? (
                <Card className="flex flex-col items-center gap-3 px-6 py-16 text-center">
                  <span className="grid h-14 w-14 place-items-center rounded-2xl border border-red-400/30 bg-red-400/10 text-red-300">
                    <ServerCrash className="h-6 w-6" />
                  </span>
                  <p className="text-sm font-semibold text-slate-200">API sin conexión</p>
                  <p className="max-w-md text-sm text-muted">
                    No se puede contactar con el backend en el puerto 8000. Arranca
                    {` `}
                    <code className="rounded bg-surface-2 px-1.5 py-0.5 font-mono text-xs text-emerald-300">
                      start_dev.ps1
                    </code>
                    {` `}
                    y recarga la página.
                  </p>
                </Card>
              ) : betsData === null ? (
                <LoaderPane />
              ) : (
                <>
                  <FilterBar
                    scope={scope}
                    setScope={setScope}
                    market={market}
                    setMarket={setMarket}
                    bets={betsData.bets}
                    onRefresh={handleRefresh}
                    refreshing={refreshing}
                    updatedAt={betsData.updated_at}
                  />
                  <KpiCards bets={betsData.bets} />
                  {!betsData.cached ? (
                    <EmptyState
                      title="Sin predicciones todavía"
                      message="Genera el listado de apuestas de valor +EV. El proceso descarga los modelos y consulta Athena: puede tardar un par de minutos en dar el primer resultado."
                      icon={<Target className="h-6 w-6" />}
                      action={
                        <button
                          onClick={handleRefresh}
                          disabled={refreshing}
                          className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-b from-emerald-400 to-emerald-500 px-4 py-2 text-sm font-semibold text-emerald-950 shadow-[0_8px_20px_-8px_rgba(16,185,129,0.8)] transition-all hover:from-emerald-300 hover:to-emerald-400 disabled:cursor-not-allowed disabled:opacity-60"
                        >
                          <RefreshCw className="h-4 w-4" />
                          {refreshing ? "Calculando…" : "Generar predicciones"}
                        </button>
                      }
                    />
                  ) : betsData.bets.length === 0 ? (
                    <EmptyState
                      title="Sin resultados para estos filtros"
                      message="No hay apuestas que coincidan con el alcance y mercado seleccionados. Prueba con «Todas» o con otro mercado."
                    />
                  ) : (
                    <BetsTable bets={betsData.bets} />
                  )}
                </>
              )}
            </div>
          )}

          {active === "graficas" && (
            <div className="flex flex-col gap-4">
              {betsData && betsData.bets.length > 0 ? <KpiCards bets={betsData.bets} /> : null}
              <ChartsSection stats={stats} />
            </div>
          )}

          {active === "bankroll" && (
            <BankrollPanel bankroll={bankroll} onSettle={handleSettle} settling={settling} />
          )}

          {active === "pipeline" && <PipelinePanel logs={logs} onStart={handleStartPipeline} />}
        </main>
      </div>
    </div>
  );
}