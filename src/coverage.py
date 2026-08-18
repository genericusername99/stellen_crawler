import argparse
import itertools
import json
import sys
from pathlib import Path

from config import DEFAULT_CONFIG_PATH, load_search_config
from crawl import default_sources, run_search
from dedup import dedup_key
from models import Job

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DEFAULT_REFERENCE_PATH = Path(__file__).resolve().parent.parent / "reference_jobs.json"


def load_reference_jobs(path: Path) -> list[Job]:
    if not path.exists():
        raise FileNotFoundError(
            f"Reference jobs file not found at {path}. Copy "
            "reference_jobs.example.json to reference_jobs.json and fill in "
            "jobs you found manually on a reference board such as Indeed."
        )

    with path.open(encoding="utf-8") as f:
        entries = json.load(f)

    return [
        Job(
            title=entry["title"],
            company=entry["company"],
            location=entry.get("location", ""),
            description=None,
            url=entry.get("url", ""),
            source="reference",
            published_at=None,
        )
        for entry in entries
    ]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Compare crawler results against a manually collected reference "
            "list (e.g. jobs found by hand on Indeed) to measure coverage."
        )
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
        "--reference",
        default=DEFAULT_REFERENCE_PATH,
        type=Path,
        help="Path to the reference jobs JSON file (default: reference_jobs.json)",
    )
    return parser.parse_args()


def resolve_search_terms(args: argparse.Namespace) -> list[tuple[str, str]]:
    if args.query or args.location:
        return [(args.query or "", args.location or "")]

    config = load_search_config(args.config)
    return list(itertools.product(config.queries, config.locations))


def print_stat(label: str, count: int) -> None:
    print(f"{label:<20}{count:>4} jobs")


def main() -> None:
    args = parse_args()
    search_terms = resolve_search_terms(args)

    crawler_jobs, _ = run_search(default_sources(), search_terms)
    reference_jobs = load_reference_jobs(args.reference)

    crawler_by_key = {dedup_key(job): job for job in crawler_jobs}
    reference_by_key = {dedup_key(job): job for job in reference_jobs}

    overlap = crawler_by_key.keys() & reference_by_key.keys()
    crawler_only = crawler_by_key.keys() - reference_by_key.keys()
    reference_only = reference_by_key.keys() - crawler_by_key.keys()

    print_stat("Reference board:", len(reference_by_key))
    print_stat("Crawler:", len(crawler_by_key))
    print_stat("Overlap:", len(overlap))
    print_stat("Reference only:", len(reference_only))
    print_stat("Crawler only:", len(crawler_only))

    if reference_only:
        print("\nMissed by the crawler (found on the reference board only):")
        for key in reference_only:
            job = reference_by_key[key]
            print(f"  - {job.title} — {job.company} ({job.location})")


if __name__ == "__main__":
    main()
