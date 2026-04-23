#!/usr/bin/env python3
"""Build a unified games catalog from multiple GitHub repositories."""

from __future__ import annotations

import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SOURCES_FILE = ROOT / "data" / "sources.json"
OUTPUT_FILE = ROOT / "data" / "games.json"
MANUAL_FILE = ROOT / "data" / "manual_games.json"
REPO_LIST_FILE = ROOT / "data" / "repo_lists.json"

GAME_FILE_RE = re.compile(r"(index|game|play|main)\.html?$", re.IGNORECASE)
HTML_EXT = (".html", ".htm")


@dataclass(frozen=True)
class Source:
    owner: str
    repo: str
    paths: list[str]


class GitHubClient:
    def __init__(self, token: str | None = None) -> None:
        self.token = token

    def _request_json(self, url: str) -> Any:
        req = urllib.request.Request(url)
        req.add_header("Accept", "application/vnd.github+json")
        req.add_header("User-Agent", "omg-central-catalog-builder")
        if self.token:
            req.add_header("Authorization", f"Bearer {self.token}")

        try:
            with urllib.request.urlopen(req) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as err:
            body = err.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"GitHub request failed ({err.code}) for {url}: {body}") from err

    def get_repo_meta(self, owner: str, repo: str) -> dict[str, Any]:
        return self._request_json(f"https://api.github.com/repos/{owner}/{repo}")

    def get_recursive_tree(self, owner: str, repo: str, branch: str) -> dict[str, Any]:
        encoded_branch = urllib.parse.quote(branch, safe="")
        url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{encoded_branch}?recursive=1"
        return self._request_json(url)





def parse_repo_url(url: str) -> tuple[str, str, str | None]:
    parsed = urllib.parse.urlparse(url)
    parts = [p for p in parsed.path.split("/") if p]
    if len(parts) < 2:
        raise ValueError(f"Invalid GitHub repo URL: {url}")
    owner, repo = parts[0], parts[1]
    scoped_path = None
    if len(parts) >= 5 and parts[2] == "tree":
        scoped_path = "/".join(parts[4:])
    return owner, repo, scoped_path


def load_repo_list_entries() -> tuple[list[Source], list[dict[str, Any]]]:
    if not REPO_LIST_FILE.exists():
        return [], []

    raw = json.loads(REPO_LIST_FILE.read_text(encoding="utf-8"))
    dynamic_sources: list[Source] = []
    repo_entries: list[dict[str, Any]] = []

    for idx, repo_url in enumerate(raw):
        try:
            owner, repo, scoped_path = parse_repo_url(repo_url)
        except ValueError:
            continue

        paths = [scoped_path] if scoped_path else ["."]
        dynamic_sources.append(Source(owner=owner, repo=repo, paths=paths))

        repo_entries.append(
            {
                "id": f"repo_list_{idx}_{owner}_{repo}",
                "title": f"Collection: {owner}/{repo}",
                "owner": owner,
                "repo": repo,
                "source": "repo-lists",
                "path": scoped_path or ".",
                "default_branch": "unknown",
                "url": repo_url,
                "fallback_urls": [repo_url],
                "kind": "repo_collection",
            }
        )

    return dynamic_sources, repo_entries

def load_sources(path: Path) -> list[Source]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    return [Source(owner=s["owner"], repo=s["repo"], paths=s.get("paths", ["."])) for s in raw]


def normalize_title(path: str) -> str:
    stem = Path(path).stem
    stem = re.sub(r"[-_]+", " ", stem)
    return stem.strip().title() or "Untitled Game"


def eligible_html(path: str) -> bool:
    p = path.lower()
    if not p.endswith(HTML_EXT):
        return False
    if any(x in p for x in ("/node_modules/", "/dist/", "/build/", "/vendor/")):
        return False
    filename = Path(p).name
    return filename == "index.html" or GAME_FILE_RE.search(filename) is not None


def path_in_scope(path: str, scopes: list[str]) -> bool:
    for scope in scopes:
        if scope in (".", ""):
            return True
        scope_norm = scope.strip("/") + "/"
        if path.startswith(scope_norm):
            return True
    return False


def page_candidate_urls(owner: str, repo: str, default_branch: str, path: str) -> list[str]:
    path_clean = path.lstrip("/")
    return [
        f"https://{owner}.github.io/{repo}/{path_clean}",
        f"https://raw.githubusercontent.com/{owner}/{repo}/{default_branch}/{path_clean}",
    ]


def build_catalog(sources: list[Source], client: GitHubClient) -> list[dict[str, Any]]:
    catalog: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()

    for src in sources:
        slug = f"{src.owner}/{src.repo}"
        print(f"Scanning {slug} ...", file=sys.stderr)
        try:
            meta = client.get_repo_meta(src.owner, src.repo)
            default_branch = meta.get("default_branch") or "main"
            tree = client.get_recursive_tree(src.owner, src.repo, default_branch)
        except Exception as err:
            print(f"Warning: failed to scan {slug}: {err}", file=sys.stderr)
            continue

        truncated = bool(tree.get("truncated"))

        if truncated:
            print(f"Warning: tree for {slug} is truncated; results may be incomplete.", file=sys.stderr)

        for node in tree.get("tree", []):
            if node.get("type") != "blob":
                continue
            path = node.get("path", "")
            if not path or not path_in_scope(path, src.paths) or not eligible_html(path):
                continue

            key = (src.owner, src.repo, path)
            if key in seen:
                continue
            seen.add(key)

            urls = page_candidate_urls(src.owner, src.repo, default_branch, path)
            catalog.append(
                {
                    "id": f"{src.owner}_{src.repo}_{path}".replace("/", "_").replace(".", "_"),
                    "title": normalize_title(path),
                    "owner": src.owner,
                    "repo": src.repo,
                    "source": slug,
                    "path": path,
                    "default_branch": default_branch,
                    "url": urls[0],
                    "fallback_urls": urls,
                }
            )

        time.sleep(0.15)

    catalog.sort(key=lambda g: (g["source"].lower(), g["title"].lower(), g["path"].lower()))
    return catalog


def load_manual_games() -> list[dict[str, Any]]:
    if not MANUAL_FILE.exists():
        return []
    raw = json.loads(MANUAL_FILE.read_text(encoding="utf-8"))
    games: list[dict[str, Any]] = []
    for i, item in enumerate(raw):
        url = item.get("url")
        if not url:
            continue
        title = item.get("title") or f"Manual Game {i+1}"
        source = item.get("source") or "manual"
        path = item.get("path") or "manual"
        games.append({
            "id": f"manual_{i}_{title}".replace(" ", "_").replace("/", "_"),
            "title": title,
            "owner": item.get("owner", "manual"),
            "repo": item.get("repo", "manual"),
            "source": source,
            "path": path,
            "default_branch": item.get("default_branch", "manual"),
            "url": url,
            "fallback_urls": item.get("fallback_urls", [url]),
        })
    return games

def main() -> None:
    if not SOURCES_FILE.exists():
        raise SystemExit(f"Missing sources file: {SOURCES_FILE}")

    sources = load_sources(SOURCES_FILE)
    dynamic_sources, repo_entries = load_repo_list_entries()
    if dynamic_sources:
        sources = dynamic_sources
    token = os.getenv("GITHUB_TOKEN")
    client = GitHubClient(token=token)

    catalog = build_catalog(sources, client)
    catalog.extend(repo_entries)
    catalog.extend(load_manual_games())

    payload = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "source_count": len(sources),
        "game_count": len(catalog),
        "games": catalog,
    }

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print(f"Wrote {len(catalog)} games to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
