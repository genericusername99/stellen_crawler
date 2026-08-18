import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from dedup import dedup_key
from models import Job

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "jobs.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    dedup_key TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    company TEXT NOT NULL,
    location TEXT NOT NULL,
    description TEXT,
    url TEXT NOT NULL,
    sources TEXT NOT NULL,
    published_at TEXT,
    first_seen TEXT NOT NULL,
    last_seen TEXT NOT NULL
)
"""


def connect(db_path: Path = DEFAULT_DB_PATH) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute(SCHEMA)
    return conn


def upsert_jobs(conn: sqlite3.Connection, jobs: list[Job]) -> tuple[list[Job], list[Job]]:
    """Insert jobs not seen before, refresh last_seen/sources for the rest.

    Returns (new_jobs, seen_again_jobs).
    """
    now = datetime.now(timezone.utc).isoformat()
    new_jobs: list[Job] = []
    seen_again: list[Job] = []

    for job in jobs:
        key = dedup_key(job)
        row = conn.execute(
            "SELECT sources FROM jobs WHERE dedup_key = ?", (key,)
        ).fetchone()
        job_sources = job.sources or [job.source]

        if row is None:
            conn.execute(
                """
                INSERT INTO jobs (
                    dedup_key, title, company, location, description, url,
                    sources, published_at, first_seen, last_seen
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    key,
                    job.title,
                    job.company,
                    job.location,
                    job.description,
                    job.url,
                    ",".join(job_sources),
                    job.published_at.isoformat() if job.published_at else None,
                    now,
                    now,
                ),
            )
            new_jobs.append(job)
        else:
            existing_sources = set(row[0].split(",")) if row[0] else set()
            merged_sources = sorted(existing_sources | set(job_sources))
            conn.execute(
                """
                UPDATE jobs
                SET last_seen = ?, sources = ?, description = COALESCE(description, ?)
                WHERE dedup_key = ?
                """,
                (now, ",".join(merged_sources), job.description, key),
            )
            seen_again.append(job)

    conn.commit()
    return new_jobs, seen_again
