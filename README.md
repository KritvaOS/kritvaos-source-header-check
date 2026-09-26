# KritvaOS Source Header Checker v0.3.2

Reusable source-header validation infrastructure for KritvaOS repositories.

## Install into a new repository

```bash
git clone https://github.com/KritvaOS/kritvaos-source-header-check.git
cd kritvaos-source-header-check
git checkout v0.3.2

./install.sh ~/workarea/kritvaOS/kritvaos-community
```

`install.sh` is for first-time installation only. It never overwrites existing managed files.

## Update an existing installation

```bash
cd ~/workarea/kritvaOS/kritvaos-source-header-check
git checkout v0.3.2

./update.sh ~/workarea/kritvaOS/kritvaos-community
```

The updater checks the installed version, refuses to run with uncommitted target changes, updates managed checker/test/hook files, and preserves a locally modified checker configuration.

## Verify

```bash
cd ~/workarea/kritvaOS/kritvaos-community

cat config/source_header_check.version
python3 tests/test_source_header_check.py
python3 scripts/lint/check_source_headers.py --mode tracked --strict
git config --get core.hooksPath
```

## Adoption payload

Only the `adoption/` payload is installed. The reference repository's root `README.md`, `LICENSE`, `install.sh`, and `update.sh` are not copied into target repositories.

## v0.3.2 fixes

- Supports extensionless `.githooks/pre-commit`.
- Supports `.yml` and `.yaml` leading headers.
- Exempts `requirements.txt` metadata files.
- Adds regression tests for checker infrastructure files.
- Supports legacy v0.3 installations during update.

## Version

The adoption payload version is stored in:

```text
adoption/VERSION
```

Target repositories record the adopted version in:

```text
config/source_header_check.version
```
