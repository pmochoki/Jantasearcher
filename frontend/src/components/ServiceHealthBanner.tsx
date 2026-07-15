"use client";

import type { ServicesHealth } from "@/lib/api";

function Pill({
  label,
  ok,
  detail,
  warn,
}: {
  label: string;
  ok: boolean;
  detail?: string;
  warn?: boolean;
}) {
  const tone = ok
    ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-300"
    : warn
      ? "border-amber-500/30 bg-amber-500/10 text-amber-300"
      : "border-rose-500/30 bg-rose-500/10 text-rose-300";

  return (
    <span
      className={`inline-flex max-w-full items-center rounded-full border px-3 py-1 text-xs ${tone}`}
      title={detail}
    >
      {label}
      {detail ? `: ${detail}` : ""}
    </span>
  );
}

export function ServiceHealthBanner({
  health,
  loading,
  claudeLiveOk,
  claudeLiveTesting,
  onTestClaude,
}: {
  health: ServicesHealth | null;
  loading: boolean;
  claudeLiveOk?: boolean | null;
  claudeLiveTesting?: boolean;
  onTestClaude?: () => void;
}) {
  if (loading && !health) {
    return (
      <div className="mb-4 flex flex-wrap gap-2">
        <span className="text-xs text-zinc-500">Checking services…</span>
      </div>
    );
  }

  if (!health) {
    return (
      <div className="mb-4 rounded-xl border border-rose-500/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-200">
        Could not reach the API — is the backend running?
      </div>
    );
  }

  const s = health.services;
  const supabaseDetail =
    s.supabase.jobs_count != null ? `${s.supabase.jobs_count} listings` : s.supabase.detail;

  return (
    <div className="mb-4 space-y-2">
      <div className="flex flex-wrap gap-2">
        <Pill label="Supabase" ok={s.supabase.ok} detail={supabaseDetail} />
        <Pill
          label="Claude"
          ok={s.claude.ok && claudeLiveOk !== false}
          detail={
            claudeLiveOk === true
              ? "live test OK"
              : s.claude.model
                ? s.claude.model
                : s.claude.detail
          }
          warn={s.claude.ok && claudeLiveOk == null}
        />
        <Pill
          label="LinkedIn"
          ok={s.linkedin.ok}
          detail={s.linkedin.local_only ? "local Mac" : s.linkedin.detail}
          warn={Boolean(s.linkedin.local_only)}
        />
        <Pill
          label="Telegram"
          ok={s.telegram.ok}
          detail={s.telegram.local_only ? "local Mac" : s.telegram.detail}
          warn={Boolean(s.telegram.local_only && s.telegram.token_configured)}
        />
        <Pill
          label="Automation"
          ok={s.automation.ok}
          detail={s.automation.vercel ? "use local backend" : s.automation.detail}
          warn={Boolean(s.automation.vercel)}
        />
      </div>
      {s.claude.ok && onTestClaude && (
        <button
          type="button"
          onClick={onTestClaude}
          disabled={claudeLiveTesting}
          className="rounded-lg border border-violet-500/30 bg-violet-500/10 px-3 py-1.5 text-xs text-violet-200 hover:bg-violet-500/20 disabled:opacity-50"
        >
          {claudeLiveTesting ? "Testing Claude…" : "Run Claude live test"}
        </button>
      )}
      {health.host === "vercel" && (
        <p className="text-xs text-zinc-500">
          Scrapers, LinkedIn session, and Telegram bot run on your Mac — Vercel serves the dashboard
          and API.
        </p>
      )}
    </div>
  );
}
