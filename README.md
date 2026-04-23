# OMG Central

A lightweight game hub that can index **1,000+ browser games** by aggregating game files from multiple GitHub repositories.

## What this repo includes

- A simple web UI with:
  - source/repo filter
  - text search
  - sortable game list
  - embedded game preview (iframe)
- A catalog builder script that scans configured GitHub repos and generates `data/games.json`.
- Seed sources based on your requested repositories.

## Quick start

1. Build the catalog:

```bash
python3 scripts/fetch_games.py
```

2. Serve locally:

```bash
python3 -m http.server 8080
```

3. Open:

- http://localhost:8080

## Add more repositories

Edit `data/sources.json` and add entries:

```json
{
  "owner": "example-owner",
  "repo": "example-repo",
  "paths": ["games", "projects"]
}
```

Then rerun:

```bash
python3 scripts/fetch_games.py
```

## Notes on scale

- The script uses the GitHub API tree endpoint and can process large repositories quickly.
- Public unauthenticated API requests are rate-limited.
- Set `GITHUB_TOKEN` for higher limits:

```bash
export GITHUB_TOKEN=ghp_xxx
python3 scripts/fetch_games.py
```

## Generated output

- `data/games.json` contains a normalized list of game entries:
  - title
  - source repo
  - path
  - playable URL candidates


## Integrating raw repo lists

If you have a plain list of GitHub URLs (including `tree/...` links), put them in `data/repo_lists.json`.

The builder will:
- treat those URLs as source repos to scan
- auto-create "Collection" entries in the UI so each repo link is still visible/clickable even if scanning fails

This is useful when importing a very large list and you still want immediate integration before full indexing finishes.


### Embedding behavior for repo-list entries

For each URL in `repo_lists.json`, the builder now generates multiple iframe URL candidates (GitHub Pages, raw.githack, jsDelivr, and the original repo URL).

In the UI, use **Try next embed URL** to cycle candidates until one loads for that repo/game.
