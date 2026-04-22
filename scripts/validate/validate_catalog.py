#!/usr/bin/env python3
"""Compliance validation for imported game catalog data."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from ipaddress import ip_address
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

DEFAULT_ALLOWLIST_HOSTS = {
    "archive.org",
    "github.com",
    "itch.io",
    "opengameart.org",
    "raw.githubusercontent.com",
}

ALLOWED_LICENSE_STATUS = {"allowed", "restricted", "blocked", "unknown", "missing"}
ALLOWED_REDISTRIBUTION_RIGHTS = {"allowed", "restricted", "unknown", "missing"}
REQUIRED_FIELDS = {
    "id",
    "title",
    "source_url",
    "source_license",
    "source_license_status",
    "attribution_required",
    "redistribution_rights",
}

SUSPICIOUS_PATTERNS = (
    re.compile(r"(?:^|[.\-])(malware|phish|trojan|virus)(?:[.\-]|$)", re.IGNORECASE),
    re.compile(r"(?:tinyurl|bit\.ly|t\.co|goo\.gl)", re.IGNORECASE),
)


@dataclass
class ValidationIssue:
    severity: str
    game_id: str
    message: str


@dataclass
class ValidationResult:
    issues: list[ValidationIssue]
    total_games: int
    blocked_games: set[str]

    @property
    def has_errors(self) -> bool:
        return any(issue.severity == "error" for issue in self.issues)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "catalog",
        type=Path,
        nargs="?",
        default=Path("data/catalog/imported-games.json"),
        help="Path to imported games JSON catalog.",
    )
    parser.add_argument(
        "--report-path",
        type=Path,
        default=Path("data/reports/compliance-report.md"),
        help="Path to write compliance markdown report.",
    )
    parser.add_argument(
        "--allow-host",
        action="append",
        default=[],
        help="Additional allowed source host/domain. May be passed multiple times.",
    )
    return parser.parse_args()


def load_catalog(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict) and "games" in payload:
        games = payload["games"]
    elif isinstance(payload, list):
        games = payload
    else:
        raise ValueError("Catalog must be a list or an object with a 'games' list.")

    if not isinstance(games, list):
        raise ValueError("Catalog 'games' must be a list.")

    normalized: list[dict[str, Any]] = []
    for item in games:
        if not isinstance(item, dict):
            raise ValueError("Each game entry must be an object.")
        normalized.append(item)
    return normalized


def is_allowed_host(host: str, allowlist: set[str]) -> bool:
    return any(host == domain or host.endswith(f".{domain}") for domain in allowlist)


def host_is_suspicious(host: str) -> bool:
    if host.startswith("xn--"):
        return True
    for pattern in SUSPICIOUS_PATTERNS:
        if pattern.search(host):
            return True
    try:
        ip_address(host)
        return True
    except ValueError:
        return False


def validate_catalog(games: list[dict[str, Any]], allowlist: set[str]) -> ValidationResult:
    issues: list[ValidationIssue] = []
    seen_ids: dict[str, int] = {}
    blocked_games: set[str] = set()

    for idx, game in enumerate(games):
        game_id = str(game.get("id", f"__index_{idx}"))

        missing_fields = sorted(field for field in REQUIRED_FIELDS if field not in game)
        if missing_fields:
            issues.append(
                ValidationIssue(
                    severity="error",
                    game_id=game_id,
                    message=f"Missing required field(s): {', '.join(missing_fields)}",
                )
            )
            blocked_games.add(game_id)

        if game_id in seen_ids:
            issues.append(
                ValidationIssue(
                    severity="error",
                    game_id=game_id,
                    message=f"Duplicate id found (first seen at entry #{seen_ids[game_id]}).",
                )
            )
            blocked_games.add(game_id)
        else:
            seen_ids[game_id] = idx

        source_license = str(game.get("source_license", "")).strip()
        if not source_license:
            issues.append(
                ValidationIssue(
                    severity="error",
                    game_id=game_id,
                    message="source_license must not be empty.",
                )
            )
            blocked_games.add(game_id)

        if "attribution_required" in game and not isinstance(game["attribution_required"], bool):
            issues.append(
                ValidationIssue(
                    severity="error",
                    game_id=game_id,
                    message="attribution_required must be a boolean.",
                )
            )
            blocked_games.add(game_id)

        license_status = str(game.get("source_license_status", "")).lower().strip()
        if license_status not in ALLOWED_LICENSE_STATUS:
            issues.append(
                ValidationIssue(
                    severity="error",
                    game_id=game_id,
                    message=(
                        "source_license_status must be one of: "
                        f"{', '.join(sorted(ALLOWED_LICENSE_STATUS))}."
                    ),
                )
            )
            blocked_games.add(game_id)
        elif license_status == "blocked":
            issues.append(
                ValidationIssue(
                    severity="error",
                    game_id=game_id,
                    message="Blocked license status is not permitted in catalog build.",
                )
            )
            blocked_games.add(game_id)

        redistribution_rights = str(game.get("redistribution_rights", "")).lower().strip()
        if redistribution_rights not in ALLOWED_REDISTRIBUTION_RIGHTS:
            issues.append(
                ValidationIssue(
                    severity="error",
                    game_id=game_id,
                    message=(
                        "redistribution_rights must be one of: "
                        f"{', '.join(sorted(ALLOWED_REDISTRIBUTION_RIGHTS))}."
                    ),
                )
            )
            blocked_games.add(game_id)
        elif redistribution_rights in {"unknown", "missing"}:
            if not bool(game.get("manual_approval", False)):
                issues.append(
                    ValidationIssue(
                        severity="error",
                        game_id=game_id,
                        message=(
                            "redistribution_rights is unknown/missing and requires "
                            "manual_approval=true."
                        ),
                    )
                )
                blocked_games.add(game_id)

        source_url = str(game.get("source_url", "")).strip()
        try:
            parsed = urlparse(source_url)
            host = (parsed.hostname or "").lower()
            if parsed.scheme not in {"https"}:
                issues.append(
                    ValidationIssue(
                        severity="error",
                        game_id=game_id,
                        message="source_url must use https.",
                    )
                )
                blocked_games.add(game_id)
            elif not host:
                issues.append(
                    ValidationIssue(
                        severity="error",
                        game_id=game_id,
                        message="source_url must include a valid host.",
                    )
                )
                blocked_games.add(game_id)
            else:
                if not is_allowed_host(host, allowlist):
                    issues.append(
                        ValidationIssue(
                            severity="error",
                            game_id=game_id,
                            message=f"source_url host '{host}' is not allowlisted.",
                        )
                    )
                    blocked_games.add(game_id)
                if host_is_suspicious(host):
                    issues.append(
                        ValidationIssue(
                            severity="error",
                            game_id=game_id,
                            message=f"source_url host '{host}' is suspicious/malicious.",
                        )
                    )
                    blocked_games.add(game_id)
                if parsed.username or parsed.password or "@" in parsed.netloc:
                    issues.append(
                        ValidationIssue(
                            severity="error",
                            game_id=game_id,
                            message="source_url must not include userinfo credentials.",
                        )
                    )
                    blocked_games.add(game_id)
        except Exception as exc:
            issues.append(
                ValidationIssue(
                    severity="error",
                    game_id=game_id,
                    message=f"Invalid source_url: {exc}",
                )
            )
            blocked_games.add(game_id)

    return ValidationResult(issues=issues, total_games=len(games), blocked_games=blocked_games)


def write_report(path: Path, result: ValidationResult) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")

    lines = [
        "# Compliance Report",
        "",
        f"Generated at: {now}",
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
        f"| Total entries scanned | {result.total_games} |",
        f"| Total issues | {len(result.issues)} |",
        f"| Blocked entries | {len(result.blocked_games)} |",
        "",
        "## Issues",
        "",
    ]

    if not result.issues:
        lines.append("No compliance issues found.")
    else:
        lines.extend([
            "| Severity | Game ID | Message |",
            "| --- | --- | --- |",
        ])
        for issue in result.issues:
            message = issue.message.replace("|", "\\|")
            lines.append(f"| {issue.severity} | {issue.game_id} | {message} |")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    allowlist = {host.lower().strip() for host in DEFAULT_ALLOWLIST_HOSTS}
    allowlist.update(host.lower().strip() for host in args.allow_host if host.strip())

    try:
        games = load_catalog(args.catalog)
    except Exception as exc:
        print(f"Catalog read failure: {exc}", file=sys.stderr)
        return 2

    result = validate_catalog(games, allowlist)
    write_report(args.report_path, result)

    if result.has_errors:
        print(
            f"Compliance validation failed with {len(result.issues)} issue(s). "
            f"See {args.report_path} for details.",
            file=sys.stderr,
        )
        return 1

    print(f"Compliance validation passed ({result.total_games} entries).")
    print(f"Report written to {args.report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
