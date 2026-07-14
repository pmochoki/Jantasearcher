/** Strip HTML tags for fallback display before Claude translation loads. */
export function stripHtml(text: string): string {
  if (!text) return "";
  const withBreaks = text.replace(/<\/(p|div|li|h[1-6]|tr)>/gi, "\n").replace(/<br\s*\/?>/gi, "\n");
  const stripped = withBreaks.replace(/<[^>]+>/g, " ");
  const decoded = stripped
    .replace(/&nbsp;/g, " ")
    .replace(/&amp;/g, "&")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'");
  return decoded
    .split("\n")
    .map((line) => line.replace(/\s+/g, " ").trim())
    .filter(Boolean)
    .join("\n");
}

export function listingPreview(job: { description_en?: string | null; description?: string }): string {
  if (job.description_en?.trim()) return job.description_en;
  return stripHtml(job.description || "");
}
