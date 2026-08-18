import json
from dataclasses import dataclass
from pathlib import Path

from models import Job

DEFAULT_SCORING_CONFIG_PATH = Path(__file__).resolve().parent.parent / "scoring_config.json"


@dataclass
class ScoringRule:
    keyword: str
    weight: int


@dataclass
class ScoringConfig:
    rules: list[ScoringRule]
    min_score: int | None = None


def load_scoring_config(path: Path = DEFAULT_SCORING_CONFIG_PATH) -> ScoringConfig:
    if not path.exists():
        raise FileNotFoundError(
            f"Scoring config not found at {path}. Create it with a 'rules' list "
            "(see scoring_config.json in the repo root)."
        )

    with path.open(encoding="utf-8") as f:
        data = json.load(f)

    rules = [ScoringRule(r["keyword"], r["weight"]) for r in data.get("rules", [])]
    return ScoringConfig(rules=rules, min_score=data.get("min_score"))


def score_job(job: Job, config: ScoringConfig) -> int:
    haystack = f"{job.title} {job.description or ''}".lower()
    return sum(rule.weight for rule in config.rules if rule.keyword.lower() in haystack)


def apply_scoring(jobs: list[Job], config: ScoringConfig) -> list[Job]:
    """Score every job, drop anything below the configured minimum, sort by score."""
    for job in jobs:
        job.score = score_job(job, config)

    if config.min_score is not None:
        jobs = [job for job in jobs if job.score >= config.min_score]

    return sorted(jobs, key=lambda job: job.score, reverse=True)
