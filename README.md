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

## Scoring configuration

Edit `scoring_config.json` by hand to change how jobs are ranked. Each rule
adds/subtracts its weight if the (case-insensitive) keyword appears in the
job's title or description; jobs are sorted by total score, highest first.
Set `"min_score"` to a number to drop jobs below that score, or `null` to
keep everything:

```json
{
  "min_score": null,
  "rules": [
    {"keyword": "Werkstudent", "weight": 5},
    {"keyword": "Senior", "weight": -5}
  ]
}
```

## Usage

```powershell
python src\main.py
python src\main.py --query "Werkstudent Informatik" --location "Tübingen"
python src\main.py --config path\to\other_config.json
python src\main.py --scoring-config path\to\other_scoring.json
```

## Coverage measurement

There's no legitimate API for scraping Indeed directly, so coverage is
measured against a reference list you collect by hand: search a board like
Indeed yourself, copy `reference_jobs.example.json` to `reference_jobs.json`
(git-ignored, since it's a one-off manual snapshot that goes stale
immediately), and fill in the title/company/location of what you found:

```json
[
  {"title": "Werkstudent Softwareentwicklung (m/w/d)", "company": "Example GmbH", "location": "Stuttgart"}
]
```

Then run:

```powershell
.\.venv\Scripts\python.exe src\main.py --query "Werkstudent Informatik" --location "Tübingen"
```

This runs the crawler over the same query/location and reports overlap,
crawler-only, and reference-only counts, plus the actual titles the crawler
missed — useful for judging whether a new source is worth adding.

## Status

- Sources implemented: Arbeitnow, Adzuna, Bundesagentur für Arbeit (`src/sources/`).
- Deduplication across sources (`src/dedup.py`), SQLite persistence with
  new-job detection (`src/db.py`, `data/jobs.db`), configurable keyword-based
  scoring/filtering (`src/scoring.py`), and coverage measurement against a
  manually collected reference list (`src/coverage.py`) are all implemented.
- Fuzzy (non-exact) deduplication is the main thing not yet implemented —
  matching is still exact on normalized company+title+location.

See `Context.txt` for the full project plan and milestones.
