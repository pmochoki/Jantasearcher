"use client";

import { useCallback, useEffect, useState } from "react";
import { AppShell } from "@/components/AppShell";
import { useAuth } from "@/contexts/AuthProvider";
import {
  fetchAutomationRuns,
  fetchAutomationStatus,
  type AutomationRunEntry,
  type AutomationStatus,
} from "@/lib/api";

export default function LogsPage() {
  const { session, loading: authLoading } = useAuth();
  const [runs, setRuns] = useState<AutomationRunEntry[]>([]);
  const [cyclesCompleted, setCyclesCompleted] = useState(0);
  const [status, setStatus] = useState<AutomationStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!session) {
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const [runData, auto] = await Promise.all([
        fetchAutomationRuns(100),
        fetchAutomationStatus().catch(() => null),
      ]);
      setRuns(runData.runs);
      setCyclesCompleted(runData.cycles_completed);
      setStatus(auto);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load logs");
    } finally {
      setLoading(false);
    }
  }, [session]);

  useEffect(() => {
    if (authLoading) return;
    void load();
  }, [authLoading, load]);

  return (
    <AppShell title="Automation Logs" connected={!error && !loading}>
      {error && (
        <div className="mb-4 rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-200">
          {error}
        </div>
      )}

      {status && (
        <div className="mb-6 grid gap-3 sm:grid-cols-3">
          <Stat label="Cycles completed" value={String(cyclesCompleted)} />
          <Stat
            label="Applies today"
            value={`${status.state.applications_today_count}/${status.apply_max_per_day}`}
          />
          <Stat
            label="Automation"
            value={status.enabled ? (status.thread_alive ? "Running" : "Idle") : "Off"}
          />
        </div>
      )}

      {status?.state?.last_error && (
        <div className="mb-4 rounded-xl border border-amber-500/30 bg-amber-500/10 px-4 py-3 text-sm text-amber-100">
          Last error: {status.state.last_error}
        </div>
      )}

      <div className="rounded-2xl border border-white/10 bg-white/5 overflow-hidden">
        <div className="border-b border-white/10 px-4 py-3 text-sm font-medium text-zinc-200">
          Recent runs
        </div>
        {loading ? (
          <div className="p-6 text-center text-sm text-zinc-400">Loading logs…</div>
        ) : runs.length === 0 ? (
          <div className="p-6 text-center text-sm text-zinc-400">
            No automation runs logged yet. Trigger a cycle from the dashboard or wait for the scheduler.
          </div>
        ) : (
          <ul className="divide-y divide-white/5">
            {runs.map((run, i) => (
              <li key={`${run.at}-${i}`} className="px-4 py-3 text-sm">
                <div className="flex flex-wrap items-center gap-2">
                  <span
                    className={`inline-block h-2 w-2 rounded-full ${
                      run.ok ? "bg-emerald-400" : "bg-red-400"
                    }`}
                  />
                  <span className="font-medium text-zinc-200">{run.kind}</span>
                  <span className="text-zinc-500">{formatTime(run.at)}</span>
                </div>
                <p className="mt-1 text-zinc-300">{run.message}</p>
                {run.details && Object.keys(run.details).length > 0 && (
                  <pre className="mt-2 max-h-32 overflow-auto rounded-lg bg-black/30 p-2 text-xs text-zinc-400">
                    {JSON.stringify(run.details, null, 2)}
                  </pre>
                )}
              </li>
            ))}
          </ul>
        )}
      </div>
    </AppShell>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-white/10 bg-white/5 px-4 py-3">
      <div className="text-xs text-zinc-500">{label}</div>
      <div className="text-lg font-semibold text-zinc-100">{value}</div>
    </div>
  );
}

function formatTime(iso: string): string {
  try {
    return new Date(iso).toLocaleString();
  } catch {
    return iso;
  }
}
