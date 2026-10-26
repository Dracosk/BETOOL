export type Bet = {
  game_id?: string | null;
  game_date?: string | null;
  home?: string | null;
  away?: string | null;
  market?: string | null;
  bet_name?: string | null;
  model_prob?: number | null;
  odd?: number | null;
  ev?: number | null;
  bank?: number | null;
};

export type BetsResponse = {
  bets: Bet[];
  total: number;
  count: number;
  scope: string;
  market: string | null;
  cached: boolean;
  updated_at: number | null;
};

export type JobStatus = {
  running: string | null;
  name: string | null;
  status: string;
  started: number | null;
  finished: number | null;
  error: string | null;
  result: unknown;
};

export type StatsResponse = {
  empty: boolean;
  count: number;
  avg_ev: number;
  max_ev: number;
  total_bank: number;
  ev_histogram: { label: string; count: number }[];
  by_market: { market: string; count: number; avg_ev: number }[];
  scatter: {
    ev: number | null;
    odd: number | null;
    model_prob: number | null;
    market: string | null;
  }[];
};

export type BankrollBet = Bet & {
  filename: string;
  index: number;
  settlement: "pending" | "won" | "lost" | "void";
};

export type BankrollResponse = {
  files: { filename: string; created: string | null }[];
  bets: BankrollBet[];
  totals: { potential_ev: number; bank: number; bets: number; settled: number };
  curve: { game_date: string; label: string; settlement: string; pl: number }[];
};

export type PipelineLogs = { logs: string[]; status: JobStatus };

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function http<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      detail = (await res.json()).detail ?? detail;
    } catch {
      /* respuesta sin JSON */
    }
    throw new Error(detail || `Error ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export type Scope = "all" | "today" | "3d";

export const api = {
  health: () => http<{ status: string }>("/api/health"),

  getBets: (scope: Scope = "all", market?: string) =>
    http<BetsResponse>(
      `/api/bets?scope=${scope}${market ? `&market=${encodeURIComponent(market)}` : ""}`,
    ),

  refreshPredictions: () =>
    http<{ started: boolean; status: JobStatus }>("/api/predict/refresh", { method: "POST" }),

  predictStatus: () => http<JobStatus>("/api/predict/status"),

  getStats: () => http<StatsResponse>("/api/stats"),

  getPipelineLogs: () => http<PipelineLogs>("/api/pipeline/logs"),

  startPipeline: (module: string, scope: Scope = "all") =>
    http<{ started: boolean; module: string }>(
      `/api/pipeline/${module}?scope=${scope}`,
      { method: "POST" },
    ),

  getBankroll: () => http<BankrollResponse>("/api/bankroll"),

  settle: (filename: string, index: number, status: string) =>
    http<{ filename: string; index: number; status: string }>("/api/bankroll/settle", {
      method: "POST",
      body: JSON.stringify({ filename, index, status }),
    }),
};

export function errorMessage(err: unknown): string {
  return err instanceof Error ? err.message : String(err);
}