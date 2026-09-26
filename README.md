# KritvaOS Source Header Checker

**Reference Repository Standard — v0.3**

This repository is a standalone reference implementation for the KritvaOS source-header validation standard. New KritvaOS repositories can adopt the checker and its Git/CI integration rather than creating their own header-validation mechanism.

## 1. Repository purpose

The repository defines a common standard for:

- SPDX licensing
- KritvaOS copyright identification
- `Created : DD-MM-YYYY`
- Required metadata fields
- Comment syntax by file type
- Local Git pre-commit validation
- GitHub CI validation
- Regression tests
- Exclusion of generated/vendor/third-party content

Recommended repository:

```text
KritvaOS/kritvaos-source-header-check
```

It is infrastructure/reference material, not a KritvaOS runtime component.

## 2. Reference relationship

```text
             kritvaos-source-header-check
                         │
              Reference Standard
                         │
       ┌─────────────────┼─────────────────┐
       ▼                 ▼                 ▼
  kritva-core       kritva-sense       kritva-mind
       │                 │                 │
   local hook +      local hook +      local hook +
       CI                CI                CI
```

The reference repository owns the standard. Individual KritvaOS repositories adopt it.

## 3. Folder structure

```text
kritvaos-source-header-check/
├── .githooks/
│   └── pre-commit
├── .github/
│   └── workflows/
│       └── source-header-check.yml
├── config/
│   └── source_header_check.yaml
├── scripts/
│   └── lint/
│       ├── check_source_headers.py
│       └── requirements.txt
├── tests/
│   ├── test_source_header_check.py
│   └── source_header_check/
│       ├── valid/
│       │   ├── sample.cpp
│       │   ├── sample.py
│       │   ├── sample.yaml
│       │   └── sample.md
│       └── invalid/
│           ├── missing_spdx.cpp
│           ├── bad_date.cpp
│           └── missing_field.cpp
├── README.md
└── LICENSE
```

## 4. File responsibilities

### `.githooks/pre-commit`

Thin local Git integration. It invokes the checker:

```bash
python3 scripts/lint/check_source_headers.py --mode staged
```

It should not contain validation rules.

Enable it with:

```bash
git config core.hooksPath .githooks
```

### `.github/workflows/source-header-check.yml`

Authoritative CI enforcement. It runs:

```bash
python scripts/lint/check_source_headers.py --mode tracked --strict
```

The local hook can be bypassed with `--no-verify`; CI is therefore the enforcement mechanism.

### `config/source_header_check.yaml`

Policy/configuration layer. Defines:

- file types
- comment styles
- required fields
- exclusions
- shebang handling
- extensions and patterns

Do not duplicate this policy in the Git hook or workflow.

### `scripts/lint/check_source_headers.py`

Single source of truth for validation behavior.

It:

1. classifies files
2. extracts the actual leading header
3. parses fields
4. checks SPDX
5. checks copyright
6. validates `Created`
7. validates required fields
8. handles shebangs
9. applies exclusions
10. supports staged/tracked/explicit-file modes
11. emits structured error codes

The v0.3 design is important: it extracts the actual leading header rather than searching arbitrary text in the first N lines. Therefore this must not satisfy header validation:

```cpp
const char *text = "Created : 26-09-2026";
```

### `scripts/lint/requirements.txt`

Python dependencies for the checker:

```text
PyYAML
```

Install with:

```bash
python3 -m pip install -r scripts/lint/requirements.txt
```

### `tests/test_source_header_check.py`

Unit tests for the checker itself.

Important regression cases include:

- valid header extraction
- shebang handling
- invalid date
- source strings not being interpreted as header fields

### `tests/source_header_check/valid/`

Known-good examples for supported formats.

### `tests/source_header_check/invalid/`

Deliberately broken examples used as test fixtures. They are not intended to pass repository validation.

## 5. Supported header styles

### C/C++/RTL

```cpp
//==============================================================================
// Copyright (c) 2026 KritvaOS
// SPDX-License-Identifier: Apache-2.0
//
// File        : example.cpp
// Description : Example implementation
//
// Component   : Core
// Module      : Example
// Layer       : Runtime
//
// Author      : KritvaOS Team
// Created     : 26-09-2026
//==============================================================================
```

### Python/YAML/Shell

```python
#==============================================================================
# Copyright (c) 2026 KritvaOS
# SPDX-License-Identifier: Apache-2.0
#
# File        : example.py
# Description : Example implementation
#
# Component   : Core
# Module      : Example
# Layer       : Development
#
# Author      : KritvaOS Team
# Created     : 26-09-2026
#==============================================================================
```

Python/shell shebangs are supported before the header:

```python
#!/usr/bin/env python3
```

### Markdown/XML

```text
<!--
Copyright (c) 2026 KritvaOS
SPDX-License-Identifier: Apache-2.0

File        : example.md
Description : Example documentation

Component   : Documentation
Module      : Example
Layer       : User

Author      : KritvaOS Team
Created     : 26-09-2026
-->
```

## 6. Header fields

Core fields:

```text
Copyright
SPDX-License-Identifier
File
Description
Component
Module
Layer
Author
Created
```

Additional fields can be required for particular file classes, for example:

```text
Test Type
Interface
Hardware
Requirements
API
```

Do not invent metadata merely to populate a field.

## 7. Date standard

KritvaOS uses:

```text
DD-MM-YYYY
```

Valid:

```text
Created     : 26-09-2026
```

Invalid:

```text
Created     : 2026-09-26
Created     : 26/09/2026
Created     : 09-26-2026
```

The checker validates both format and calendar validity.

## 8. Error codes

| Code | Meaning |
|---|---|
| `HEADER-001` | Missing SPDX |
| `HEADER-002` | Missing/invalid Created date |
| `HEADER-003` | Missing copyright |
| `HEADER-004` | Missing required field |
| `HEADER-005` | Shebang/header placement issue |
| `HEADER-006` | Malformed header or encoding |
| `HEADER-007` | No matching rule in strict mode |
| `HEADER-008` | Malformed/missing leading header |

Example:

```text
src/example.cpp: [HEADER-002] invalid Created date '2026-09-26', expected DD-MM-YYYY
```

## 9. Normal developer workflow

```bash
git add src/example.cpp
git commit -m "Add example module"
```

The pre-commit hook runs automatically.

Success:

```text
[header-check] checked 1 file(s)
[header-check] PASSED
```

Failure:

```text
[header-check] FAILED
  src/example.cpp: [HEADER-002] invalid Created date ...
```

Fix the file and commit again.

## 10. Manual commands

Staged files:

```bash
python3 scripts/lint/check_source_headers.py --mode staged
```

Entire tracked repository:

```bash
python3 scripts/lint/check_source_headers.py --mode tracked --strict
```

Specific files:

```bash
python3 scripts/lint/check_source_headers.py \
    --files src/foo.cpp tests/foo_test.cpp
```

Unit tests:

```bash
python3 tests/test_source_header_check.py
```

## 11. Recommended adoption by a new KritvaOS repository

For a new repository:

1. Start from the v0.3 reference package.
2. Copy/adopt `.githooks`, `.github/workflows`, `config`, `scripts/lint`, and tests.
3. Adjust only repository-specific rules in `config/source_header_check.yaml`.
4. Install dependencies.
5. Enable the Git hook.
6. Run a full validation.
7. Commit the adopted infrastructure before substantial source development.

Example:

```bash
python3 -m pip install -r scripts/lint/requirements.txt
git config core.hooksPath .githooks
python3 scripts/lint/check_source_headers.py --mode tracked --strict
git add .
git commit -m "Adopt KritvaOS source header standard"
```

## 12. Recommended commit sequence for the reference repository

Keep the history logical and reusable.

### Commit 1 — Repository skeleton

```bash
git add README.md LICENSE
git commit -m "Initialize source header checker repository"
```

### Commit 2 — Validation configuration

```bash
git add config/source_header_check.yaml
git commit -m "Add source header validation configuration"
```

### Commit 3 — Checker implementation

```bash
git add scripts/lint/check_source_headers.py scripts/lint/requirements.txt
git commit -m "Add source header checker"
```

### Commit 4 — Regression tests

```bash
git add tests/
git commit -m "Add source header checker tests"
```

### Commit 5 — Local Git integration

```bash
git add .githooks/pre-commit
git commit -m "Add source header pre-commit hook"
```

### Commit 6 — CI integration

```bash
git add .github/workflows/source-header-check.yml
git commit -m "Add source header CI validation"
```

### Commit 7 — Documentation refinement

```bash
git add README.md
git commit -m "Document source header checker workflow"
```

## 13. Release/tag

Once v0.3 is stable:

```bash
git tag -a v0.3.0 -m "KritvaOS Source Header Checker v0.3.0"
git push origin main
git push origin v0.3.0
```

Adopting repositories should record the reference version they use, for example:

```text
Source Header Checker: v0.3.0
```

## 14. Updating the reference standard

Use this flow:

```text
Requirement
    ↓
Issue
    ↓
Design/change
    ↓
Checker/config update
    ↓
Regression test
    ↓
README update
    ↓
Review
    ↓
Commit
    ↓
Tag/release
```

If a common KritvaOS requirement changes, update the reference repository rather than silently modifying every downstream repository.

## 15. Repository-specific customization

Customization should normally occur in:

```text
config/source_header_check.yaml
```

For example, RTL repositories may require:

```text
Interface
```

Test repositories may require:

```text
Test Type
```

Hardware repositories may require:

```text
Hardware
```

The fundamental checker behavior should remain common.

## 16. Governance recommendation

Treat this repository as the canonical KritvaOS source-header reference.

Recommended ownership:

```text
KritvaOS
└── Development Infrastructure
    └── Source Header Checker
```

Common changes should be reviewed before release.

A future CODEOWNERS file can assign:

```text
/config/        @KritvaOS/maintainers
/scripts/lint/  @KritvaOS/maintainers
/tests/         @KritvaOS/maintainers
.githooks/      @KritvaOS/maintainers
.github/        @KritvaOS/maintainers
```

## 17. Long-term evolution

Keep this repository focused.

If KritvaOS later needs a broader common development standard, it could evolve into:

```text
kritvaos-development-standards/
├── source-header-check/
├── clang-format/
├── clang-tidy/
├── commit-policy/
├── repository-template/
└── CI-common/
```

Do not combine these prematurely. The current standalone source-header repository is intentionally small.

## 18. Core principle

```text
One Standard
     │
     ├── One Configuration
     │
     ├── One Checker
     │
     ├── One Test Suite
     │
     ├── Local Validation
     │
     └── CI Validation
```

This gives KritvaOS repositories a consistent source-header convention while keeping the implementation independently maintainable.

**Reference:** KritvaOS Source Header Checker v0.3  
**Date:** 26-09-2026


## 11. Install into an Existing KritvaOS Repository

The reference repository provides `install.sh` to adopt the source-header checker into an existing Git repository.

The installer copies **only the adoption payload**. It does **not** copy the reference repository's `README.md`, `LICENSE`, or other reference-repository files.

### Reference repository structure

```text
kritvaos-source-header-check/
├── adoption/
│   ├── .githooks/
│   ├── .github/
│   ├── config/
│   ├── scripts/
│   └── tests/
├── install.sh
├── README.md
└── LICENSE
```

The `adoption/` directory is the installable payload.

### Step 1 — Clone the reference repository

```bash
git clone https://github.com/KritvaOS/kritvaos-source-header-check.git
cd kritvaos-source-header-check
```

### Step 2 — Select the reference version

For a stable adoption, use a released tag:

```bash
git checkout v0.3.0
```

Verify:

```bash
git describe --tags --exact-match
```

Expected:

```text
v0.3.0
```

### Step 3 — Run the installer

For an existing KritvaOS repository:

```bash
./install.sh ../kritva-core
```

For example:

```bash
./install.sh ~/workarea/kritvaOS/kritvaos-community
```

The installer:

1. Verifies that the target directory exists.
2. Verifies that the target is a Git repository.
3. Copies only the files under `adoption/`.
4. Enables the repository's `.githooks` directory.
5. Does **not** copy the reference `README.md`.
6. Does **not** overwrite the target repository's root `README.md`.

### Step 4 — Install checker dependencies

Change to the target repository:

```bash
cd ~/workarea/kritvaOS/kritvaos-community
```

Install the checker dependency:

```bash
python3 -m pip install -r scripts/lint/requirements.txt
```

### Step 5 — Run the checker unit tests

```bash
python3 tests/test_source_header_check.py
```

Expected:

```text
...
OK
```

### Step 6 — Check the existing repository

Before committing the adoption:

```bash
python3 scripts/lint/check_source_headers.py --mode tracked --strict
```

This checks the existing tracked files against the adopted policy.

If existing files do not yet have headers, the checker will report them. Fix those files before enabling the standard as a required CI check.

### Step 7 — Verify Git hook configuration

The installer configures:

```bash
git config core.hooksPath .githooks
```

Verify:

```bash
git config --get core.hooksPath
```

Expected:

```text
.githooks
```

### Step 8 — Verify the pre-commit hook

Create or modify a source file and stage it:

```bash
git add <file>
```

Then commit:

```bash
git commit -m "Adopt KritvaOS source header standard"
```

The hook should automatically execute:

```bash
scripts/lint/check_source_headers.py --mode staged
```

### Complete command sequence

For a typical existing repository:

```bash
git clone https://github.com/KritvaOS/kritvaos-source-header-check.git
cd kritvaos-source-header-check
git checkout v0.3.0

./install.sh ~/workarea/kritvaOS/kritvaos-community

cd ~/workarea/kritvaOS/kritvaos-community

python3 -m pip install -r scripts/lint/requirements.txt

python3 tests/test_source_header_check.py

python3 scripts/lint/check_source_headers.py --mode tracked --strict

git config --get core.hooksPath
```

Expected hook configuration:

```text
.githooks
```

### What gets installed

```text
Target Repository
├── .githooks/
│   └── pre-commit
├── .github/
│   └── workflows/
│       └── source-header-check.yml
├── config/
│   └── source_header_check.yaml
├── scripts/
│   └── lint/
│       ├── check_source_headers.py
│       └── requirements.txt
└── tests/
    └── test_source_header_check.py
```

The target repository's existing files remain in place, including:

```text
README.md
LICENSE
NOTICE
CONTRIBUTING.md
SECURITY.md
```

The reference repository's `README.md` is **never copied** by `install.sh`.

### Important adoption rule

Use a released reference tag when adopting the checker:

```bash
git checkout v0.3.0
```

Do not install directly from an arbitrary development branch for production KritvaOS repositories.

Record the adopted version in the target repository's development documentation:

```text
Source Header Checker: v0.3.0
```

