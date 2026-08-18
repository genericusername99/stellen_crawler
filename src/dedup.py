import re

from models import Job


def _normalize(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^\w\s]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _normalize_location(text: str) -> str:
    # Sources disagree on specificity, e.g. Adzuna returns "Stuttgart,
    # Baden-Württemberg" while Arbeitnow returns just "Stuttgart". Compare
    # only the primary component so the same city still matches.
    primary = text.split(",")[0]
    return _normalize(primary)


def _dedup_key(job: Job) -> tuple[str, str, str]:
    return (_normalize(job.company), _normalize(job.title), _normalize_location(job.location))


def deduplicate(jobs: list[Job]) -> list[Job]:
    """Merge jobs that look like the same vacancy across sources.

    Matches on normalized company + title + location rather than URL,
    since the same vacancy can have a different URL on every job board.
    """
    merged: dict[tuple[str, str, str], Job] = {}

    for job in jobs:
        key = _dedup_key(job)
        existing = merged.get(key)

        if existing is None:
            job.sources = [job.source]
            merged[key] = job
            continue

        if job.source not in existing.sources:
            existing.sources.append(job.source)
        if existing.description is None and job.description is not None:
            existing.description = job.description
        if existing.published_at is None and job.published_at is not None:
            existing.published_at = job.published_at

    return list(merged.values())
