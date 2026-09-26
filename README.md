# KritvaOS Source Header Checker v0.3

v0.3 replaces the v0.2 search-based validation with **true leading-header extraction**.

## Main fixes
- Validates only the actual leading header block.
- Source strings and test fixtures cannot satisfy header fields.
- Dedicated `Created : DD-MM-YYYY` validation.
- Supports `#`, `//`, `/* ... */`, and `<!-- ... -->` headers.
- Supports optional Python/shell shebangs.
- Test-specific rules are evaluated before generic C/C++ rules.
- Local pre-commit and GitHub CI use the same checker.
- JSON remains headerless.
- Policy, generated, vendor, and third-party paths are excluded.

## Install

```bash
python3 -m pip install -r scripts/lint/requirements.txt
git config core.hooksPath .githooks
```

## Run

```bash
python3 scripts/lint/check_source_headers.py --mode staged
python3 scripts/lint/check_source_headers.py --mode tracked --strict
python3 scripts/lint/check_source_headers.py --files src/foo.cpp tests/foo_test.cpp
python3 tests/test_source_header_check.py
```

## Error codes

- HEADER-001: missing SPDX
- HEADER-002: missing/invalid Created date
- HEADER-003: missing copyright
- HEADER-004: missing required field
- HEADER-005: shebang/header placement
- HEADER-006: malformed header/encoding
- HEADER-007: no matching rule in strict mode
- HEADER-008: malformed leading header
