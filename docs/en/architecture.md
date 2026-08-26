# Architecture

> **How the wiki is structured, why those choices, and what each piece does.**

**Languages:** [English](./architecture.md) | [中文](../zh/architecture.md)

---

## The 11 Iron Rules

These are non-negotiable. Every other design choice flows from them.

| # | Rule | What it forbids |
|---|---|---|
| 1 | **RAW IS IMMUTABLE** | Editing `raw/<citekey>/full.md` (Zotero / MinerU outputs are write-once) |
| 2 | **MARKDOWN IS THE SOURCE OF TRUTH** | Putting wiki content in databases; JSON is only a temporary buffer |
| 3 | **LLM EXTRACTS, SCRIPTS VALIDATE** | Asking scripts to do semantic tasks, or asking LLMs to do mechanical ones |
| 4 | **NO REGEX ON MEANING** | Writing regexes to extract any semantic field (numbers, names, claims) |
| 5 | **PROGRESSIVE DISCLOSURE** | Frontmatter shows everything visible; body uses Transclusion for on-demand detail |
| 6 | **CONTEXT OPTIMIZATION** | Loading whole papers into LLM context when only a section is needed |
| 7 | **EVERY FACT HAS PROVENANCE** | A claim or evidence without a paper + section + page reference |
| 8 | **EVERY NUMBER IS VERIFIABLE** | A numeric value that `grep` cannot find in `raw/full.md` |
| 9 | **CLAIM ≠ PAPER CONCLUSION** | Treating the paper's conclusion as a `claim` node |
| 10 | **HUMAN REVIEWS PENDING** | LLM writing directly to `papers/`, `claims/`, or `evidence/` |
| 11 | **GRAPH EDGES ARE TYPED & CONFIDENT** | Untyped edges (a wikilink with no `supports`/`contradicts`/`qualifies` + confidence) |

---

## Node Architecture (5 core + 2 auxiliary + raw)

### Core nodes (5)

```
┌──────────────┐
│  paperinfo   │  ──bibliographic──>  paper
└──────────────┘                          │
                                          ▼
                                       claim ◀──── cross-paper ────► claim
                                          ▲                            ▲
                                          │                            │
                                       evidence                    evidence
                                          │                            │
                                          ▼                            ▼
                                       paper ──> paper ──> paper ──> ...
                                       (raw full.md is the source)
```

| Node | One per | Frontmatter anchors |
|---|---|---|
| `paperinfo` | paper | DOI, journal, abstract, authors, year |
| `paper` | paper | `paperinfo:` link + `raw_path:` + `claims:` list |
| `claim` | topic (cross-paper) | `related_papers:` + `supports/contradicts/qualifies_evidence:` |
| `evidence` | fact | 11 `verify_*` fields + `prov_source_text:` |
| `synthesis` | topic (long-form) | `related_claims:` + thematic narrative |

### Auxiliary nodes (2)

- **`topic/`** — Landing page that aggregates related claims, evidence, and syntheses around a tag (e.g. `topic/dm-network.md`). Created only when ≥3 related claims exist.
- **`00-pending/`** — LLM staging buffer. Not a "real" node directory — it's the human review zone (Iron Rule #10).

### Raw layer

```
raw/<citekey>/full.md       # the only authoritative source for all numbers/quotes
raw/<citekey>/images/       # extracted figures (optional)
raw/<citekey>/tables/       # extracted tables (optional)
```

Raw files are **never** modified after they enter this directory.

---

## The Extraction Pipeline (T0–T4)

| Stage | Time | What | Output |
|---|---|---|---|
| T0 · Ingest | ~30s | Copy paper into `raw/`, derive citekey | `raw/<citekey>/full.md` |
| T1 · Scan | ~30s | Read paper, identify sections, compute char density | `sections.json` |
| T2 · Extract | ~5–8m | Write claim/evidence JSON skeletons | `00-pending/<citekey>/claims/*.json` + `evidence/*.json` |
| T3 · Evidence | ~3m | Add 11 verify_* fields, find prov_source_text in raw | `evidence/*.json` (filled) |
| T4 · Audit | ~2m | Adversarial: did the LLM invent numbers? | `audit_report.md` |

LLM writes JSON → scripts convert to Markdown → human reviews in `00-pending/` → `wiki promote` moves to `papers/`, `claims/`, `evidence/`.

---

## The Validation Layers (L0–L4.6)

| Layer | What it checks | Mechanical / LLM |
|---|---|---|
| **L0 Structure** | File names, directory layout, required frontmatter keys | script |
| **L0.5 Type** | All `type:` values are valid enums (paper / paperinfo / claim / evidence / synthesis / topic) | script |
| **L1 Evidence** | Every evidence has all 11 verify_* fields (filled or `null`) | script |
| **L1.5 Schema** | JSON-Schema validation against `scripts/schemas/*.json` | script |
| **L2 Semantic** | Claims are falsifiable (have `statement:` that is a complete sentence), evidence → paper backlinks exist | script + LLM |
| **L3 Consistency** | Numbers in frontmatter are grep-able in `raw/full.md` (exact / fuzzy / LaTeX-tolerant) | script (grounding) |
| **L4.6 Edges** | All edges have type (`supports`/`contradicts`/`qualifies`) + confidence (`high`/`medium`/`low`) | script |

Run: `wiki lint --layer L3` (or omit `--layer` for all).

---

## Edge Typing & Confidence

Every connection between nodes is typed:

```
evidence.supports_evidence:  [[smith-2022-dmn-fc-reduction]]      (type: supports)
                .contradicts_evidence: []
                .qualifies_evidence:  [[doe-2020-motion-confound]]  (type: qualifies)

Each evidence also carries:
    .supports_targets:    [paper-id-1, paper-id-2]   # 3 parallel arrays
    .supports_relations:  [direct, indirect]
    .supports_confidences:[high, medium]

    .contradicts_targets / .contradicts_relations / .contradicts_confidences
    .qualifies_targets  / .qualifies_relations  / .qualifies_confidences
```

Iron Rule #11 forbids untyped edges. A bare `[[wikilink]]` without a type+confidence is a lint error at L4.6.

---

## Why these choices?

| Decision | Rationale |
|---|---|
| **Plain Markdown, not DB** | Diff-able, git-able, Obsidian-renderable, future-proof (Iron Rule #2) |
| **YAML frontmatter, not JSON sidecar** | One file per node = one source of truth, no broken links |
| **`00-pending/` buffer** | LLM is fast but not always right; humans are slow but reliable (Iron Rule #10) |
| **Raw is immutable** | You can always re-extract if your extraction logic improves (Iron Rule #1) |
| **Typed edges with confidence** | The graph is *queryable* ("all evidence contradicting X with high confidence"), not just *browsable* |
| **11 verify_* fields** | Numbers are the most-fabricated content; making each one explicit + grep-verifiable stops fabrication early (Iron Rule #8) |
| **JSON-Schema validation** | LLMs produce free-form JSON; schemas force the structure to be predictable |
| **No regex on meaning** | "r = 0.65" → "r = 0 . 6 5" after LaTeX OCR; regex catches neither. LLM reads it, writes `r=0.65`. (Iron Rule #4) |

---

## Directory Layout

```
evidence-wiki-skill/                  <- the skill repo (this one)
├── README.md / README.zh.md
├── LICENSE
├── CONTRIBUTING.md
├── CHANGELOG.md
├── pyproject.toml
├── install.sh
├── docs/                              <- human-readable documentation (en + zh)
├── scripts/                           <- validation + maintenance CLI
│   ├── wiki                           <- unified CLI entry
│   ├── wiki_common.py
│   ├── wiki_lint.py                   <- L0-L4.6
│   ├── wiki_check_evidence.py         <- L3 grounding grep
│   ├── wiki_render_nodes.py           <- body table auto-render
│   ├── wiki_render_evidence_body.py   <- per-evidence auto-render
│   ├── wiki_promote.py                <- 00-pending → papers/claims/evidence
│   ├── wiki_zotero.py                 <- Zotero SQLite bridge
│   ├── ... (31 .py total)
│   ├── archive/                       <- legacy fix scripts (kept for traceability)
│   ├── schemas/                       <- JSON-Schema definitions
│   └── tests/
├── skills/                            <- 9 micro-skills (slash-commands)
├── specs/                             <- architecture documents
├── references/                        <- templates, style guide, examples
│   ├── templates/                     <- paper.md, claim.md, evidence.md, ...
│   └── examples/
└── __init__.py
```

A user wiki created by `wiki init`:

```
my-research-wiki/
├── AGENTS.md          <- the 11 iron rules (loaded by pi)
├── index.md           <- auto-generated TOC
├── log.md             <- append-only
├── paperinfo/         <- 1 .md per paper
├── raw/<citekey>/     <- immutable MinerU output
├── 00-pending/<citekey>/  <- LLM staging (Iron Rule #10)
├── papers/<citekey>.md    <- promoted paper nodes
├── claims/<slug>.md       <- promoted cross-paper claims
├── evidence/<slug>.md     <- promoted evidence nodes
├── syntheses/         <- long-form synthesis docs
└── topics/            <- topic landing pages
```

---

## When to break the rules

You don't. The rules are iron.

The only time you can "violate" a rule is during the **T0 ingest** step, where `wiki ingest` reads the raw MinerU output and copies it. After that, raw files are frozen.

If a rule is genuinely blocking your work, the right move is to **open an issue** and propose a new rule, not to silently violate an existing one.

---

## Further reading

- [Tutorial](./tutorial.md) — hands-on walkthrough
- [Micro-skills](./micro-skills.md) — the 9 slash-commands
- [Schemas](../../scripts/schemas/) — `claim.schema.json`, `evidence.schema.json`, `topic.schema.json`
- [Templates](../../references/templates/) — `paper.md`, `claim.md`, `evidence.md`