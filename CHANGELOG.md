# Changelog

All notable changes to **Evidence Wiki Skill** are documented here. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/).

## [1.0.0] · 2026-08-26

### Added
- Initial public release.
- **9 micro-skills**: `wiki-extract-paper`, `wiki-build-claim`, `wiki-build-evidence`, `wiki-build-topic`, `wiki-query-evidence`, `wiki-lint-wiki`, `wiki-zotero-sync`, `wiki-stitch-knowledge`, `wiki-audit-paper`.
- **31 Python scripts** under `scripts/` covering the 4-layer lint (L0 / L0.5 / L1 / L1.5 / L2 / L3 / L4.6) and 5-stage extraction pipeline (T0–T4).
- **JSON-Schema definitions** for `paperinfo`, `claim`, `evidence`, `topic`, `synthesis` nodes.
- **Templates** for all node types (`paper.md`, `claim.md`, `evidence.md`, plus modality-specific `paper-fmri.md`, `paper-eeg.md`, `paper-fnirs.md`, …).
- **Bilingual documentation**: English (default) and Chinese (`*.zh.md`).
- `wiki` unified CLI (`scripts/wiki`) — single entry for `init`, `ingest`, `lint`, `check-evidence`, `search`, `status`, `index`, `archive`, `zotero`, `zotero-csv`.
- `install.sh` for optional pi-coding-agent integration.
- `pyproject.toml` for `pip install -e .`.

### Verified
- All 31 scripts pass `python3 -m py_compile`.
- Internal imports (`wiki_common`, `wiki_lint`, `wiki_render_nodes`, `wiki_render_evidence_body`, `wiki_check_evidence`, `_registry`) resolve cleanly when `scripts/` is on `PYTHONPATH`.
- 11 Iron Rules encoded in both `AGENTS.md` and `docs/*/architecture.md`.

### Notes
- This is the first public release. Future versions will follow semver:
  - **Patch** (`1.0.x`) — bug fixes in scripts, schema tightening.
  - **Minor** (`1.x.0`) — new micro-skill, new node type, backward-compatible.
  - **Major** (`x.0.0`) — Iron Rule changes, schema breaking changes.

[1.0.0]: https://github.com/hasibagen/evidence-wiki/releases/tag/v1.0.0