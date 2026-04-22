from __future__ import annotations

from dataclasses import asdict, dataclass, field
from hashlib import sha1
from typing import Any


@dataclass(slots=True)
class GameEntry:
    """Normalized catalog entry emitted by all source adapters."""

    title: str
    title_hash: str
    canonical_url: str
    source_repo: str
    source_path: str
    raw_url: str
    play_url: str | None = None
    description: str | None = None
    tags: list[str] = field(default_factory=list)
    source_confidence: float = 0.0
    parse_notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)



def normalize_title(value: str) -> str:
    cleaned = value.strip().replace("_", " ").replace("-", " ")
    return " ".join(chunk for chunk in cleaned.split() if chunk)



def title_hash(title: str) -> str:
    normalized = normalize_title(title).lower()
    return sha1(normalized.encode("utf-8")).hexdigest()
