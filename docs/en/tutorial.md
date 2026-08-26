# Tutorial · A Walkthrough from Zero to Your First Evidence Node

> **Goal:** By the end of this tutorial you will have ingested one paper, extracted structured evidence, promoted it through human review, and queried it. Total time: ~20 minutes (plus the LLM extraction, which is async).

**Languages:** [English](./tutorial.md) | [中文](../zh/tutorial.md)

---

## Prerequisites

- Python ≥ 3.10
- A working LLM endpoint (Claude / GPT / pi-coding-agent with any model)
- Optional: [Obsidian](https://obsidian.md/) installed for visualization

---

## Step 0 · Install the skill

```bash
git clone https://github.com/hasibagen/evidence-wiki.git
cd evidence-wiki
pip install -e .

# Verify the CLI works
./scripts/wiki --help
```

You should see a list of subcommands: `init`, `ingest`, `lint`, `check-evidence`, `search`, `status`, `index`, `archive`, `zotero`, `zotero-csv`.

---

## Step 1 · Create your wiki

Pick any empty directory as your wiki root. **Do not** initialize inside the `evidence-wiki` repo itself — that one holds the skill code, not your data.

```bash
mkdir ~/my-research-wiki
cd ~/my-research-wiki
wiki init
```

This creates:

```
my-research-wiki/
├── AGENTS.md      # the 11 iron rules (auto-loaded by pi)
├── index.md       # auto-rebuilt TOC
├── log.md         # append-only audit log
├── paperinfo/     # bibliographic metadata
├── raw/           # immutable raw paper text (MinerU output)
├── 00-pending/    # LLM-extracted, awaiting your review
├── papers/        # published "what this paper claims" nodes
├── claims/        # cross-paper claims
├── evidence/      # specific evidence (numbers, quotes)
├── syntheses/     # long-form synthesis docs
└── topics/        # topic landing pages
```

> **Iron Rule #10 — HUMAN REVIEWS PENDING.** The `00-pending/` directory is a buffer zone. LLM writes here, humans promote. You will never lose work, but you also never let raw LLM output become a "real" node without review.

---

## Step 2 · Prepare a paper

You need a paper in **Markdown** form (MinerU output is perfect). For this tutorial we'll assume:

```
my-research-wiki/
└── raw/
    └── smith_2022_neuroimage/
        └── full.md
```

The `smith_2022_neuroimage` part is the **citekey** — a unique identifier used everywhere. Convention: `<author>_<year>_<short-journal-or-title>.md`.

> **Iron Rule #1 — RAW IS IMMUTABLE.** Once `full.md` is in `raw/`, you never edit it. All wiki nodes reference `raw/<citekey>/full.md` for provenance.

If you don't have a paper yet, you can also run `wiki ingest path/to/anywhere.md` — it will copy it into `raw/<citekey>/` for you and create a citekey.

---

## Step 3 · Ingest and extract

### 3.1 · Initialize the pending directory

```bash
wiki ingest raw/smith_2022_neuroimage/full.md
```

This:
- Detects or asks for the citekey (`smith_2022_neuroimage`)
- Creates `00-pending/smith_2022_neuroimage/`
- Generates three skeleton files:
  - `00-pending/smith_2022_neuroimage/smith_2022_neuroimage.md` (paper.md skeleton)
  - `00-pending/smith_2022_neuroimage/claims/*.md` (claim skeletons)
  - `00-pending/smith_2022_neuroimage/evidence/*.md` (evidence skeletons)

### 3.2 · Run LLM extraction

The `wiki` CLI handles mechanical steps. The **LLM extraction** is best run inside an interactive pi-coding-agent session:

```
> /extract raw/smith_2022_neuroimage/full.md
```

This triggers the **4-stage extraction pipeline**:

| Stage | What it does | Time |
|---|---|---|
| T1 · Scan | Read the paper, identify sections (Intro / Methods / Results / Discussion) | ~30s |
| T2 · Extract | For each section, write claim/evidence JSON skeletons | ~5–8 min |
| T3 · Evidence | Number each piece of evidence, add provenance (page, quote) | ~3 min |
| T4 · Audit | Adversarial review: did the LLM invent numbers? | ~2 min |

The LLM writes everything into `00-pending/smith_2022_neuroimage/`. **Nothing in `papers/`, `claims/`, `evidence/` is touched yet.**

---

## Step 4 · Human review (the most important step)

Open `00-pending/smith_2022_neuroimage/smith_2022_neuroimage.md` in your editor. It has a YAML frontmatter and a Markdown body.

### 4.1 · Check the frontmatter

```yaml
---
type: paper
citekey: smith_2022_neuroimage
title: "Smith et al. (2022). Functional connectivity in resting-state fMRI."
authors: [Smith, J., Doe, A.]
year: 2022
journal: NeuroImage
study_type: empirical_research
modality: fmri
paperinfo: "[[paperinfo/smith_2022_neuroimage]]"
raw_path: "raw/smith_2022_neuroimage/full.md"
claims:
  - "[[smith-2022-default-mode-network]]"
  - "[[smith-2022-test-retest-reliability]]"
related_evidence: []
---
```

Verify:
- ✅ `citekey` matches the directory name
- ✅ `title`, `authors`, `year`, `journal` match the paper
- ✅ `study_type` is one of `empirical_research` / `methodology` / `review` / `meta_analysis` / `empirical_computational_modeling`
- ✅ `modality` matches the imaging method (fmri / eeg / fnirs / meg / multimodal / behavioral / other)
- ✅ `raw_path` is the **relative** path to `full.md` from wiki root

### 4.2 · Check the claims

Open each claim file under `claims/`. The template is in [`references/templates/claim.md`](../../references/templates/claim.md). A claim is **your synthesis**, not the paper's conclusion. It should be falsifiable.

```yaml
---
type: claim
id: smith-2022-default-mode-network
statement: |
  Default Mode Network (DMN) functional connectivity is reduced in
  patients with major depression compared to healthy controls.
authors: [Smith, J.]
year: 2022
status: pending
related_papers:
  - "[[smith_2022_neuroimage]]"
supports_evidence:
  - "[[smith-2022-dmn-fc-reduction]]"
qualifies_evidence: []
contradicts_evidence: []
---

## Reasoning

The DMN shows reduced within-network connectivity (t = -3.45, p < 0.001)
in 42 patients vs 38 controls, after FDR correction. Effect persists
after controlling for motion (mean FD < 0.2 mm).

## Sources

- Smith et al. (2022), NeuroImage, Results §3.2
```

### 4.3 · Check the evidence

Each evidence file has **11 numeric verification fields** — sample size, test method, statistic value, effect size, 95% CI, df, p-value, etc. These are the **Iron Rule #8 — EVERY NUMBER IS VERIFIABLE** fields.

For example `evidence/smith-2022-dmn-fc-reduction.md`:

```yaml
verify_n: 80                # total sample
verify_test_method: independent_samples_t_test
verify_test_stat_type: t
verify_test_stat_value: -3.45
verify_df: 78
verify_p_value: 0.0009
verify_effect_size_type: cohens_d
verify_effect_size_value: -0.62
verify_ci_95: [-0.95, -0.29]
prov_source_text: "DMN within-network FC was reduced in patients (t₇₈ = -3.45, p = 0.0009, d = -0.62)"
```

The `wiki check-evidence` script will grep `prov_source_text` in `raw/smith_2022_neuroimage/full.md` and verify it exists:

```bash
wiki check-evidence smith_2022_neuroimage
# ✅ smith-2022-dmn-fc-reduction: prov_source_text found verbatim (fuzzy match)
# ✅ 1/1 evidence verified
```

---

## Step 5 · Promote to "real" nodes

Once you've reviewed the pending directory, promote it:

```bash
wiki promote smith_2022_neuroimage
```

This **atomically**:

1. Moves `00-pending/smith_2022_neuroimage/papers/smith_2022_neuroimage.md` → `papers/smith_2022_neuroimage.md`
2. Moves each claim → `claims/<slug>.md`
3. Moves each evidence → `evidence/<slug>.md`
4. Auto-renders body tables (`## 数值校验` / `## 支持的 Claim`)
5. Updates backlinks in related papers

The `00-pending/` directory is left empty (or you can delete it).

---

## Step 6 · Lint

```bash
wiki lint
```

Runs the **4-layer lint** (L0 → L3):

| Layer | What | Mechanical? |
|---|---|---|
| L0 Structure | File naming, directory layout, frontmatter required fields | ✅ script |
| L0.5 Type | All `type:` fields are valid enums | ✅ script |
| L1 Evidence | Every evidence has all 11 verify_* fields filled or null | ✅ script |
| L1.5 Schema | JSON-Schema validation against `scripts/schemas/*.json` | ✅ script |
| L2 Semantic | Claims are falsifiable, evidence → paper backlinks exist | ✅ script + LLM |
| L3 Consistency | Numbers in frontmatter grep-able in `raw/full.md` | ✅ script (grounding) |
| L4.6 Edges | All edges typed (`supports`/`contradicts`/`qualifies`) + confidence | ✅ script |

You should see `0 errors` for a clean wiki.

---

## Step 7 · Query

Now that you have nodes, you can query:

```bash
wiki search "default mode network depression"
```

Or use the slash-command inside pi-coding-agent:

```
> /query evidence for "DMN FC reduction in major depression"
```

This returns all `evidence/*.md` files whose `interp_text`, `prov_source_text`, or `tags` match.

---

## Step 8 · Visualize (Obsidian)

Open `my-research-wiki/` as a vault in Obsidian.

- The **graph view** shows `paper → claim ← evidence` links
- Each `[[wikilink]]` is clickable
- `tag:#dm` or `tag:#fmri` groups nodes by tag
- `tag:#needs-review` shows what's still pending

---

## What's next?

| You want to … | Use |
|---|---|
| Track a claim across papers | [`/claim`](./micro-skills.md#claim) |
| Pull bibliography into `paperinfo/` | [`/sync`](./micro-skills.md#sync) |
| Find duplicate claims | [`/stitch`](./micro-skills.md#stitch) |
| Run adversarial review on a paper | [`/audit`](./micro-skills.md#audit) |
| Build a topic landing page | [`/topic`](./micro-skills.md#topic) |
| Add custom imaging modality templates | Edit `references/templates/paper-*.md` |
| Re-extract with a different model | `pi -p "extract this paper, 8 evidence" --provider <x> --model <y>` |

For deeper understanding, read **[`architecture.md`](./architecture.md)**.

---

## Common pitfalls

1. **Forgetting to grep numbers.** `wiki check-evidence` is not optional. If the script can't find your `prov_source_text` in `raw/full.md`, the number is unverified.
2. **Treating `claim` as a paraphrase of the paper's conclusion.** Claims are *your* synthesis, often across many papers. A paper conclusion is in `papers/<citekey>.md`, not in `claims/`.
3. **Editing raw `full.md`.** Never. Iron Rule #1. If MinerU made a mistake, leave a `note:` in the pending paper.md.
4. **LLM writes to `papers/` directly.** Iron Rule #10. Everything goes to `00-pending/` first.
5. **Forgetting to commit.** This is git. Every promotion is a commit-worthy event.

---

## FAQ

**Q: Can I use this without Obsidian?**
A: Yes. Obsidian is just the renderer. The wiki is plain Markdown + YAML.

**Q: Can I use this without pi-coding-agent?**
A: Yes. The `wiki` CLI handles all mechanical steps. You can also drive extraction manually — see [`scripts/wiki_lint.py`](../../scripts/wiki_lint.py) for the validation pipeline.

**Q: Why Markdown and not SQLite?**
A: Iron Rule #2. Markdown diffs in git, renders in Obsidian, exports anywhere. SQLite is fast for queries but a black box for audit. Evidence Wiki optimizes for **auditability over speed**.

**Q: How big can my wiki get?**
A: The test wiki is at 192 papers, 870 claims, 1154 evidence nodes, all linting in < 30s. Expect linear scaling. If you hit performance issues, the bottleneck is usually the `wiki_render_evidence_body` step which re-writes every evidence file — narrow it to changed files only.

**Q: Can I import from Zotero directly?**
A: Yes. `wiki zotero list-workspaces` shows your Zotero libraries; `wiki zotero sync --collection <name>` pulls bibliographic metadata into `paperinfo/`. Full text must come from MinerU separately.

**Q: How do I cite this skill?**
A: See the README's Citation section.