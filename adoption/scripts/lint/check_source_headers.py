#!/usr/bin/env python3
#==============================================================================
# Copyright (c) 2026 KritvaOS
# SPDX-License-Identifier: Apache-2.0
#
# File        : check_source_headers.py
# Description : Validate KritvaOS source-file headers
#
# Component   : Infrastructure
# Module      : Source Header Checker
# Layer       : Development
#
# Requirements: Python 3
# API         : Command-line interface
#
# Author      : KritvaOS
# Created     : 26-09-2026
#==============================================================================

from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
from pathlib import Path

REQUIRED_FIELDS = ("File", "Description", "Component", "Module", "Layer", "Requirements", "API", "Author", "Created")
SPDX_MARKER = "SPDX-License-Identifier: Apache-2.0"
COPYRIGHT_MARKER = "Copyright (c) 2026 KritvaOS"
EXCLUDED_DIRS = {".git", "build", "out", "third_party", "vendor", "generated", "external", "__pycache__"}
EXCLUDED_FILES = {"LICENSE", "NOTICE", "CHANGELOG.md"}
SPECIAL_SHELL_FILES = {".githooks/pre-commit"}
HEADER_EXEMPT_NAMES = {"requirements.txt"}
COMMENT_STYLE = {
    ".c": "//", ".cc": "//", ".cpp": "//", ".cxx": "//", ".h": "//", ".hh": "//", ".hpp": "//", ".hxx": "//",
    ".java": "//", ".js": "//", ".ts": "//", ".go": "//", ".rs": "//", ".py": "#", ".sh": "#", ".bash": "#",
    ".yaml": "#", ".yml": "#", ".toml": "#", ".cmake": "#", ".mk": "#", ".dts": "//", ".dtsi": "//",
    ".v": "//", ".sv": "//", ".svh": "//", ".vh": "//", ".md": "<!--", ".xml": "<!--", ".html": "<!--", ".htm": "<!--",
}

def git_tracked_files(repo: Path) -> list[Path]:
    result = subprocess.run(["git", "-C", str(repo), "ls-files", "-z"], check=True, capture_output=True)
    return [repo / p for p in result.stdout.decode("utf-8", errors="replace").split("\0") if p]

def relative(path: Path, repo: Path) -> str:
    return path.relative_to(repo).as_posix()

def excluded(path: Path, repo: Path) -> bool:
    rel = path.relative_to(repo)
    return path.name in EXCLUDED_FILES or any(part in EXCLUDED_DIRS for part in rel.parts)

def rule_for(path: Path, repo: Path) -> str | None:
    rel = relative(path, repo)
    if rel in SPECIAL_SHELL_FILES:
        return "#"
    if path.name in HEADER_EXEMPT_NAMES or path.suffix.lower() == ".json":
        return None
    return COMMENT_STYLE.get(path.suffix.lower())

def read_lines(path: Path, count: int = 100) -> list[str]:
    with path.open("r", encoding="utf-8", errors="strict") as f:
        return [line.rstrip("\n") for _, line in zip(range(count), f)]

def extract_header(path: Path, repo: Path) -> tuple[list[str], str | None]:
    rule = rule_for(path, repo)
    if rule is None:
        return [], None
    lines = read_lines(path)
    start_idx = 1 if lines and lines[0].startswith("#!") else 0
    if rule == "<!--":
        start = next((i for i in range(start_idx, len(lines)) if lines[i].lstrip().startswith("<!--")), None)
        if start is None:
            return [], "HEADER-008"
        end = next((i for i in range(start, len(lines)) if "-->" in lines[i]), None)
        if end is None:
            return lines[start:], "HEADER-008"
        return lines[start:end + 1], None
    start = next((i for i in range(start_idx, len(lines)) if lines[i].lstrip().startswith(rule)), None)
    if start is None:
        return [], "HEADER-008"
    header = []
    for line in lines[start:]:
        stripped = line.lstrip()
        if stripped.startswith(rule):
            header.append(line)
        elif not stripped:
            if header:
                header.append(line)
        else:
            break
    return (header, None) if header else ([], "HEADER-008")

def validate_file(path: Path, repo: Path) -> list[dict]:
    if path.name in HEADER_EXEMPT_NAMES or path.suffix.lower() == ".json":
        return []
    if rule_for(path, repo) is None:
        return [{"file": str(path), "code": "HEADER-007", "message": "no matching source-header rule"}]
    try:
        header, extraction_error = extract_header(path, repo)
    except UnicodeDecodeError:
        return [{"file": str(path), "code": "HEADER-006", "message": "file is not valid UTF-8 text"}]
    if extraction_error:
        return [{"file": str(path), "code": extraction_error, "message": "missing or malformed leading header block"}]
    text = "\n".join(header)
    errors = []
    if SPDX_MARKER not in text:
        errors.append({"file": str(path), "code": "HEADER-001", "message": "missing SPDX-License-Identifier: Apache-2.0"})
    if COPYRIGHT_MARKER not in text:
        errors.append({"file": str(path), "code": "HEADER-003", "message": "missing Copyright (c) 2026 KritvaOS"})
    for field in REQUIRED_FIELDS:
        if field == "Created":
            continue
        if not any(field in line for line in header):
            errors.append({"file": str(path), "code": "HEADER-004", "message": f"missing or empty required field '{field}'"})
    created_line = next((line for line in header if "Created" in line), None)
    if created_line is None:
        errors.append({"file": str(path), "code": "HEADER-002", "message": "missing 'Created : DD-MM-YYYY'"})
    else:
        value = created_line.split(":", 1)[1].strip() if ":" in created_line else ""
        try:
            dt.datetime.strptime(value, "%d-%m-%Y")
        except ValueError:
            errors.append({"file": str(path), "code": "HEADER-002", "message": "invalid 'Created' date; expected DD-MM-YYYY"})
    return errors

def main() -> int:
    parser = argparse.ArgumentParser(description="KritvaOS source header checker")
    parser.add_argument("--mode", choices=("tracked", "files"), default="tracked")
    parser.add_argument("--files", nargs="*")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    repo = Path.cwd().resolve()
    paths = git_tracked_files(repo) if args.mode == "tracked" else [(repo / p).resolve() for p in (args.files or [])]
    checked, errors = 0, []
    for path in paths:
        if not path.is_file() or excluded(path, repo):
            continue
        if path.suffix.lower() == ".json" or path.name in HEADER_EXEMPT_NAMES:
            continue
        checked += 1
        errors.extend(validate_file(path, repo))
    if args.json:
        print(json.dumps({"checked": checked, "errors": errors}, indent=2))
    else:
        print(f"[header-check] checked {checked} file(s)")
        if errors:
            print("[header-check] FAILED")
            for e in errors:
                print(f"  {e['file']}: [{e['code']}] {e['message']}")
        else:
            print("[header-check] PASSED")
    return 1 if errors else 0

if __name__ == "__main__":
    raise SystemExit(main())
