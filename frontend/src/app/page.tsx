"use client";

import { useCallback, useEffect, useState } from "react";
import { AppShell } from "@/components/AppShell";
import { JobListTable } from "@/components/JobListTable";
import { ServiceHealthBanner } from "@/components/ServiceHealthBanner";
import { StatCard } from "@/components/StatCard";
import { useAuth } from "@/contexts/AuthProvider";
import {
  fetchJobs,
  fetchStats,
  fetchServicesHealth,
  fetchAutomationStatus,
  fetchUrgencyStatus,
  pingClaude,
  triggerAutomation,
  runScraper,
  runEuJobsScraper,
  runScholarshipScraper,
  runProfessionScraper,
  runCanary,
  type Job,
  type Stats,
  type ServicesHealth,
} from "@/lib/api";

export default function Home() {
  const { session, loading: authLoading } = useAuth();
  const [stats, setStats] = useState<Stats | null>(null);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [jobsHasMore, setJobsHasMore] = useState(false);
  const [jobsLoadingMore, setJobsLoadingMore] = useState(false);
  const DASHBOARD_JOBS_LIMIT = 20;
  const [servicesHealth, setServicesHealth] = useState<ServicesHealth | null>(null);
  const [healthLoading, setHealthLoading] = useState(true);
  const [dataLoading, setDataLoading] = useState(false);
  const [scraping, setScraping] = useState(false);
  const [euScraping, setEuScraping] = useState(false);
  const [scholarshipScraping, setScholarshipScraping] = useState(false);
  const [professionScraping, setProfessionScraping] = useState(false);
  const [canaryRunning, setCanaryRunning] = useState(false);
  const [dataError, setDataError] = useState<string | null>(null);
  const [automation, setAutomation] = useState<string | null>(null);
  const [automationRunning, setAutomationRunning] = useState(false);
  const [urgencyMsg, setUrgencyMsg] = useState<string | null>(null);
  const [claudeLiveOk, setClaudeLiveOk] = useState<boolean | null>(null);
  const [claudeLiveTesting, setClaudeLiveTesting] = useState(false);

  const loadHealth = useCallback(async () => {
    setHealthLoading(true);
    try {
      setServicesHealth(await fetchServicesHealth());
    } catch {
      setServicesHealth(null);
    } finally {
      setHealthLoading(false);
    }
  }, []);

  const loadData = useCallback(async () => {
    if (!session) return;
    setDataLoading(true);
    setDataError(null);
    try {
      const [s, j, auto, urg] = await Promise.all([
        fetchStats(),
        fetchJobs({ limit: DASHBOARD_JOBS_LIMIT, offset: 0 }),
        fetchAutomationStatus().catch(() => null),
        fetchUrgencyStatus().catch(() => null),
      ]);
      setStats(s);
      setJobs(j.jobs);
      setJobsHasMore(j.has_more);
      if (auto?.enabled) {
        const parts = [
          auto.thread_alive ? "automation on" : "automation idle",
          `${auto.state.applications_today_count}/${auto.apply_max_per_day} applies today`,
        ];
        setAutomation(parts.join(" · "));
      } else {
        setAutomation("automation off (local backend only)");
      }
      if (urg) {
        setUrgencyMsg(
          urg.urgency_active
            ? `${urg.message} · apply ${urg.schedule.apply_max_per_day}/day · scan every ${urg.schedule.check_cycle_minutes}m`
            : urg.message,
        );
      }
    } catch (e) {
      setDataError(e instanceof Error ? e.message : "Failed to load data");
    } finally {
      setDataLoading(false);
    }
  }, [session]);

  useEffect(() => {
    void loadHealth();
  }, [loadHealth]);

  useEffect(() => {
    if (authLoading) return;
    void loadData();
  }, [authLoading, loadData]);

  async function handleClaudeLiveTest() {
    setClaudeLiveTesting(true);
    setDataError(null);
    try {
      const result = await pingClaude();
      setClaudeLiveOk(result.ok);
    } catch (e) {
      setClaudeLiveOk(false);
      setDataError(e instanceof Error ? e.message : "Claude live test failed");
    } finally {
      setClaudeLiveTesting(false);
    }
  }

  async function handleScrape() {
    setScraping(true);
    setDataError(null);
    try {
      await runScraper();
      await loadData();
    } catch (e) {
      setDataError(e instanceof Error ? e.message : "Scraper failed");
    } finally {
      setScraping(false);
    }
  }

  async function handleEuScrape() {
    setEuScraping(true);
    setDataError(null);
    try {
      await runEuJobsScraper();
      await loadData();
    } catch (e) {
      setDataError(e instanceof Error ? e.message : "EU scraper failed");
    } finally {
      setEuScraping(false);
    }
  }

  async function handleScholarshipScrape() {
    setScholarshipScraping(true);
    setDataError(null);
    try {
      await runScholarshipScraper();
      await loadData();
    } catch (e) {
      setDataError(e instanceof Error ? e.message : "Scholarship scraper failed");
    } finally {
      setScholarshipScraping(false);
    }
  }

  async function handleProfessionScrape() {
    setProfessionScraping(true);
    setDataError(null);
    try {
      await runProfessionScraper();
      await loadData();
    } catch (e) {
      setDataError(e instanceof Error ? e.message : "Profession scraper failed");
    } finally {
      setProfessionScraping(false);
    }
  }

  async function handleCanary() {
    setCanaryRunning(true);
    setDataError(null);
    try {
      await runCanary();
    } catch (e) {
      setDataError(e instanceof Error ? e.message : "Canary failed");
    } finally {
      setCanaryRunning(false);
    }
  }

  async function handleAutomationRun() {
    setAutomationRunning(true);
    setDataError(null);
    try {
      await triggerAutomation();
      setAutomation("Automation cycle started — check Telegram for progress");
    } catch (e) {
      setDataError(e instanceof Error ? e.message : "Automation failed");
    } finally {
      setAutomationRunning(false);
    }
  }

  const apiConnected = Boolean(servicesHealth?.ok);
  const tableLoading = authLoading || dataLoading;

  return (
    <AppShell title="Dashboard" connected={apiConnected}>
      {urgencyMsg && (
        <div
          className={`mb-4 rounded-xl border px-4 py-3 text-sm ${
            urgencyMsg.includes("CRITICAL") || urgencyMsg.includes("URGENT")
              ? "border-rose-500/40 bg-rose-500/10 text-rose-100"
              : "border-amber-500/30 bg-amber-500/10 text-amber-100"
          }`}
        >
          {urgencyMsg}
        </div>
      )}

      <ServiceHealthBanner
        health={servicesHealth}
        loading={healthLoading}
        claudeLiveOk={claudeLiveOk}
        claudeLiveTesting={claudeLiveTesting}
        onTestClaude={handleClaudeLiveTest}
      />

      {automation && (
        <div className="mb-4">
          <span className="inline-flex items-center rounded-full border border-sky-500/30 bg-sky-500/10 px-3 py-1 text-xs text-sky-300">
            {automation}
          </span>
        </div>
      )}

      {dataError && (
        <div className="mb-4 rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-200">
          {dataError}
        </div>
      )}

      <p className="mb-4 text-sm text-zinc-400">
        Scans all European countries and Hungary for mechatronics roles, plus MSc scholarships.
        LinkedIn runs logged-in — verification prompts go to Telegram.
      </p>
      <div className="mb-4 flex flex-wrap gap-2">
        <button
          type="button"
          onClick={handleAutomationRun}
          disabled={automationRunning}
          className="rounded-xl border border-sky-500/30 bg-sky-500/10 px-4 py-2 text-sm text-sky-200 hover:bg-sky-500/20 disabled:opacity-50"
        >
          {automationRunning ? "Starting automation…" : "Run automation cycle"}
        </button>
        <button
          type="button"
          onClick={handleEuScrape}
          disabled={euScraping}
          className="rounded-xl bg-[var(--color-accent)] px-4 py-2 text-sm font-medium text-black transition-opacity hover:opacity-90 disabled:opacity-50"
        >
          {euScraping ? "Scanning Europe…" : "Scan all Europe + Hungary jobs"}
        </button>
        <button
          type="button"
          onClick={handleScholarshipScrape}
          disabled={scholarshipScraping}
          className="rounded-xl border border-violet-500/30 bg-violet-500/10 px-4 py-2 text-sm text-violet-200 hover:bg-violet-500/20 disabled:opacity-50"
        >
          {scholarshipScraping ? "Scanning scholarships…" : "Scan scholarships"}
        </button>
        <button
          type="button"
          onClick={handleScrape}
          disabled={scraping}
          className="rounded-xl border border-white/10 px-4 py-2 text-sm text-zinc-300 hover:bg-white/5 disabled:opacity-50"
        >
          {scraping ? "Scraping LinkedIn…" : "LinkedIn (single search)"}
        </button>
        <button
          type="button"
          onClick={handleProfessionScrape}
          disabled={professionScraping}
          className="rounded-xl border border-white/10 px-4 py-2 text-sm text-zinc-300 hover:bg-white/5 disabled:opacity-50"
        >
          {professionScraping ? "Scraping profession.hu…" : "Scrape profession.hu"}
        </button>
        <button
          type="button"
          onClick={handleCanary}
          disabled={canaryRunning}
          className="rounded-xl border border-amber-500/30 px-4 py-2 text-sm text-amber-200 hover:bg-amber-500/10 disabled:opacity-50"
        >
          {canaryRunning ? "Running canary…" : "Run DOM canary"}
        </button>
      </div>

      <div className="grid gap-4 md:grid-cols-4 lg:grid-cols-6">
        <StatCard label="Jobs Found" value={stats?.found ?? "—"} />
        <StatCard label="Scholarships" value={stats?.scholarships ?? "—"} />
        <StatCard label="Applied OK" value={stats?.applications_successful ?? "—"} />
        <StatCard label="Apply failed" value={stats?.applications_failed ?? "—"} />
        <StatCard label="Pending review" value={stats?.applications_pending_review ?? "—"} />
        <StatCard label="Cover letters" value={stats?.with_cover_letter ?? "—"} />
      </div>

      <div className="mt-6 rounded-2xl border border-white/10 bg-white/5">
        <div className="flex flex-col gap-3 p-4 md:flex-row md:items-center md:justify-between">
          <div>
            <div className="text-sm font-medium text-white">Recent jobs</div>
            <div className="mt-1 text-xs text-zinc-400">
              Jobs and scholarships — click a row for summary, or use the link column.
            </div>
          </div>
          <div className="flex flex-wrap gap-2">
            <span className="inline-flex items-center rounded-full border border-white/10 bg-black/20 px-3 py-1 text-xs text-zinc-300">
              Needs answer: {stats?.needs_answer ?? 0}
            </span>
            <span className="inline-flex items-center rounded-full border border-white/10 bg-black/20 px-3 py-1 text-xs text-zinc-300">
              Failed: {stats?.failed ?? 0}
            </span>
          </div>
        </div>

        <JobListTable
          jobs={jobs}
          loading={tableLoading}
          onJobUpdate={(jobId, patch) =>
            setJobs((prev) =>
              prev.map((j) => (j.id === jobId ? { ...j, ...patch } : j)),
            )
          }
        />
        {jobsHasMore && (
          <div className="mt-4 text-center">
            <button
              type="button"
              disabled={jobsLoadingMore}
              onClick={async () => {
                if (!session) return;
                setJobsLoadingMore(true);
                try {
                  const { jobs: more, has_more } = await fetchJobs({
                    limit: DASHBOARD_JOBS_LIMIT,
                    offset: jobs.length,
                  });
                  setJobs((prev) => [...prev, ...more]);
                  setJobsHasMore(has_more);
                } finally {
                  setJobsLoadingMore(false);
                }
              }}
              className="rounded-xl border border-white/10 px-6 py-2 text-sm text-zinc-300 hover:bg-white/5 disabled:opacity-50"
            >
              {jobsLoadingMore ? "Loading…" : "Load more jobs"}
            </button>
          </div>
        )}
      </div>
    </AppShell>
  );
}
