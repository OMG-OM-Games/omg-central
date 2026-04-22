#!/usr/bin/env python3
"""Ingestion + validation pipeline for game catalog automation."""

from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
RAW_GAMES_PATH = DATA_DIR / "raw-games.json"
OVERRIDES_PATH = DATA_DIR / "manual-overrides.json"
LAST_CATALOG_PATH = DATA_DIR / ".last-catalog.json"
CATALOG_PATH = ROOT / "catalog.json"
REVIEW_QUEUE_PATH = ROOT / "review-queue.json"
DIFF_REPORT_PATH = ROOT / "diff-report.md"
CHANGELOG_JSON_PATH = ROOT / "app" / "changelog.json"
CHANGELOG_PAGE_PATH = ROOT / "app" / "changelog.html"


@dataclass
class ValidationIssue:
    game_id: str
    reasons: list[str]
    game: dict[str, Any]


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return deepcopy(default)
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def normalize_game(game: dict[str, Any]) -> dict[str, Any]:
    normalized = {
        "id": str(game.get("id", "")).strip(),
        "title": str(game.get("title", "")).strip(),
        "genres": game.get("genres", []),
        "thumbnail": str(game.get("thumbnail", "")).strip(),
        "ingested_at": game.get("ingested_at"),
    }
    if not isinstance(normalized["genres"], list):
        normalized["genres"] = []
    normalized["genres"] = [str(item).strip() for item in normalized["genres"] if str(item).strip()]
    return normalized


def apply_overrides(games: list[dict[str, Any]], overrides: dict[str, Any]) -> tuple[list[dict[str, Any]], set[str]]:
    force_hide = set(overrides.get("force_hide_game_ids", []))
    title_fixes = overrides.get("title_fixes", {})
    genre_fixes = overrides.get("genre_fixes", {})
    thumbnail_fixes = overrides.get("thumbnail_fixes", {})
    featured_ids = overrides.get("featured_game_ids", [])

    featured_positions = {game_id: idx + 1 for idx, game_id in enumerate(featured_ids)}

    updated: list[dict[str, Any]] = []
    for base in games:
        game = deepcopy(base)
        game_id = game["id"]
        if game_id in title_fixes:
            game["title"] = str(title_fixes[game_id]).strip()
        if game_id in genre_fixes and isinstance(genre_fixes[game_id], list):
            game["genres"] = [str(item).strip() for item in genre_fixes[game_id] if str(item).strip()]
        if game_id in thumbnail_fixes:
            game["thumbnail"] = str(thumbnail_fixes[game_id]).strip()

        game["is_featured"] = game_id in featured_positions
        if game["is_featured"]:
            game["featured_rank"] = featured_positions[game_id]

        updated.append(game)

    updated.sort(key=lambda item: (not item.get("is_featured", False), item.get("featured_rank", 9999), item["title"].lower()))
    return updated, force_hide


def validate_game(game: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    if not game["id"]:
        reasons.append("Missing required field: id")
    if not game["title"]:
        reasons.append("Missing required field: title")
    if not game["genres"]:
        reasons.append("Missing or empty required field: genres")
    if not game["thumbnail"]:
        reasons.append("Missing required field: thumbnail")
    return reasons


def generate_diff(previous: list[dict[str, Any]], current: list[dict[str, Any]]) -> dict[str, Any]:
    previous_by_id = {entry["id"]: entry for entry in previous}
    current_by_id = {entry["id"]: entry for entry in current}

    added = sorted([gid for gid in current_by_id if gid not in previous_by_id])
    removed = sorted([gid for gid in previous_by_id if gid not in current_by_id])

    changed: list[dict[str, Any]] = []
    for game_id in sorted(set(current_by_id).intersection(previous_by_id)):
        old = previous_by_id[game_id]
        new = current_by_id[game_id]
        if old != new:
            changed_fields = []
            for field in sorted(set(old).union(new)):
                if old.get(field) != new.get(field):
                    changed_fields.append(field)
            changed.append({"id": game_id, "fields": changed_fields})

    return {"added": added, "removed": removed, "changed": changed}


def write_diff_report(diff: dict[str, Any], current: list[dict[str, Any]]) -> None:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    title_by_id = {entry["id"]: entry["title"] for entry in current}

    lines = [
        "# Catalog Diff Report",
        "",
        f"Generated: {now}",
        "",
        f"## Added ({len(diff['added'])})",
    ]
    if diff["added"]:
        lines.extend([f"- `{game_id}` — {title_by_id.get(game_id, 'Unknown title')}" for game_id in diff["added"]])
    else:
        lines.append("- None")

    lines.extend(["", f"## Removed ({len(diff['removed'])})"])
    if diff["removed"]:
        lines.extend([f"- `{game_id}`" for game_id in diff["removed"]])
    else:
        lines.append("- None")

    lines.extend(["", f"## Changed ({len(diff['changed'])})"])
    if diff["changed"]:
        for entry in diff["changed"]:
            lines.append(f"- `{entry['id']}` — fields: {', '.join(entry['fields'])}")
    else:
        lines.append("- None")

    DIFF_REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_changelog_page(added_games: list[dict[str, Any]]) -> None:
    page = """<!doctype html>
<html lang=\"en\">
  <head>
    <meta charset=\"utf-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
    <title>Catalog Changelog</title>
    <style>
      body { font-family: system-ui, sans-serif; margin: 2rem; line-height: 1.5; }
      .card { border: 1px solid #ddd; border-radius: 10px; padding: 12px; margin-bottom: 10px; }
      img { width: 120px; border-radius: 8px; }
    </style>
  </head>
  <body>
    <h1>Recently Added Games</h1>
    <p>This page is generated by the ingestion automation.</p>
    <div id=\"entries\"></div>
    <script>
      fetch('./changelog.json')
        .then((res) => res.json())
        .then((payload) => {
          const wrap = document.getElementById('entries');
          if (!payload.added_games.length) {
            wrap.innerHTML = '<p>No new games in this run.</p>';
            return;
          }
          wrap.innerHTML = payload.added_games.map((game) => `\n            <article class=\"card\">\n              <h2>${game.title}</h2>\n              <p><strong>ID:</strong> ${game.id}</p>\n              <p><strong>Genres:</strong> ${game.genres.join(', ')}</p>\n              <img src=\"${game.thumbnail}\" alt=\"${game.title} thumbnail\" />\n            </article>`).join('');
        });
    </script>
  </body>
</html>
"""
    CHANGELOG_PAGE_PATH.write_text(page, encoding="utf-8")
    save_json(
        CHANGELOG_JSON_PATH,
        {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "added_games": added_games,
        },
    )


def main() -> None:
    raw_games = load_json(RAW_GAMES_PATH, default=[])
    overrides = load_json(OVERRIDES_PATH, default={})
    previous_catalog = load_json(LAST_CATALOG_PATH, default=[])

    normalized = [normalize_game(game) for game in raw_games]
    overridden, force_hide = apply_overrides(normalized, overrides)

    review_queue: list[dict[str, Any]] = []
    catalog: list[dict[str, Any]] = []

    for game in overridden:
        reasons = validate_game(game)
        if game["id"] in force_hide:
            reasons.append("force-hidden by manual override")

        if reasons:
            review_queue.append({
                "id": game["id"],
                "title": game.get("title", ""),
                "reasons": reasons,
                "candidate": game,
            })
        else:
            catalog.append(game)

    diff = generate_diff(previous_catalog, catalog)

    save_json(CATALOG_PATH, catalog)
    save_json(REVIEW_QUEUE_PATH, review_queue)
    write_diff_report(diff, catalog)
    save_json(LAST_CATALOG_PATH, catalog)

    added_games = [game for game in catalog if game["id"] in diff["added"]]
    write_changelog_page(added_games)

    print(f"Published catalog entries: {len(catalog)}")
    print(f"Review queue entries: {len(review_queue)}")
    print(f"Added: {len(diff['added'])}, Removed: {len(diff['removed'])}, Changed: {len(diff['changed'])}")


if __name__ == "__main__":
    main()
