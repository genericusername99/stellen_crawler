from dataclasses import dataclass
from datetime import datetime


@dataclass
class Job:
    title: str
    company: str
    location: str
    description: str | None
    url: str
    source: str
    published_at: datetime | None
