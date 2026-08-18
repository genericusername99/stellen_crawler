# stellen-crawler

Job crawler / aggregator for German IT job openings. Searches multiple job
sources, normalizes results into a common `Job` model, and (eventually)
deduplicates, filters, and ranks them.

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
```

Adzuna requires API credentials. Register a free app at
https://developer.adzuna.com/, then copy `.env.example` to `.env` and fill
in `ADZUNA_APP_ID` / `ADZUNA_APP_KEY`. `.env` is git-ignored — never commit
it. Arbeitnow needs no credentials. The Bundesagentur für Arbeit source uses
a shared public API key (`jobboerse-jobsuche`, baked into the official
Arbeitsagentur app and documented by the community for third-party use), so
it also needs no per-user setup.

## Search configuration

Search terms and locations are not hardcoded — edit `search_config.json` by
hand to change what gets searched:

```json
{
  "queries": ["Werkstudent Informatik", "Cloud"],
  "locations": ["Tübingen", "Stuttgart"]
}
```

Every query is combined with every location across all sources. Running
`python src\main.py` with no flags reads this file. `--query`/`--location`
flags run a single one-off search instead, ignoring the config file.

## Usage

```powershell
python src\main.py
python src\main.py --query "Werkstudent Informatik" --location "Tübingen"
python src\main.py --config path\to\other_config.json
```

## Status

- Sources implemented: Arbeitnow, Adzuna, Bundesagentur für Arbeit (`src/sources/`).
- Deduplication across sources (`src/dedup.py`) and SQLite persistence with
  new-job detection (`src/db.py`, `data/jobs.db`) are implemented.
- Fuzzy (non-exact) deduplication, filtering/scoring, and coverage
  measurement against a reference job board: not yet implemented.

See `Context.txt` for the full project plan and milestones.
