from pathlib import Path
import sys

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from ai.cover_letter import generate_cover_letter  # noqa: E402
from database.db import (  # noqa: E402
    get_job,
    get_jobs,
    get_stats,
    init_db,
    update_job_cover_letter,
    update_job_status,
)
from notifications.telegram import notify_cover_letter_ready  # noqa: E402
from scraper.config import ScraperConfig  # noqa: E402
from scraper.linkedin_scraper import run_scraper_sync  # noqa: E402

app = FastAPI(title="JantaSearcher API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    init_db()


class StatusUpdate(BaseModel):
    status: str


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/stats")
def stats():
    return get_stats()


@app.get("/jobs")
def list_jobs(status: str | None = None, limit: int = 100):
    jobs = get_jobs(external_only=True, status=status, limit=limit)
    return {"jobs": jobs}


@app.get("/jobs/{job_id}")
def read_job(job_id: int):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@app.post("/jobs/{job_id}/cover-letter")
def create_cover_letter(job_id: int):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    try:
        letter = generate_cover_letter(
            job_title=job["title"],
            company=job["company"],
            location=job["location"],
            description=job["description"],
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=500, detail=f"Cover letter generation failed: {exc}") from exc

    update_job_cover_letter(job_id, letter)
    notify_cover_letter_ready(job_title=job["title"], company=job["company"], job_id=job_id)
    return {"ok": True, "cover_letter": letter}


@app.patch("/jobs/{job_id}/status")
def patch_job_status(job_id: int, body: StatusUpdate):
    allowed = {"pending", "submitted", "failed", "flagged"}
    if body.status not in allowed:
        raise HTTPException(status_code=400, detail=f"Status must be one of: {allowed}")

    if not get_job(job_id):
        raise HTTPException(status_code=404, detail="Job not found")

    update_job_status(job_id, body.status)
    return {"ok": True, "status": body.status}


@app.post("/scraper/run")
def run_scraper():
    try:
        cfg = ScraperConfig.from_env()
        result = run_scraper_sync(cfg)
        return {"ok": True, "result": result}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=500, detail=f"Scraper run failed: {exc}") from exc
