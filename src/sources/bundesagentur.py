from datetime import datetime

import requests

from models import Job
from sources import JobSource

API_URL = "https://rest.arbeitsagentur.de/jobboerse/jobsuche-service/pc/v6/jobs"
# Shared public key baked into the official Arbeitsagentur app, openly
# documented by the community (bundesAPI/jobsuche-api) for third-party use.
# Not a per-developer secret, so it lives here rather than in .env.
API_KEY = "jobboerse-jobsuche"
REQUEST_TIMEOUT = 10
RESULTS_PER_PAGE = 100
MAX_PAGES = 3


class BundesagenturSource(JobSource):
    name = "bundesagentur"

    def search(self, query: str = "", location: str = "") -> list[Job]:
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
        params = {"size": RESULTS_PER_PAGE, "page": page}
        if query:
            params["was"] = query
        if location:
            params["wo"] = location

        response = requests.get(
            API_URL,
            headers={"X-API-Key": API_KEY},
            params=params,
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        return response.json().get("ergebnisliste", [])

    def _to_job(self, raw: dict) -> Job:
        locations = raw.get("stellenlokationen") or [{}]
        address = locations[0].get("adresse") or {}

        published_at = None
        date_str = raw.get("datumErsteVeroeffentlichung")
        if date_str:
            try:
                published_at = datetime.fromisoformat(date_str)
            except ValueError:
                published_at = None

        reference = raw.get("referenznummer", "")
        url = raw.get("externeURL") or (
            f"https://www.arbeitsagentur.de/jobsuche/jobdetail/{reference}"
        )

        return Job(
            title=raw.get("stellenangebotsTitel", ""),
            company=raw.get("firma", ""),
            location=address.get("ort", ""),
            description=None,
            url=url,
            source=self.name,
            published_at=published_at,
        )
