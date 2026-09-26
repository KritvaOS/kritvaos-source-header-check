# KritvaOS Source Header Checker v0.3.3

## Purpose

Validate KritvaOS source headers without treating every tracked text file as source code.

## v0.3.3 classification policy

Checked:
- C/C++ source and headers
- Python
- Shell
- Verilog/SystemVerilog
- DTS/DTSI
- `.githooks/pre-commit`
- `.github/workflows/*.yml` and `*.yaml`

Skipped by default:
- Unsupported extensions
- Markdown documentation
- GitHub agents/instructions
- Templates
- `requirements.txt`
- checker version metadata
- generated/vendor/build/external content
- source-header test fixtures

The invalid fixtures remain covered by the unit-test suite.

## Install

```bash
./install.sh <target-repository>
```

## Update

```bash
./update.sh <target-repository>
```

The updater supports legacy v0.3 installations without a version file.

## Verify

```bash
python3 tests/test_source_header_check.py
python3 scripts/lint/check_source_headers.py --mode tracked --strict
```

## Version

The adoption version is stored in `adoption/VERSION`.
