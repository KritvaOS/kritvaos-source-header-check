#!/usr/bin/env bash
set -euo pipefail
#==============================================================================
# Copyright (c) 2026 KritvaOS
# SPDX-License-Identifier: Apache-2.0
#
# File        : update.sh
# Description : Safely update an installed KritvaOS Source Header Checker
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
log(){ echo "[header-check] $*"; }
error(){ echo "[header-check] ERROR: $*" >&2; }

[[ $# -eq 1 ]] || { echo "Usage: $0 <target-repository>"; exit 1; }
TARGET_DIR="$(cd "$1" 2>/dev/null && pwd)" || { error "Target repository does not exist: $1"; exit 1; }
[[ -d "${TARGET_DIR}/.git" ]] || { error "Target is not a Git repository: ${TARGET_DIR}"; exit 1; }
[[ -f "${SOURCE_DIR}/VERSION" ]] || { error "Source VERSION not found."; exit 1; }

VERSION_FILE="${TARGET_DIR}/config/source_header_check.version"
if [[ -f "${VERSION_FILE}" ]]; then
  CURRENT_VERSION="$(tr -d '[:space:]' < "${VERSION_FILE}")"
else
  CURRENT_VERSION="legacy-v0.3"
  log "Target has no checker version file."
  log "Detected legacy installation format."
fi
NEW_VERSION="$(tr -d '[:space:]' < "${SOURCE_DIR}/VERSION")"

log "Updating KritvaOS Source Header Checker"
log "Source : ${SOURCE_DIR}"
log "Target : ${TARGET_DIR}"
log "Current version : ${CURRENT_VERSION}"
log "New version     : ${NEW_VERSION}"

if [[ "${CURRENT_VERSION}" == "${NEW_VERSION}" ]]; then
  log "Target is already up to date."
  exit 0
fi

if [[ -n "$(git -C "${TARGET_DIR}" status --porcelain)" ]]; then
  error "Target repository has uncommitted changes."
  error "Please commit or stash changes before updating."
  error "No files were changed."
  exit 1
fi

FILES=(
".githooks/pre-commit"
".github/workflows/source-header-check.yml"
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

for f in "${FILES[@]}"; do
  [[ -f "${SOURCE_DIR}/${f}" ]] || { error "Missing source file: adoption/${f}"; exit 1; }
done

for f in "${FILES[@]}"; do
  mkdir -p "${TARGET_DIR}/$(dirname "${f}")"
  cp "${SOURCE_DIR}/${f}" "${TARGET_DIR}/${f}"
done

CONFIG="${TARGET_DIR}/config/source_header_check.yaml"
SOURCE_CONFIG="${SOURCE_DIR}/config/source_header_check.yaml"
if [[ ! -f "${CONFIG}" ]]; then
  cp "${SOURCE_CONFIG}" "${CONFIG}"
elif git -C "${TARGET_DIR}" ls-files --error-unmatch "config/source_header_check.yaml" >/dev/null 2>&1 &&
     git -C "${TARGET_DIR}" diff --quiet -- "config/source_header_check.yaml"; then
  cp "${SOURCE_CONFIG}" "${CONFIG}"
else
  log "Preserved locally modified config/source_header_check.yaml"
fi

printf '%s\n' "${NEW_VERSION}" > "${VERSION_FILE}"
chmod +x "${TARGET_DIR}/.githooks/pre-commit" "${TARGET_DIR}/scripts/lint/check_source_headers.py"
git -C "${TARGET_DIR}" config core.hooksPath .githooks
log "Update completed successfully."
