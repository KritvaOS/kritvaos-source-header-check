#!/usr/bin/env python3
#==============================================================================
# Copyright (c) 2026 KritvaOS
# SPDX-License-Identifier: Apache-2.0
#
# File        : check_source_headers.py
# Description : Validate KritvaOS source-file headers.
#
# Component   : Infrastructure
# Module      : Source Header Checker
# Layer       : Development
#
# Author      : KritvaOS Team
# Created     : 26-09-2026
#==============================================================================

from __future__ import annotations

import argparse
import fnmatch
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import yaml

FIELD_RE = re.compile(r"^\s*([A-Za-z][A-Za-z ]*?)\s*:\s*(.*?)\s*$")
SPDX_RE = re.compile(r"SPDX-License-Identifier:\s*Apache-2\.0\b")
COPYRIGHT_RE = re.compile(r"Copyright\s*\(c\)\s*2026\s+KritvaOS\b")
DATE_RE = re.compile(r"^\d{2}-\d{2}-\d{4}$")


@dataclass
class Rule:
    name: str
    style: str
    extensions: list[str]
    patterns: list[str]
    required_fields: list[str]
    shebang: str | None = None


def load_config(root: Path) -> dict:
    with (root / "config/source_header_check.yaml").open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def build_rules(config: dict) -> list[Rule]:
    return [
        Rule(
            r["name"],
            r["style"],
            r.get("extensions", []),
            r.get("patterns", []),
            r.get("required_fields", []),
            r.get("shebang"),
        )
        for r in config.get("rules", [])
    ]


def normalize_rel(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def is_excluded(rel: str, config: dict) -> bool:
    parts = rel.split("/")
    excluded_dirs = set(config.get("exclude", {}).get("directories", []))
    if any(part in excluded_dirs for part in parts[:-1]):
        return True

    filename = parts[-1]
    return any(
        fnmatch.fnmatch(rel, pattern) or fnmatch.fnmatch(filename, pattern)
        for pattern in config.get("exclude", {}).get("files", [])
    )


def matches_rule(rel: str, rule: Rule) -> bool:
    # Explicit patterns are checked before generic extension matching.
    if any(
        fnmatch.fnmatch(rel, pattern)
        or fnmatch.fnmatch(Path(rel).name, pattern)
        for pattern in rule.patterns
    ):
        return True

    return Path(rel).suffix.lower() in {x.lower() for x in rule.extensions}


def classify(rel: str, rules: list[Rule]) -> Rule | None:
    for rule in rules:
        if matches_rule(rel, rule):
            return rule
    return None


def strip_comment(line: str, style: str) -> str:
    s = line.strip()

    if style == "hash":
        return s[1:].strip() if s.startswith("#") else ""

    if style == "slash":
        if s.startswith("//"):
            return s[2:].strip()
        return s.strip("*/").strip()

    if style == "html":
        if s.startswith("<!--"):
            s = s[4:]
        if s.endswith("-->"):
            s = s[:-3]
        return s.strip()

    return s


def extract_header(
    text: str, style: str, shebang: str | None = None
) -> tuple[str, list[str], str | None]:
    """Extract only the leading contiguous header block."""

    lines = text.splitlines()
    if not lines:
        return "", [], "HEADER-008"

    index = 0

    if shebang == "optional" and lines[0].startswith("#!"):
        index = 1

    while index < len(lines) and not lines[index].strip():
        index += 1

    if index >= len(lines):
        return "", [], "HEADER-008"

    raw: list[str] = []

    if style == "html":
        if lines[index].lstrip().startswith("<?xml"):
            index += 1
            while index < len(lines) and not lines[index].strip():
                index += 1

        if index >= len(lines) or "<!--" not in lines[index]:
            return "", [], "HEADER-008"

        while index < len(lines):
            raw.append(lines[index])
            if "-->" in lines[index]:
                break
            index += 1

        if not raw or "-->" not in raw[-1]:
            return "", [], "HEADER-008"

    elif style == "slash":
        if lines[index].lstrip().startswith("//"):
            while index < len(lines) and lines[index].lstrip().startswith("//"):
                raw.append(lines[index])
                index += 1

        elif lines[index].lstrip().startswith("/*"):
            while index < len(lines):
                raw.append(lines[index])
                if "*/" in lines[index]:
                    break
                index += 1

            if not raw or "*/" not in raw[-1]:
                return "", [], "HEADER-008"

        else:
            return "", [], "HEADER-008"

    elif style == "hash":
        while index < len(lines) and lines[index].lstrip().startswith("#"):
            raw.append(lines[index])
            index += 1

        if not raw:
            return "", [], "HEADER-008"

    else:
        return "", [], "HEADER-008"

    normalized = [strip_comment(line, style).strip() for line in raw]
    return "\n".join(raw), normalized, None


def parse_fields(lines: list[str]) -> dict[str, str]:
    fields: dict[str, str] = {}

    for line in lines:
        line = line.strip()

        if not line or set(line) <= set("-=_*"):
            continue

        match = FIELD_RE.match(line)
        if match:
            fields[match.group(1).strip()] = match.group(2).strip()

    return fields


def validate(path: Path, rule: Rule, config: dict) -> list[tuple[str, str]]:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return [("HEADER-006", "file is not valid UTF-8")]

    header, normalized, extraction_error = extract_header(
        text, rule.style, rule.shebang
    )

    if extraction_error:
        return [(extraction_error, "missing or malformed leading header block")]

    errors: list[tuple[str, str]] = []

    if config["settings"].get("require_spdx", True) and not SPDX_RE.search(header):
        errors.append(
            ("HEADER-001", "missing SPDX-License-Identifier: Apache-2.0")
        )

    if config["settings"].get("require_copyright", True) and not COPYRIGHT_RE.search(
        header
    ):
        errors.append(
            ("HEADER-003", "missing Copyright (c) 2026 KritvaOS")
        )

    fields = parse_fields(normalized)

    if config["settings"].get("require_created_date", True):
        created = fields.get("Created", "")

        if not created:
            errors.append(("HEADER-002", "missing 'Created : DD-MM-YYYY'"))
        elif not DATE_RE.fullmatch(created):
            errors.append(
                (
                    "HEADER-002",
                    f"invalid Created date '{created}', expected DD-MM-YYYY",
                )
            )
        else:
            try:
                datetime.strptime(created, "%d-%m-%Y")
            except ValueError:
                errors.append(("HEADER-002", f"invalid calendar date '{created}'"))

    for required in rule.required_fields:
        if required == "Created":
            continue

        if not fields.get(required, "").strip():
            errors.append(
                (
                    "HEADER-004",
                    f"missing or empty required field '{required}'",
                )
            )

    return errors


def git_lines(root: Path, args: list[str]) -> list[str]:
    result = subprocess.run(
        ["git", "-C", str(root), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return [line for line in result.stdout.splitlines() if line.strip()]


def collect_paths(root: Path, mode: str, explicit: list[str]) -> list[Path]:
    if explicit:
        return [Path(item).resolve() for item in explicit]

    if mode == "staged":
        rels = git_lines(
            root,
            ["diff", "--cached", "--name-only", "--diff-filter=ACMRT"],
        )
    else:
        rels = git_lines(root, ["ls-files"])

    return [(root / item).resolve() for item in rels]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="KritvaOS source header checker"
    )
    parser.add_argument(
        "--mode", choices=["staged", "tracked"], default="staged"
    )
    parser.add_argument("--files", nargs="*", default=[])
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[2]
    config = load_config(root)
    rules = build_rules(config)

    failures = []
    checked = 0

    for path in collect_paths(root, args.mode, args.files):
        if not path.is_file():
            continue

        try:
            rel = normalize_rel(path, root)
        except ValueError:
            continue

        if is_excluded(rel, config):
            continue

        rule = classify(rel, rules)

        if rule is None:
            if args.strict or not config["settings"].get(
                "allow_unknown_extensions", True
            ):
                failures.append(
                    (rel, "HEADER-007", "no matching source-header rule")
                )
            continue

        checked += 1

        for code, message in validate(path, rule, config):
            failures.append((rel, code, message))

    print(f"[header-check] checked {checked} file(s)")

    if failures:
        print("[header-check] FAILED")
        for rel, code, message in failures:
            print(f"  {rel}: [{code}] {message}")
        return 1

    print("[header-check] PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
