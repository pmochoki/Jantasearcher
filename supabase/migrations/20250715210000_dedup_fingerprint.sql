-- Step 5: fingerprint dedup, fix find_duplicate_job overload, last_seen tracking

ALTER TABLE public.jobs
  ADD COLUMN IF NOT EXISTS listing_fingerprint TEXT,
  ADD COLUMN IF NOT EXISTS last_seen_at TIMESTAMPTZ NOT NULL DEFAULT now();

CREATE INDEX IF NOT EXISTS jobs_listing_fingerprint_idx
  ON public.jobs (listing_fingerprint)
  WHERE listing_fingerprint IS NOT NULL;

CREATE INDEX IF NOT EXISTS jobs_user_fingerprint_idx
  ON public.jobs (user_id, listing_fingerprint)
  WHERE user_id IS NOT NULL AND listing_fingerprint IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS jobs_user_source_job_id_unique
  ON public.jobs (user_id, source_job_id)
  WHERE user_id IS NOT NULL AND source_job_id IS NOT NULL;

-- PostgREST cannot choose between 3-arg and 4-arg overloads — keep one signature.
DROP FUNCTION IF EXISTS public.find_duplicate_job(TEXT, TEXT, REAL);

CREATE OR REPLACE FUNCTION public.find_duplicate_job(
  p_company TEXT,
  p_title TEXT,
  p_similarity_threshold REAL DEFAULT 0.72,
  p_user_id UUID DEFAULT NULL
)
RETURNS UUID
LANGUAGE sql
STABLE
AS $$
  SELECT j.id
  FROM public.jobs j
  WHERE similarity(j.normalized_company, public.normalize_job_text(p_company)) >= p_similarity_threshold
    AND similarity(j.normalized_title, public.normalize_job_text(p_title)) >= p_similarity_threshold
    AND (p_user_id IS NULL OR j.user_id = p_user_id)
  ORDER BY
    (
      similarity(j.normalized_company, public.normalize_job_text(p_company))
      + similarity(j.normalized_title, public.normalize_job_text(p_title))
    ) DESC,
    j.date_found DESC
  LIMIT 1;
$$;

COMMENT ON FUNCTION public.find_duplicate_job IS
  'Fuzzy duplicate lookup scoped per user when p_user_id is set.';
