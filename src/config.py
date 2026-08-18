import json
from dataclasses import dataclass
from pathlib import Path

DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent.parent / "search_config.json"


@dataclass
class SearchConfig:
    queries: list[str]
    locations: list[str]


def load_search_config(path: Path = DEFAULT_CONFIG_PATH) -> SearchConfig:
    if not path.exists():
        raise FileNotFoundError(
            f"Search config not found at {path}. Create it with 'queries' "
            "and 'locations' lists (see search_config.json in the repo root)."
        )

    with path.open(encoding="utf-8") as f:
        data = json.load(f)

    queries = data.get("queries") or []
    locations = data.get("locations") or []

    if not queries or not locations:
        raise ValueError(f"{path} must define non-empty 'queries' and 'locations' lists.")

    return SearchConfig(queries=queries, locations=locations)
