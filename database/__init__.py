from database.db import (
    get_job,
    get_jobs,
    init_db,
    save_jobs,
    update_job_cover_letter,
    update_job_status,
)

__all__ = [
    "init_db",
    "save_jobs",
    "get_jobs",
    "get_job",
    "update_job_cover_letter",
    "update_job_status",
]
