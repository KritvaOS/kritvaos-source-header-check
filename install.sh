#!/usr/bin/env bash
set -euo pipefail

#==============================================================================
# Copyright (c) 2026 KritvaOS
# SPDX-License-Identifier: Apache-2.0
#
# File        : install.sh
# Description : Install the KritvaOS source-header checker into a target repo.
#
# Component   : Infrastructure
# Module      : Source Header Checker
# Layer       : Development
#
# Author      : KritvaOS Team
# Created     : 26-09-2026
#==============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_DIR="${SCRIPT_DIR}/adoption"

usage()
{
    echo "Usage:"
    echo "  $0 <target-repository>"
    echo
    echo "Example:"
    echo "  $0 ../kritva-core"
    exit 1
}

if [[ $# -ne 1 ]]; then
    usage
fi

TARGET_DIR="$(cd "$1" 2>/dev/null && pwd)" || {
    echo "[header-check] ERROR: Target repository does not exist:"
    echo "  $1"
    exit 1
}

if [[ ! -d "${TARGET_DIR}/.git" ]]; then
    echo "[header-check] ERROR: Target is not a Git repository:"
    echo "  ${TARGET_DIR}"
    exit 1
fi

if [[ ! -d "${SOURCE_DIR}" ]]; then
    echo "[header-check] ERROR: Adoption directory not found:"
    echo "  ${SOURCE_DIR}"
    exit 1
fi

echo "[header-check] Installing KritvaOS Source Header Checker"
echo "[header-check] Source : ${SOURCE_DIR}"
echo "[header-check] Target : ${TARGET_DIR}"
echo

# ---------------------------------------------------------------------------
# Explicitly copy ONLY adoption payload.
# README.md, LICENSE and other reference-repository files are NOT copied.
# ---------------------------------------------------------------------------

mkdir -p \
    "${TARGET_DIR}/.githooks" \
    "${TARGET_DIR}/.github/workflows" \
    "${TARGET_DIR}/config" \
    "${TARGET_DIR}/scripts/lint" \
    "${TARGET_DIR}/tests"

cp "${SOURCE_DIR}/.githooks/pre-commit" \
   "${TARGET_DIR}/.githooks/pre-commit"

cp "${SOURCE_DIR}/.github/workflows/source-header-check.yml" \
   "${TARGET_DIR}/.github/workflows/source-header-check.yml"

cp "${SOURCE_DIR}/config/source_header_check.yaml" \
   "${TARGET_DIR}/config/source_header_check.yaml"

cp "${SOURCE_DIR}/scripts/lint/check_source_headers.py" \
   "${TARGET_DIR}/scripts/lint/check_source_headers.py"

cp "${SOURCE_DIR}/scripts/lint/requirements.txt" \
   "${TARGET_DIR}/scripts/lint/requirements.txt"

cp "${SOURCE_DIR}/tests/test_source_header_check.py" \
   "${TARGET_DIR}/tests/test_source_header_check.py"

chmod +x "${TARGET_DIR}/.githooks/pre-commit"
chmod +x "${TARGET_DIR}/scripts/lint/check_source_headers.py"

# ---------------------------------------------------------------------------
# Configure Git to use the repository's .githooks directory.
# ---------------------------------------------------------------------------

git -C "${TARGET_DIR}" config core.hooksPath .githooks

echo
echo "[header-check] Installation complete."
echo
echo "Installed:"
echo "  .githooks/pre-commit"
echo "  .github/workflows/source-header-check.yml"
echo "  config/source_header_check.yaml"
echo "  scripts/lint/check_source_headers.py"
echo "  scripts/lint/requirements.txt"
echo "  tests/test_source_header_check.py"
echo
echo "Reference README.md was NOT copied."
echo
echo "Next steps:"
echo "  cd ${TARGET_DIR}"
echo "  python3 -m pip install -r scripts/lint/requirements.txt"
echo "  python3 tests/test_source_header_check.py"
echo "  python3 scripts/lint/check_source_headers.py --mode tracked --strict"
