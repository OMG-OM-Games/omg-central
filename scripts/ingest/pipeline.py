from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from .adapters import build_all_adapters, dedupe_entries

ROOT = Path(__file__).resolve().parents[2]
OUT_PATH = ROOT / "data" / "games" / "catalog.json"


def run_pipeline() -> dict:
    collected = []
    errors: list[dict[str, str]] = []

    for adapter in build_all_adapters():
        try:
            collected.extend(adapter.collect_entries())
        except Exception as exc:  # noqa: BLE001 - keep pipeline resilient for manual review queue
            errors.append({"source": adapter.spec.repo, "error": str(exc)})

    deduped = dedupe_entries(collected)

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_entries": len(deduped),
        "sources_requested": [adapter.spec.repo for adapter in build_all_adapters()],
        "source_errors": errors,
        "entries": [asdict(entry) for entry in deduped],
    }
    return payload


def write_catalog(payload: dict) -> None:
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    result = run_pipeline()
    write_catalog(result)
    print(f"Wrote {result['total_entries']} entries to {OUT_PATH}")
