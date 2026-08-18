# stellen-crawler

Job crawler / aggregator for German IT job openings. Searches multiple job
sources, normalizes results into a common `Job` model, and (eventually)
deduplicates, filters, and ranks them.

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
```

## Usage

```powershell
python src\main.py --query "Werkstudent Informatik" --location "Tübingen"
```

## Status

- Arbeitnow source implemented (`src/sources/arbeitnow.py`).
- Adzuna, deduplication, persistence, scoring: not yet implemented.

See `Context.txt` for the full project plan and milestones.
