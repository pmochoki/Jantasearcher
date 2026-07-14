import type { ApplicationOutcome } from "@/lib/api";

const styles: Record<
  string,
  { label: string; className: string }
> = {
  applied: {
    label: "Application submitted",
    className: "bg-emerald-500/15 text-emerald-200 border-emerald-500/30",
  },
  failed: {
    label: "Application failed",
    className: "bg-rose-500/15 text-rose-200 border-rose-500/30",
  },
  review_pending: {
    label: "Awaiting your approval",
    className: "bg-violet-500/15 text-violet-200 border-violet-500/30",
  },
  needs_answer: {
    label: "Needs your answer",
    className: "bg-amber-500/15 text-amber-200 border-amber-500/30",
  },
  captcha: {
    label: "CAPTCHA — action needed",
    className: "bg-orange-500/15 text-orange-200 border-orange-500/30",
  },
};

export function ApplicationOutcomeBadge({
  outcome,
  message,
}: {
  outcome?: ApplicationOutcome | null;
  message?: string | null;
}) {
  if (!outcome) return null;
  const style = styles[outcome] ?? {
    label: outcome.replaceAll("_", " "),
    className: "bg-white/10 text-zinc-200 border-white/10",
  };

  return (
    <div
      className={`rounded-xl border px-3 py-2 text-sm ${style.className}`}
    >
      <div className="font-medium">{style.label}</div>
      {message ? (
        <div className="mt-1 text-xs opacity-90">{message}</div>
      ) : null}
    </div>
  );
}

export function OpportunityTypeBadge({
  type,
}: {
  type?: string | null;
}) {
  const isScholarship = type === "scholarship";
  return (
    <span
      className={`rounded-full border px-2 py-0.5 text-xs ${
        isScholarship
          ? "border-violet-500/30 bg-violet-500/10 text-violet-200"
          : "border-sky-500/30 bg-sky-500/10 text-sky-200"
      }`}
    >
      {isScholarship ? "Scholarship" : "Job"}
    </span>
  );
}
