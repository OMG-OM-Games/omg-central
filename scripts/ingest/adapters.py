from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Iterable
from urllib.parse import quote
from urllib.request import Request, urlopen

from .models import GameEntry, normalize_title, title_hash

GITHUB_API = "https://api.github.com"


@dataclass(slots=True)
class SourceSpec:
    name: str
    repo: str
    subtree: str | None = None


class GithubSourceAdapter:
    """Base adapter for repositories hosted on GitHub."""

    spec: SourceSpec

    def __init__(self, spec: SourceSpec | None = None) -> None:
        if spec is not None:
            self.spec = spec
        if not hasattr(self, "spec"):
            raise ValueError("Adapter missing SourceSpec")

    def collect_entries(self) -> list[GameEntry]:
        branch = self._detect_default_branch()
        files = self._list_repo_tree(branch)
        if self.spec.subtree:
            files = [path for path in files if path.startswith(self.spec.subtree.rstrip("/") + "/")]

        entries: list[GameEntry] = []
        for path in files:
            entry = self._parse_path(path=path, branch=branch)
            if entry:
                entries.append(entry)
        return entries

    def _request_json(self, url: str) -> dict | list:
        req = Request(url, headers={"Accept": "application/vnd.github+json", "User-Agent": "omg-central-ingest"})
        with urlopen(req, timeout=30) as response:
            payload = response.read().decode("utf-8")
        return json.loads(payload)

    def _detect_default_branch(self) -> str:
        repo_url = f"{GITHUB_API}/repos/{self.spec.repo}"
        payload = self._request_json(repo_url)
        branch = payload.get("default_branch")
        if not branch:
            raise RuntimeError(f"Unable to determine default branch for {self.spec.repo}")
        return branch

    def _list_repo_tree(self, branch: str) -> list[str]:
        tree_url = f"{GITHUB_API}/repos/{self.spec.repo}/git/trees/{quote(branch)}?recursive=1"
        payload = self._request_json(tree_url)
        if not isinstance(payload, dict) or "tree" not in payload:
            raise RuntimeError(f"Unexpected tree payload for {self.spec.repo}")
        return [item["path"] for item in payload["tree"] if item.get("type") == "blob"]

    def _parse_path(self, path: str, branch: str) -> GameEntry | None:
        lower = path.lower()
        suffix = PurePosixPath(path).suffix

        if suffix not in {".html", ".htm", ".json", ".md"}:
            return None

        confidence = 0.25
        notes: list[str] = ["Path discovered via repository tree scan."]

        if re.search(r"(^|/)index\.(html|htm)$", lower):
            confidence += 0.4
            notes.append("Index HTML path suggests a playable page.")
        elif "/games/" in lower:
            confidence += 0.3
            notes.append("Path under /games/ subtree.")
        elif suffix == ".json":
            confidence += 0.2
            notes.append("JSON path may contain metadata.")

        path_parts = [part for part in PurePosixPath(path).parts if part not in {"games", "src", "public"}]
        if not path_parts:
            return None

        candidate = path_parts[-2] if path_parts[-1].startswith("index.") and len(path_parts) >= 2 else path_parts[-1]
        candidate = PurePosixPath(candidate).stem
        title = normalize_title(candidate)
        if not title:
            return None

        owner, repo_name = self.spec.repo.split("/", 1)
        encoded_path = quote(path)
        raw_url = f"https://raw.githubusercontent.com/{self.spec.repo}/{quote(branch)}/{encoded_path}"
        canonical_url = f"https://github.com/{self.spec.repo}/blob/{quote(branch)}/{encoded_path}"

        play_url = None
        if suffix in {".html", ".htm"}:
            rel = path.removeprefix(self.spec.subtree.rstrip("/") + "/") if self.spec.subtree else path
            rel = rel.removesuffix("index.html").removesuffix("index.htm")
            play_url = f"https://{owner}.github.io/{repo_name}/{rel}".rstrip("/")
            confidence += 0.15
            notes.append("Derived GitHub Pages URL from HTML path.")

        return GameEntry(
            title=title,
            title_hash=title_hash(title),
            canonical_url=canonical_url,
            source_repo=self.spec.repo,
            source_path=path,
            raw_url=raw_url,
            play_url=play_url,
            source_confidence=round(min(confidence, 1.0), 2),
            parse_notes=notes,
            tags=[self.spec.name],
        )


class BubblsUgsAssetsAdapter(GithubSourceAdapter):
    spec = SourceSpec(name="bubbls_ugs_assets", repo="bubbls/UGS-Assets")


class NeruvyGamesAdapter(GithubSourceAdapter):
    spec = SourceSpec(name="neruvy_games", repo="Neruvy/neruvy-games", subtree="games")


class NeruvyWebPortAdapter(GithubSourceAdapter):
    spec = SourceSpec(name="neruvy_web_port", repo="Neruvy/web-port")


class GnMathAssetsAdapter(GithubSourceAdapter):
    spec = SourceSpec(name="gn_math_assets", repo="gn-math/assets")


class ShartshrekWebPortAdapter(GithubSourceAdapter):
    spec = SourceSpec(name="shartshrek_web_port", repo="shartshrek/web-port")


class GenizyWebPortAdapter(GithubSourceAdapter):
    spec = SourceSpec(name="genizy_web_port", repo="genizy/web-port")


class NeruvyDuckmathAdapter(GithubSourceAdapter):
    spec = SourceSpec(name="neruvy_duckmath", repo="Neruvy/duckmath")


class Mathtut0r1ngSiteAdapter(GithubSourceAdapter):
    spec = SourceSpec(name="mathtut0r1ng_site", repo="mathtut0r1ng/mathtut0r1ng.github.io")


class Mathtut0r1ngAssetsBackupAdapter(GithubSourceAdapter):
    spec = SourceSpec(name="mathtut0r1ng_assets_backup", repo="mathtut0r1ng/assets-backup")


def build_all_adapters() -> list[GithubSourceAdapter]:
    return [
        BubblsUgsAssetsAdapter(),
        NeruvyGamesAdapter(),
        NeruvyWebPortAdapter(),
        GnMathAssetsAdapter(),
        ShartshrekWebPortAdapter(),
        GenizyWebPortAdapter(),
        NeruvyDuckmathAdapter(),
        Mathtut0r1ngSiteAdapter(),
        Mathtut0r1ngAssetsBackupAdapter(),
    ]


def dedupe_entries(entries: Iterable[GameEntry]) -> list[GameEntry]:
    deduped: list[GameEntry] = []
    seen: set[tuple[str, str]] = set()

    for entry in entries:
        key = (entry.canonical_url, entry.title_hash)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(entry)

    deduped.sort(key=lambda item: (item.title.lower(), item.source_repo.lower(), item.source_path.lower()))
    return deduped
