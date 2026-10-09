# Contributing to ClaimTrace

Thank you for your interest in improving **ClaimTrace**. This document explains how to set up a dev environment, run tests, and submit changes.

## Code of conduct

Be kind. The skill is for individual researchers; we are all on the same side.

## Reporting issues

Open an issue on GitHub. Include:

- **Repro steps** (which command, what input)
- **Expected vs. actual output**
- **Your environment** (Python version, OS, LLM provider)
- **Wiki size** (number of papers / claims / evidence)

For security issues, please email the maintainer directly instead of opening a public issue.

## Development setup

```bash
git clone https://github.com/hasibagen/claimtrace.git
cd claimtrace
pip install -e ".[dev]"    # when extras are defined; otherwise pip install -e .
```

### Layout

```
scripts/             <- all Python tooling (31 scripts)
scripts/schemas/     <- JSON-Schema definitions
scripts/tests/       <- pytest tests (run: pytest scripts/tests/)
skills/              <- 9 micro-skills (slash-commands)
specs/               <- architecture documents
references/templates <- markdown templates for nodes
references/examples  <- example nodes
docs/                <- human-readable docs (en + zh)
```

### Testing

```bash
# Syntax check all scripts
for f in scripts/*.py; do python3 -m py_compile "$f"; done

# Run pytest
pytest scripts/tests/

# Smoke-test the CLI
./scripts/wiki --help
```

## Submitting changes

1. **Fork** the repo.
2. **Branch** from `main`: `git checkout -b feat/your-feature`.
3. **Make changes.** Follow the existing style:
   - Docstrings use `"""..."""` at module top with usage example.
   - All scripts start with `#!/usr/bin/env python3`.
   - All functions use type hints (Python 3.10+ syntax).
4. **Run tests** — they must pass.
5. **Run lint**: `wiki lint` (against your test wiki).
6. **Update CHANGELOG.md** under `[Unreleased]`.
7. **Commit**: prefer [Conventional Commits](https://www.conventionalcommits.org/) prefixes (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`).
8. **Push** and open a **Pull Request** against `main`.

### What NOT to change without discussion

- The **11 Iron Rules**. These are non-negotiable design pillars.
- The **JSON-Schema** definitions (changing a field type is breaking).
- The **CLI surface** (renaming `wiki` subcommands is breaking).

For any of these, open an issue first.

## Documentation

- English docs live in `docs/en/`.
- Chinese docs live in `docs/zh/`.
- Both must be updated together (the README links both).

If you translate to a new language, follow the pattern `*.zh.md` and add a row to the table in both `README.md` and the corresponding `docs/<en|zh>/README.md`.

## Release process

The maintainer cuts releases on demand (no fixed cadence):

1. Bump version in `pyproject.toml`.
2. Move `[Unreleased]` → versioned section in `CHANGELOG.md`.
3. Tag: `git tag -a v1.2.0 -m "Release 1.2.0"`.
4. Push tags: `git push --tags`.
5. Create GitHub release with the CHANGELOG excerpt.

## License

By contributing, you agree that your contributions will be licensed under the **MIT License** (see `LICENSE`).

---

Thank you again — every PR makes the wiki a little better for everyone. 🌱