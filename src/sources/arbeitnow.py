from datetime import datetime, timezone

import requests

from models import Job
from sources import JobSource

API_URL = "https://www.arbeitnow.com/api/job-board-api"
REQUEST_TIMEOUT = 10
MAX_PAGES = 3


class ArbeitnowSource(JobSource):
    """Adapter for the Arbeitnow Job Board API.

    Arbeitnow has no server-side search/location filter, only pagination,
    so `query`/`location` matching is done client-side after fetching.
    """

    name = "arbeitnow"

    def search(self, query: str = "", location: str = "") -> list[Job]:
        jobs = [self._to_job(raw) for raw in self._fetch_all()]
        return [job for job in jobs if self._matches(job, query, location)]

    def _fetch_all(self) -> list[dict]:
        raw_jobs: list[dict] = []
        page = 1

        while page <= MAX_PAGES:
            response = requests.get(
                API_URL, params={"page": page}, timeout=REQUEST_TIMEOUT
            )
            response.raise_for_status()
            payload = response.json()

            page_jobs = payload.get("data", [])
            if not page_jobs:
                break
            raw_jobs.extend(page_jobs)

            if not payload.get("links", {}).get("next"):
                break
            page += 1

        return raw_jobs

    def _matches(self, job: Job, query: str, location: str) -> bool:
        if query:
            haystack = f"{job.title} {job.description or ''}".lower()
            terms = query.lower().split()
            if not all(term in haystack for term in terms):
                return False
        if location and location.lower() not in job.location.lower():
            return False
        return True

    def _to_job(self, raw: dict) -> Job:
        created_at = raw.get("created_at")
        published_at = (
            datetime.fromtimestamp(created_at, tz=timezone.utc)
            if created_at
            else None
        )
        return Job(
            title=raw.get("title", ""),
            company=raw.get("company_name", ""),
            location=raw.get("location", ""),
            description=raw.get("description"),
            url=raw.get("url", ""),
            source=self.name,
            published_at=published_at,
        )
