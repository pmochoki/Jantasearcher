import { AppShell } from "@/components/AppShell";

export default function SettingsPage() {
  return (
    <AppShell title="Settings">
      <div className="grid gap-4 md:grid-cols-2">
        <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
          <div className="text-sm font-medium text-white">Credentials</div>
          <div className="mt-2 text-sm text-zinc-300">
            Settings UI is stubbed. Keys and credentials will be stored server-side
            via `.env` (never in the frontend).
          </div>
        </div>
        <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
          <div className="text-sm font-medium text-white">Automation</div>
          <div className="mt-2 text-sm text-zinc-300">
            Daily caps, active hours, blacklists, and job search criteria will
            be configured here.
          </div>
        </div>
      </div>
    </AppShell>
  );
}

