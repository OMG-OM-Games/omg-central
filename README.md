# omg-central

Catalog automation and moderation pipeline for game ingestion.

## What this includes

- Scheduled GitHub Action to rerun ingestion + validation daily and weekly.
- Generated pipeline outputs:
  - `catalog.json` (published entries)
  - `review-queue.json` (manual review)
  - `diff-report.md` (added/removed/changed)
- Manual curation controls in `data/manual-overrides.json`:
  - force-hide games
  - title/genre/thumbnail fixes
  - featured game pinning
- App changelog page at `app/changelog.html` driven by `app/changelog.json`.

## Local run

```bash
python scripts/run_ingestion.py
```

The script ingests `data/raw-games.json`, applies `data/manual-overrides.json`, validates fields, and writes the outputs.
