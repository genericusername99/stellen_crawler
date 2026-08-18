from dedup import deduplicate
from models import Job
from sources import JobSource
from sources.adzuna import AdzunaSource
from sources.arbeitnow import ArbeitnowSource
from sources.bundesagentur import BundesagenturSource


def default_sources() -> list[JobSource]:
    return [ArbeitnowSource(), AdzunaSource(), BundesagenturSource()]


def run_search(
    sources: list[JobSource], search_terms: list[tuple[str, str]]
) -> tuple[list[Job], int]:
    """Fetch, aggregate, and deduplicate jobs across all sources/search terms.

    Returns (deduplicated_jobs, raw_result_count).
    """
    jobs: list[Job] = []
    seen: set[tuple[str, str]] = set()

    for source in sources:
        for query, location in search_terms:
            try:
                for job in source.search(query, location):
                    key = (job.source, job.url)
                    if key in seen:
                        continue
                    seen.add(key)
                    jobs.append(job)
            except Exception as exc:
                print(
                    f"[{source.name}] search failed for "
                    f"query={query!r} location={location!r}: {exc}"
                )
                print(f"[{source.name}] skipping remaining searches for this source")
                break

    raw_count = len(jobs)
    return deduplicate(jobs), raw_count
