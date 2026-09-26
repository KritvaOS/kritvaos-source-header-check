#!/usr/bin/env python3
#==============================================================================
# Copyright (c) 2026 KritvaOS
# SPDX-License-Identifier: Apache-2.0
#
# File        : test_source_header_check.py
# Description : Unit tests for the KritvaOS source header checker
#
# Component   : Infrastructure
# Module      : Source Header Checker
# Layer       : Development
#
# Requirements: Python 3
# API         : unittest
#
# Author      : KritvaOS
# Created     : 26-09-2026
#==============================================================================
from __future__ import annotations
import importlib.util
import unittest
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
ROOT = TESTS_DIR.parent
CHECKER = ROOT / "scripts" / "lint" / "check_source_headers.py"
FIXTURES = TESTS_DIR / "source_header_check"
spec = importlib.util.spec_from_file_location("check_source_headers", CHECKER)
checker = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(checker)

class SourceHeaderCheckerTests(unittest.TestCase):
    def check_valid(self, name):
        self.assertEqual(checker.validate_file(FIXTURES / "valid" / name, ROOT), [])
    def test_valid_cpp(self): self.check_valid("sample.cpp")
    def test_valid_python(self): self.check_valid("sample.py")
    def test_valid_yaml(self): self.check_valid("sample.yaml")
    def test_valid_markdown(self): self.check_valid("sample.md")
    def test_requirements_exempt(self): self.check_valid("requirements.txt")
    def test_extensionless_pre_commit(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            hook = repo / ".githooks" / "pre-commit"
            hook.parent.mkdir(parents=True)
            hook.write_text((FIXTURES / "valid" / "sample_pre_commit").read_text(), encoding="utf-8")
            self.assertEqual(checker.validate_file(hook, repo), [])
    def test_yml_workflow(self): self.check_valid("sample_workflow.yml")
    def test_bad_date(self):
        e = checker.validate_file(FIXTURES / "invalid" / "bad_date.cpp", ROOT)
        self.assertTrue(any(x["code"] == "HEADER-002" for x in e))
    def test_missing_field(self):
        e = checker.validate_file(FIXTURES / "invalid" / "missing_field.cpp", ROOT)
        self.assertTrue(any(x["code"] == "HEADER-004" for x in e))
    def test_missing_spdx(self):
        e = checker.validate_file(FIXTURES / "invalid" / "missing_spdx.cpp", ROOT)
        self.assertTrue(any(x["code"] == "HEADER-001" for x in e))

if __name__ == "__main__":
    unittest.main(verbosity=2)
