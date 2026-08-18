import argparse
import itertools
import sys
from pathlib import Path

import db
from config import DEFAULT_CONFIG_PATH, load_search_config
from dedup import deduplicate
from models import Job
from sources.adzuna import AdzunaSource
from sources.arbeitnow import ArbeitnowSource

sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Search for job vacancies across multiple sources."
    )
    parser.add_argument("--query", help="Single search term (overrides the config file)")
    parser.add_argument("--location", help="Single location (overrides the config file)")
    parser.add_argument(
        "--config",
        default=DEFAULT_CONFIG_PATH,
        type=Path,
        help="Path to the search config JSON file (default: search_config.json)",
    )
    parser.add_argument(
        "--db",
        default=db.DEFAULT_DB_PATH,
        type=Path,
        help="Path to the SQLite database file (default: data/jobs.db)",
    )
    return parser.parse_args()


def resolve_search_terms(args: argparse.Namespace) -> list[tuple[str, str]]:
    if args.query or args.location:
        return [(args.query or "", args.location or "")]

    config = load_search_config(args.config)
    return list(itertools.product(config.queries, config.locations))


def print_job(job: Job, is_new: bool) -> None:
    published = job.published_at.strftime("%Y-%m-%d") if job.published_at else "unknown"
    sources_label = "+".join(job.sources or [job.source])
    new_label = "NEW " if is_new else ""
    print(f"[{sources_label}] {new_label}{job.title} — {job.company} ({job.location})")
    print(f"  published: {published}")
    print(f"  url: {job.url}")
    print()


def main() -> None:
    args = parse_args()
    search_terms = resolve_search_terms(args)
    sources = [ArbeitnowSource(), AdzunaSource()]

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
    jobs = deduplicate(jobs)

    conn = db.connect(args.db)
    new_jobs, seen_again = db.upsert_jobs(conn, jobs)
    conn.close()
    new_keys = {(j.title, j.company, j.location) for j in new_jobs}

    print(
        f"Found {len(jobs)} unique job(s) (from {raw_count} raw result(s)) "
        f"across {len(search_terms)} search term(s) "
        f"— {len(new_jobs)} new, {len(seen_again)} already known\n"
    )
    for job in jobs:
        is_new = (job.title, job.company, job.location) in new_keys
        print_job(job, is_new)


if __name__ == "__main__":
    main()
