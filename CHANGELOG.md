# Changelog

All notable changes to **ClaimTrace** are documented here. Format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); this project adheres
to [Semantic Versioning](https://semver.org/).

> ClaimTrace was previously published as **evidence-wiki** (v1.0.0). The GitHub
> repository rename keeps old links redirecting.

## [2.0.0] · 2026-10-08

### Renamed
- **evidence-wiki → ClaimTrace** — the name now states the core guarantee:
  every claim traces back to a verbatim, grep-verifiable quote.

### Added
- **10th micro-skill: `wiki-extract-modeling`** — deep-read extraction of
  train/validation/test protocols for modeling papers (M0–M5, mermaid pipeline,
  three-level explanation, red flags).
- **Demo vault** (`demo/`): 3 fictional fNIRS papers fully extracted into
  3 paperinfo + 3 papers + 4 claims + 4 evidence + 1 topic + 1 synthesis —
  generated and validated by this repo's own toolchain.
- **CI** (GitHub Actions): unit tests + 8-layer lint + render idempotency on
  the demo vault, on Python 3.10/3.12.
- **Engine integration pack** (`engines/pi/`): the 10 slash-command prompts and
  the `wiki-tools.ts` extension for the pi coding agent.
- **Runner & guard scripts**: `wiki_run_extract.sh` (engine-agnostic batch
  runner: pi / codex / zcode, commit-as-you-go) and `wiki_git_guard.sh`
  (multi-session git surgery guard).
- **Term-normalization gate** (`wiki_normalize_terms.py`), **promote gate**
  (`wiki_promote.py --check/--execute`), **batch status** (`wiki_batch_status.py`),
  **PDF→md** (`wiki_pdf_to_md.py`) and many more scripts — the toolchain grew
  from 31 to 40+ curated scripts.

### Changed
- **Engine decoupling (2026-09-04)**: extraction is no longer bound to one LLM
  CLI. `pi`, `codex` and `zcode` are all first-class engines via
  `INVOKE.md` / `INVOKE-PREFIX`.
- **Claim-depth fields**: premises/argument-role/polarity/epistemic-stance and
  the reasoning bridge are now part of the claim schema and rendered body.
- **Hardened serialization**: all frontmatter writes go through
  `dump_frontmatter_safe` (YAML implicit-scalar defense).
- `ARCHITECTURE.md` is the single source of truth for all field contracts
  (§3) — schemas and templates derive from it.

### Fixed
- Removed machine-specific absolute paths from scripts and docs; defaults now
  resolve from the working directory / `$HOME`.

## [1.0.0] · 2026-08-26

### Added
- Initial public release (as **Evidence Wiki Skill**).
- 9 micro-skills, 31 Python scripts, JSON-Schema definitions for all node
  types, bilingual documentation, `wiki` unified CLI.
