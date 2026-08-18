import argparse
import sys

from models import Job
from sources.arbeitnow import ArbeitnowSource

sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Search for job vacancies across multiple sources."
    )
    parser.add_argument(
        "--query",
        default="Werkstudent Informatik",
        help="Search term, e.g. 'Werkstudent Informatik'",
    )
    parser.add_argument(
        "--location",
        default="Tübingen",
        help="Location to search in, e.g. 'Tübingen'",
    )
    return parser.parse_args()


def print_job(job: Job) -> None:
    published = job.published_at.strftime("%Y-%m-%d") if job.published_at else "unknown"
    print(f"[{job.source}] {job.title} — {job.company} ({job.location})")
    print(f"  published: {published}")
    print(f"  url: {job.url}")
    print()


def main() -> None:
    args = parse_args()
    sources = [ArbeitnowSource()]

    jobs: list[Job] = []
    for source in sources:
        try:
            jobs.extend(source.search(args.query, args.location))
        except Exception as exc:
            print(f"[{source.name}] source failed: {exc}")

    print(f"Found {len(jobs)} job(s) for query={args.query!r} location={args.location!r}\n")
    for job in jobs:
        print_job(job)


if __name__ == "__main__":
    main()
