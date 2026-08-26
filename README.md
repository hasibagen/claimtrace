# Evidence Wiki Skill

> **A long-term maintenance skill for academic evidence wikis** — paper → claim → evidence nodes, LLM-extracted JSON, script-validated markdown, Obsidian-native cross-links.

[中文版本](./README.zh.md) | [Documentation](./docs/en/README.md) | [Tutorial](./docs/en/tutorial.md)

[![Python](https://img.shields.io/badge/python-3.10%2B-blue)]() [![License: MIT](https://img.shields.io/badge/license-MIT-green)]() [![Stars](https://img.shields.io/github/stars/hasibagen/evidence-wiki)]()

---

## What is this?

**Evidence Wiki Skill** is a structured system for turning the papers you read into a **queryable, traceable knowledge graph** stored as plain Markdown files. It is designed for individual researchers who read hundreds of papers and want a sustainable, long-term personal knowledge base — not a one-off summary.

**Three design pillars:**

1. **Markdown is the source of truth.** Every node is a plain `.md` file with YAML frontmatter. No databases, no proprietary formats. Diff-able, git-able, Obsidian-renderable.
2. **LLM extracts meaning, scripts validate mechanics.** LLMs are good at reading papers and writing structured JSON; scripts are good at enforcing schemas, fixing YAML, and grepping quotes. Each does what it is good at.
3. **Raw sources are immutable.** Your Zotero library and MinerU outputs are never modified. Everything the wiki produces lives in its own directory.

**The 11 Iron Rules** (full list in [`docs/en/architecture.md`](./docs/en/architecture.md)):

> RAW IS IMMUTABLE · MARKDOWN IS THE SOURCE OF TRUTH · LLM EXTRACTS, SCRIPTS VALIDATE · **NO REGEX ON MEANING** · PROGRESSIVE DISCLOSURE · CONTEXT OPTIMIZATION · EVERY FACT HAS PROVENANCE · EVERY NUMBER IS VERIFIABLE · CLAIM ≠ PAPER CONCLUSION · HUMAN REVIEWS PENDING · GRAPH EDGES ARE TYPED & CONFIDENT

---

## Why use it?

| Problem with "normal" literature notes | How Evidence Wiki solves it |
|---|---|
| Notes are scattered across apps (Notion, Word, …) | One Obsidian vault, plain files, future-proof |
| You read a paper a year later and forget why it mattered | Each claim has provenance: who said it, what evidence, how strong |
| Numbers in your notes drift from the paper | Every number is grep-verified against `raw/full.md` |
| Claims are paraphrased, paper conclusions lost | `claim` (your synthesis) is a separate node from `paper.md` (the authors' conclusion) |
| Cross-paper synthesis is hard | Typed edges (`supports` / `contradicts` / `qualifies`) with confidence (`high` / `medium` / `low`) |
| LLM hallucinations sneak in | LLM writes to `00-pending/` (human review buffer); only after you read it does it become a real node |

---

## Quick start

### Prerequisites

- Python ≥ 3.10
- [Obsidian](https://obsidian.md/) (optional but recommended)
- An LLM (any provider) for the extraction step — pi-coding-agent, Claude, GPT, etc.

### Install

```bash
git clone https://github.com/hasibagen/evidence-wiki.git
cd evidence-wiki
pip install -e .

# Optional: integrate with pi-coding-agent (installs the 5 extension tools)
./install.sh
```

The `install.sh` script:

- Creates symlinks for the 5 wiki tools into your pi-coding-agent extensions directory
- Sets up the slash-command prefix for the 9 micro-skills
- Does **not** touch your existing data

### Initialize a new wiki

```bash
mkdir my-research-wiki
cd my-research-wiki
wiki init          # creates AGENTS.md, index.md, log.md, directory skeleton
```

### Ingest your first paper

```bash
# Drop a MinerU-processed full.md into your vault, then:
wiki ingest path/to/paper.md
```

This runs a **6-stage pipeline**:

1. Place paper into `00-pending/<citekey>/`
2. Frontmatter + claim/evidence JSON skeletons
3. LLM extracts (via `/extract` slash-command)
5. Auto-render body tables
6. Audit, lint, link

For the full walkthrough, see **[`docs/en/tutorial.md`](./docs/en/tutorial.md)**.

---

## What you get

```
my-research-wiki/
├── AGENTS.md              # The 11 iron rules (loaded by pi)
├── index.md               # Auto-generated TOC
├── log.md                 # Append-only audit log
├── paperinfo/             # Bibliographic metadata (one node per paper)
├── raw/<citekey>/         # Raw MinerU full.md (immutable)
├── 00-pending/<citekey>/  # LLM-extracted, awaiting human review
├── papers/<citekey>.md    # The published "what this paper claims" node
├── claims/<slug>.md       # Cross-paper claims (your synthesis)
├── evidence/<...>.md      # Specific evidence (numbers, quotes)
├── syntheses/             # Long-form synthesis documents
└── topics/                # Topic-tagged entry points
```

Obsidian renders this natively. The graph view shows how claims connect across papers.

---

## Documentation

| | English | 中文 |
|---|---|---|
| **Tutorial** | [docs/en/tutorial.md](./docs/en/tutorial.md) | [docs/zh/tutorial.md](./docs/zh/tutorial.md) |
| **Architecture** | [docs/en/architecture.md](./docs/en/architecture.md) | [docs/zh/architecture.md](./docs/zh/architecture.md) |
| **Micro-skills** | [docs/en/micro-skills.md](./docs/en/micro-skills.md) | [docs/zh/micro-skills.md](./docs/zh/micro-skills.md) |
| **Schemas** | [specs/](./specs/) | — |
| **Templates** | [references/templates/](./references/templates/) | — |

---

## The 9 micro-skills

Each is a specialized sub-routine for one wiki operation. Invoke via slash-command:

| Slash command | What it does |
|---|---|
| `/extract` | Run the 4-stage extraction pipeline on a `full.md` |
| `/claim` | Track a claim across multiple papers |
| `/evidence` | Promote a specific piece of evidence to a node |
| `/topic` | Build a topic landing page from related claims |
| `/query` | Search the wiki for evidence about X |
| `/lint` | Run the 4-layer lint pass |
| `/sync` | Sync Zotero library → `paperinfo/` |
| `/stitch` | Deduplicate similar claims across papers |
| `/audit` | Critical adversarial review of a paper |

> Note: `/dedup` is implemented as a CLI script (`wiki_dedup_papers.py`), not a micro-skill. See [`scripts/wiki_dedup_papers.py`](./scripts/).

See **[`docs/en/micro-skills.md`](./docs/en/micro-skills.md)** for detailed usage.

---

## License

MIT — see [`LICENSE`](./LICENSE).

## Contributing

See [`CONTRIBUTING.md`](./CONTRIBUTING.md). Bug reports and PRs welcome.

## Citation

If you use this skill in published research, please cite it (placeholder — DOI will be added once archived):

```bibtex
@software{evidence_wiki_skill,
  author = {hasibagen},
  title = {Evidence Wiki Skill: Long-term Maintenance of Academic Evidence Graphs},
  year = {2026},
  url = {https://github.com/hasibagen/evidence-wiki}
}
```