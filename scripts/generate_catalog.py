#!/usr/bin/env python3
"""Generate a large starter game catalog from configured sources."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCES_PATH = ROOT / "data" / "sources.json"
OUTPUT_PATH = ROOT / "data" / "games.json"


def load_sources() -> list[dict]:
    with SOURCES_PATH.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def build_entries(sources: list[dict], count: int) -> list[dict]:
    entries: list[dict] = []
    category_cycle = [
        "arcade",
        "puzzle",
        "platformer",
        "strategy",
        "shooter",
        "sports",
        "idle",
        "misc",
    ]

    for idx in range(1, count + 1):
        source = sources[(idx - 1) % len(sources)]
        category = category_cycle[(idx - 1) % len(category_cycle)]
        entries.append(
            {
                "id": f"game-{idx:04d}",
                "title": f"Game {idx:04d}",
                "slug": f"game-{idx:04d}",
                "sourceId": source["id"],
                "sourceName": source["name"],
                "sourceUrl": source["url"],
                "category": category,
                "status": "pending-import",
                "tags": [category, "bulk-catalog"],
                "launchUrl": "",
                "notes": "Catalog placeholder. Replace with verified game metadata and launch URL."
            }
        )

    return entries


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate large game catalog JSON")
    parser.add_argument("--count", type=int, default=1500, help="Number of entries to generate")
    args = parser.parse_args()

    if args.count < 1:
        raise SystemExit("--count must be >= 1")

    sources = load_sources()
    if not sources:
        raise SystemExit("No sources found in data/sources.json")

    entries = build_entries(sources, args.count)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8") as fh:
        json.dump(entries, fh, ensure_ascii=False, indent=2)
        fh.write("\n")

    print(f"Wrote {len(entries)} entries to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
