import os
from datetime import datetime

import requests
from dotenv import load_dotenv

from models import Job
from sources import JobSource

API_URL = "https://api.adzuna.com/v1/api/jobs/de/search/{page}"
REQUEST_TIMEOUT = 10
RESULTS_PER_PAGE = 50
MAX_PAGES = 3


class AdzunaConfigError(RuntimeError):
    """Raised when Adzuna credentials are missing or rejected."""


class AdzunaSource(JobSource):
    name = "adzuna"

    def __init__(self) -> None:
        load_dotenv()
        self.app_id = os.getenv("ADZUNA_APP_ID")
        self.app_key = os.getenv("ADZUNA_APP_KEY")

    def search(self, query: str = "", location: str = "") -> list[Job]:
        if not self.app_id or not self.app_key:
            raise AdzunaConfigError(
                "ADZUNA_APP_ID / ADZUNA_APP_KEY not set (check your .env file)"
            )

        jobs: list[Job] = []
        for page in range(1, MAX_PAGES + 1):
            results = self._fetch_page(page, query, location)
            if not results:
                break
            jobs.extend(self._to_job(raw) for raw in results)
            if len(results) < RESULTS_PER_PAGE:
                break

        return jobs

    def _fetch_page(self, page: int, query: str, location: str) -> list[dict]:
        params = {
            "app_id": self.app_id,
            "app_key": self.app_key,
            "results_per_page": RESULTS_PER_PAGE,
            "content-type": "application/json",
        }
        if query:
            params["what"] = query
        if location:
            params["where"] = location

        response = requests.get(
            API_URL.format(page=page), params=params, timeout=REQUEST_TIMEOUT
        )
        if response.status_code == 401:
            raise AdzunaConfigError("Adzuna rejected the credentials (401 Unauthorized)")
        response.raise_for_status()
        return response.json().get("results", [])

    def _to_job(self, raw: dict) -> Job:
        published_at = None
        created = raw.get("created")
        if created:
            try:
                published_at = datetime.fromisoformat(created.replace("Z", "+00:00"))
            except ValueError:
                published_at = None

        return Job(
            title=raw.get("title", ""),
            company=(raw.get("company") or {}).get("display_name", ""),
            location=(raw.get("location") or {}).get("display_name", ""),
            description=raw.get("description"),
            url=raw.get("redirect_url", ""),
            source=self.name,
            published_at=published_at,
        )
