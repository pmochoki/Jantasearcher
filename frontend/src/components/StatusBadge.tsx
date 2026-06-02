export type JobStatus = "pending" | "submitted" | "flagged" | "failed";

const styles: Record<JobStatus, { label: string; className: string }> = {
  pending: {
    label: "Pending",
    className: "bg-white/10 text-white border-white/10",
  },
  submitted: {
    label: "Submitted",
    className: "bg-emerald-500/15 text-emerald-200 border-emerald-500/20",
  },
  flagged: {
    label: "Flagged",
    className: "bg-amber-500/15 text-amber-200 border-amber-500/20",
  },
  failed: {
    label: "Failed",
    className: "bg-rose-500/15 text-rose-200 border-rose-500/20",
  },
};

export function StatusBadge({ status }: { status: JobStatus }) {
  const s = styles[status];
  return (
    <span
      className={`inline-flex items-center rounded-full border px-2.5 py-1 text-xs font-medium ${s.className}`}
    >
      {s.label}
    </span>
  );
}

