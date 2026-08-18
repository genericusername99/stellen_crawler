from dataclasses import dataclass, field
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
    sources: list[str] = field(default_factory=list)
