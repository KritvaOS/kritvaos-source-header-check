#!/usr/bin/env bash
set -euo pipefail

#==============================================================================
# Copyright (c) 2026 KritvaOS
# SPDX-License-Identifier: Apache-2.0
#
# File        : install.sh
# Description : Install the KritvaOS Source Header Checker into a Git repository
#
# Component   : Infrastructure
# Module      : Source Header Checker
# Layer       : Development
#
# Requirements: Git, Python 3
# API         : Command line
#
# Author      : KritvaOS
# Created     : 26-09-2026
#==============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_DIR="${SCRIPT_DIR}/adoption"

log() { echo "[header-check] $*"; }
error() { echo "[header-check] ERROR: $*" >&2; }

usage() {
    echo "Usage: $0 <target-repository>"
}

[[ $# -eq 1 ]] || { usage; exit 1; }

TARGET_DIR="$(cd "$1" 2>/dev/null && pwd)" || {
    error "Target repository does not exist: $1"
    exit 1
}

[[ -d "${TARGET_DIR}/.git" ]] || {
    error "Target is not a Git repository: ${TARGET_DIR}"
    exit 1
}

[[ -d "${SOURCE_DIR}" ]] || {
    error "Adoption directory not found: ${SOURCE_DIR}"
    exit 1
}

log "Installing KritvaOS Source Header Checker"
log "Source : ${SOURCE_DIR}"
log "Target : ${TARGET_DIR}"

REQUIRED_FILES=(
    ".githooks/pre-commit"
    ".github/workflows/source-header-check.yml"
    "config/source_header_check.yaml"
    "config/source_header_check.version"
    "scripts/lint/check_source_headers.py"
    "scripts/lint/requirements.txt"
    "tests/test_source_header_check.py"
    "tests/source_header_check/invalid/bad_date.cpp"
    "tests/source_header_check/invalid/missing_field.cpp"
    "tests/source_header_check/invalid/missing_spdx.cpp"
    "tests/source_header_check/valid/sample.cpp"
    "tests/source_header_check/valid/sample.md"
    "tests/source_header_check/valid/sample.py"
    "tests/source_header_check/valid/sample.yaml"
)

missing=()
for file in "${REQUIRED_FILES[@]}"; do
    if [[ ! -f "${SOURCE_DIR}/${file}" && "${file}" != "config/source_header_check.version" ]]; then
        missing+=("${file}")
    fi
done

if [[ ! -f "${SOURCE_DIR}/VERSION" ]]; then
    missing+=("VERSION")
fi

if [[ ${#missing[@]} -ne 0 ]]; then
    error "Adoption package is incomplete."
    printf '  %s\n' "${missing[@]}"
    error "No files were changed."
    exit 1
fi

mkdir -p "${SOURCE_DIR}/config"
printf '%s\n' "$(cat "${SOURCE_DIR}/VERSION")" > "${SOURCE_DIR}/config/source_header_check.version"

existing=()
for file in "${REQUIRED_FILES[@]}"; do
    [[ -f "${TARGET_DIR}/${file}" ]] && existing+=("${file}")
done

if [[ ${#existing[@]} -ne 0 ]]; then
    error "Target repository already contains managed file(s):"
    printf '  %s\n' "${existing[@]}"
    error "No files were changed."
    exit 1
fi

mkdir -p \
    "${TARGET_DIR}/.githooks" \
    "${TARGET_DIR}/.github/workflows" \
    "${TARGET_DIR}/config" \
    "${TARGET_DIR}/scripts/lint" \
    "${TARGET_DIR}/tests/source_header_check/invalid" \
    "${TARGET_DIR}/tests/source_header_check/valid"

for file in "${REQUIRED_FILES[@]}"; do
    cp "${SOURCE_DIR}/${file}" "${TARGET_DIR}/${file}"
    echo "  installed: ${file}"
done

chmod +x \
    "${TARGET_DIR}/.githooks/pre-commit" \
    "${TARGET_DIR}/scripts/lint/check_source_headers.py"

git -C "${TARGET_DIR}" config core.hooksPath .githooks

log "Installation completed successfully."
