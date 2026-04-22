# OMG Central

A lightweight, static game hub scaffold designed to scale to **1,000–2,500+ game records**.

## What this repo includes

- A menu-driven browser UI (search, source filter, status filter, pagination).
- A large starter catalog JSON file.
- Source tracking for upstream repositories.
- A repeatable catalog generator script.

## Quick start

```bash
python scripts/generate_catalog.py --count 1500
python -m http.server 8000
```

Then open: <http://localhost:8000>

## Project structure

- `index.html` — App shell and menu UI.
- `styles.css` — Styling for dashboard + game cards.
- `app.js` — Client-side filtering, pagination, and rendering logic.
- `data/sources.json` — Upstream sources to aggregate from.
- `data/games.json` — Generated catalog (large list).
- `scripts/generate_catalog.py` — Generator for catalog entries.

## Notes

This starter setup supports very large lists and is ready for plugging in real importers once upstream repo scraping/import is available in your environment.
