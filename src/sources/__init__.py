from abc import ABC, abstractmethod

from models import Job


class JobSource(ABC):
    """Common interface every job source adapter must implement."""

    @abstractmethod
    def search(self, query: str, location: str) -> list[Job]:
        ...
