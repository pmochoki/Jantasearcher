from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from scraper.models import ScrapedJob

DB_PATH = Path(__file__).resolve().parents[1] / "database" / "jobdragon.db"


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                company TEXT NOT NULL,
                location TEXT NOT NULL,
                description TEXT NOT NULL,
                linkedin_url TEXT NOT NULL,
                external_apply_url TEXT NOT NULL,
                apply_url TEXT NOT NULL UNIQUE,
                is_easy_apply INTEGER NOT NULL DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'pending',
                cover_letter TEXT,
                scraped_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                applied_at DATETIME
            )
            """
        )
        _migrate_schema(conn)
        conn.commit()


def _migrate_schema(conn: sqlite3.Connection) -> None:
    columns = {row[1] for row in conn.execute("PRAGMA table_info(jobs)")}
    migrations: list[tuple[str, str]] = [
        ("linkedin_url", "ALTER TABLE jobs ADD COLUMN linkedin_url TEXT"),
        ("external_apply_url", "ALTER TABLE jobs ADD COLUMN external_apply_url TEXT"),
        ("cover_letter", "ALTER TABLE jobs ADD COLUMN cover_letter TEXT"),
    ]
    for column, sql in migrations:
        if column not in columns:
            conn.execute(sql)

    conn.execute(
        """
        UPDATE jobs
        SET linkedin_url = apply_url
        WHERE linkedin_url IS NULL OR linkedin_url = ''
        """
    )
    conn.execute(
        """
        UPDATE jobs
        SET external_apply_url = apply_url
        WHERE external_apply_url IS NULL OR external_apply_url = ''
        """
    )


def save_jobs(jobs: list[ScrapedJob]) -> int:
    if not jobs:
        return 0

    inserted = 0
    with _connect() as conn:
        for job in jobs:
            apply_url = job.external_apply_url or job.linkedin_url
            cur = conn.execute(
                """
                INSERT OR IGNORE INTO jobs
                    (title, company, location, description, linkedin_url,
                     external_apply_url, apply_url, is_easy_apply)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    job.title,
                    job.company,
                    job.location,
                    job.description,
                    job.linkedin_url,
                    job.external_apply_url,
                    apply_url,
                    int(job.is_easy_apply),
                ),
            )
            if cur.rowcount > 0:
                inserted += 1
        conn.commit()
    return inserted


def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    return dict(row)


def get_jobs(
    *,
    external_only: bool = True,
    status: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    clauses = ["1=1"]
    params: list[Any] = []

    if external_only:
        clauses.append("is_easy_apply = 0")
        clauses.append("external_apply_url != ''")
    if status:
        clauses.append("status = ?")
        params.append(status)

    params.append(limit)
    query = f"""
        SELECT * FROM jobs
        WHERE {' AND '.join(clauses)}
        ORDER BY scraped_at DESC
        LIMIT ?
    """
    with _connect() as conn:
        rows = conn.execute(query, params).fetchall()
    return [_row_to_dict(row) for row in rows]


def get_job(job_id: int) -> dict[str, Any] | None:
    with _connect() as conn:
        row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    return _row_to_dict(row) if row else None


def update_job_cover_letter(job_id: int, cover_letter: str) -> bool:
    with _connect() as conn:
        cur = conn.execute(
            "UPDATE jobs SET cover_letter = ? WHERE id = ?",
            (cover_letter, job_id),
        )
        conn.commit()
    return cur.rowcount > 0


def update_job_status(job_id: int, status: str) -> bool:
    with _connect() as conn:
        cur = conn.execute(
            """
            UPDATE jobs
            SET status = ?,
                applied_at = CASE WHEN ? = 'submitted' THEN CURRENT_TIMESTAMP ELSE applied_at END
            WHERE id = ?
            """,
            (status, status, job_id),
        )
        conn.commit()
    return cur.rowcount > 0


def get_stats() -> dict[str, int]:
    with _connect() as conn:
        total = conn.execute("SELECT COUNT(*) FROM jobs WHERE is_easy_apply = 0").fetchone()[0]
        submitted = conn.execute(
            "SELECT COUNT(*) FROM jobs WHERE status = 'submitted'"
        ).fetchone()[0]
        pending = conn.execute(
            "SELECT COUNT(*) FROM jobs WHERE status = 'pending' AND is_easy_apply = 0"
        ).fetchone()[0]
        failed = conn.execute(
            "SELECT COUNT(*) FROM jobs WHERE status = 'failed'"
        ).fetchone()[0]
        flagged = conn.execute(
            "SELECT COUNT(*) FROM jobs WHERE status = 'flagged'"
        ).fetchone()[0]
        with_cover = conn.execute(
            "SELECT COUNT(*) FROM jobs WHERE cover_letter IS NOT NULL AND cover_letter != ''"
        ).fetchone()[0]
    return {
        "found": total,
        "submitted": submitted,
        "pending": pending,
        "failed": failed,
        "flagged": flagged,
        "with_cover_letter": with_cover,
    }
