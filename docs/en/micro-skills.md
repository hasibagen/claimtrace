# The 9 Micro-Skills

> Each micro-skill is a specialized sub-routine for one wiki operation. Invoke via slash-command inside pi-coding-agent.

**Languages:** [English](./micro-skills.md) | [中文](../zh/micro-skills.md)

---

## 1. `wiki-extract-paper` · `/extract`

**What:** Run the 5-stage extraction pipeline on one `full.md`.

**When to use:**
- You have a new paper to ingest
- A paper was extracted long ago and you want a deeper re-extract
- User says: "处理这篇论文", "/extract full.md", "extract this paper"

**Modes:**

| Mode | Use for | Time |
|---|---|---|
| `quick-scan` | Review papers / methodology papers | ~1–2 min |
| `deep-read` | Empirical papers you need to cite from | ~5–10 min |
| `audit` | Re-examining an old extraction | ~3–5 min |

**Example:**

```
> /extract raw/zhang_2021_fnirs/full.md --mode deep-read
```

**NOT for:** creating a single evidence (use `wiki-build-evidence`), searching the wiki (use `wiki-query-evidence`).

---

## 2. `wiki-build-claim` · `/claim`

**What:** Create one claim (atomic proposition) that may span multiple papers.

**When to use:**
- You notice the same finding appears in 3 papers and want a canonical claim
- User says: "建一个 claim", "/claim", "this is a cross-paper finding"

**Output:** `claims/<semantic-slug>.md` (no internal numbering, prefers Chinese + real spaces).

**Frontmatter anchors:**

```yaml
type: claim
statement: |
  <one falsifiable proposition>
claim_type: empirical_result
atomic: true
scope_species: human
scope_n: 80
scope_age_mean: 35
scope_condition: major_depressive_disorder
reasoning: <why this claim is defensible>
reasoning_type: cross_paper_synthesis
related_papers: [[paper1]], [[paper2]]
supports_evidence: [[ev1]], [[ev2]]
qualifies_evidence: [[ev3]]
contradicts_evidence: []
```

**NOT for:** reading/answering questions (use `wiki-query-evidence`), cross-paper merge of existing claims (use `wiki-stitch-knowledge`).

---

## 3. `wiki-build-evidence` · `/evidence`

**What:** Promote a specific quote / number from a paper to a typed evidence node.

**When to use:**
- You find a number/quote worth tracking
- User says: "这是事实", "/evidence", "promote this to evidence"

**Output:** `evidence/<author>-<year>-<slug>.md`

**Required frontmatter (Iron Rule #8 — EVERY NUMBER IS VERIFIABLE):**

```yaml
fact_type: empirical_result   # or observation / methodology
observation: |
  <verbatim quote, ≥20 characters>
interp_text: |
  <your interpretation in plain language>
prov_paper: "[[smith_2022_neuroimage]]"
prov_section: "Results §3.2"
prov_page: 6
prov_source_text: "DMN FC was reduced (t₇₈ = -3.45, p = 0.0009, d = -0.62)"
verify_n: 80
verify_test_method: independent_samples_t_test
verify_test_stat_type: t
verify_test_stat_value: -3.45
verify_df: 78
verify_p_value: 0.0009
verify_effect_size_type: cohens_d
verify_effect_size_value: -0.62
verify_ci_95: [-0.95, -0.29]
verify_p_method: frequentist
```

**Verification:**

```bash
wiki check-evidence smith-2022-dmn-fc-reduction
# ✅ prov_source_text found verbatim in raw/smith_2022_neuroimage/full.md (fuzzy match)
```

---

## 4. `wiki-build-topic` · `/topic`

**What:** Create a topic landing page (Map of Content) that aggregates related claims.

**When to use:**
- 2+ papers share a theme
- User says: "建主题", "/topic default mode network", "tag this with #dm"

**Lazy rule:** Don't create a topic until ≥2 claims are related. Topics are *aggregation views*, not data nodes — they only organize references.

**Output:** `topics/<topic-slug>.md`

**Frontmatter:**

```yaml
type: topic
name: "Default Mode Network"
tags: [fmri, depression, dm]
related_claims:
  - "[[smith-2022-dmn-fc-reduction]]"
  - "[[doe-2020-dmn-altered-connection]]"
related_evidence: []
related_papers:
  - "[[smith_2022_neuroimage]]"
  - "[[doe_2020_jneurosci]]"
```

**NOT for:** single-paper organization (use the topic-related fields in `paper.md`), creating claims/evidence.

---

## 5. `wiki-query-evidence` · `/query`

**What:** Answer a research question by reading existing claim + evidence + topic + synthesis nodes.

**When to use:**
- "X 的证据?" / "What evidence for X?"
- "DMN 在抑郁里怎么变?"
- User says: "/query", "/ask"

**Pipeline:**

1. Read `index.md` to find candidate nodes
2. Read the candidate `evidence/*.md` and `claims/*.md`
3. Build an Evidence × Claim matrix
4. Generate a synthesis answer
5. Optionally persist as `syntheses/<question-slug>.md`

**Example:**

```
> /query "DMN functional connectivity reduction in major depression"
```

Output:
```
Found 3 papers / 5 evidence / 2 claims / 1 topic matching.

Evidence:
  ✅ smith-2022-dmn-fc-reduction (Smith 2022, NeuroImage): t=-3.45, d=-0.62, n=80
  ✅ doe-2020-dmn-altered (Doe 2020, J Neurosci): β=-0.31, p<0.001, n=120
  ⚠️  chen-2018-dmn-review (Chen 2018, meta): narrative summary, no effect size

Claims:
  ✅ smith-2022-default-mode-network: "DMN FC reduced in MDD vs HC"
  ⚠️  doe-2020-dmn-heterogeneity: "DMN effect varies by depression subtype"

Topics: topic/dm-network.md (default mode network)
```

**NOT for:** creating new nodes.

---

## 6. `wiki-lint-wiki` · `/lint`

**What:** Run the 4-layer lint pass with no writes.

**When to use:**
- After promoting a paper
- Before committing
- User says: "/lint", "检查 wiki", "lint"

**Layers:**

| Layer | What | Mechanical? |
|---|---|---|
| L0 | File naming + directory layout | ✅ |
| L0.5 | `type:` enum | ✅ |
| L1 | Evidence 11 verify_* fields | ✅ |
| L1.5 | JSON-Schema | ✅ |
| L2 | Semantic relations + LLM judges | mixed |
| L3 | Grounding grep into `raw/` | ✅ |
| L4.6 | Typed edges + confidence | ✅ |

**Example:**

```bash
wiki lint
# L0: 0 errors
# L0.5: 0 errors
# L1.5: 0 errors
# L2: 0 errors
# L3: 332 errors (all: raw/<filename> missing — needs MinerU re-extraction)
# L4.6: 0 errors
```

**Filter by layer:**

```bash
wiki lint --layer L3
wiki lint --layer L0.5,L1.5
```

---

## 7. `wiki-zotero-sync` · `/sync`

**What:** Sync your Zotero library → wiki's `paperinfo/` directory.

**When to use:**
- You added papers to Zotero and want them in the wiki
- User says: "/sync", "zotero 同步", "pull new papers"

**Pipeline:**

1. Read `~/Zotero/zotero.sqlite` (no network)
2. Match citekeys (Zotero item key → wiki citekey)
3. For new papers, create `paperinfo/<citekey>.md`
4. For existing, incrementally update using `zotero-lastmod` fingerprint
5. Flag conflicts for human review

**Example:**

```
> /sync collection="twin-brain"
```

Output:
```
Found 158 papers in Zotero collection "twin-brain"
  - 142 already in wiki (unchanged)
  -  11 new (created paperinfo/*.md)
  -   5 updated (lastmod newer than wiki)
  -   0 conflicts
```

---

## 8. `wiki-stitch-knowledge` · `/stitch`

**What:** Find and merge cross-paper duplicate claims.

**When to use:**
- After a batch extraction
- When you suspect two claims say the same thing
- User says: "/stitch", "去重", "merge similar claims"

**Pipeline:**

1. Embed all `claims/*.md` (semantic vectors)
2. Find clusters with cosine similarity > 0.85
3. LLM judges whether each pair is *semantically equivalent* (not just similar)
4. Merge: pick canonical claim, wire evidence via `same_claim_as` edge
5. Update `verify_supporting_count` / `verify_contradicting_count`

**Critical:** Uses **LLM judgment**, not string matching. "DMN reduced in depression" and "Depression shows lower DMN connectivity" are detected as duplicates even though their text differs (Iron Rule #4 — NO REGEX ON MEANING).

---

## 9. `wiki-audit-paper` · `/audit`

**What:** Critical adversarial review of one paper/node. Goes beyond mechanical L4.6 lint.

**When to use:**
- You want to challenge a paper's claims
- 30-day recheck
- User says: "/audit", "审阅", "challenge this"

**Pipeline:**

1. Load the paper + its claims + its evidence
2. Run 8–10 fixed adversarial questions:
   - Are the claims **falsifiable**?
   - Does every numeric value **grep** in raw?
   - Are the **edge types** correct? (A `contradicts` that should be `qualifies`?)
   - Is the **scope** consistent? (claim about "humans", evidence from "rats"?)
   - Does the LLM extraction **omit** findings that disagree?
   - Are the **provenance pages** correct?
   - Is the **sample size** consistent across claim and evidence?
   - Does the **paper conclusion** leak into a claim node? (Iron Rule #9)
3. Write the answers + an optional **我的判断** section to `audit_report.md`

**Example:**

```
> /audit papers/zhang_2021_fnirs.md
```

Output:
```
Audit report: zhang_2021_fnirs.md
  ✅ Claims are falsifiable
  ✅ All numbers grep-verifiable in raw
  ⚠️  E3 has verify_df=null but paper reports F(2,38)=4.51 (df not extracted)
  ⚠️  C2 conflates "statistical significance" with "practical significance"
  ✅ No paper-conclusion leakage
  → Audit file: 00-pending/zhang_2021_fnirs/audit.md
```

---

## Quick reference table

| Skill | Slash | Writes? | LLM? | Time |
|---|---|---|---|---|
| `wiki-extract-paper` | `/extract` | yes | yes | 5–10 min |
| `wiki-build-claim` | `/claim` | yes | yes | ~30s |
| `wiki-build-evidence` | `/evidence` | yes | yes | ~30s |
| `wiki-build-topic` | `/topic` | yes | yes | ~30s |
| `wiki-query-evidence` | `/query` | optional | yes | ~1 min |
| `wiki-lint-wiki` | `/lint` | no | partial | < 30s |
| `wiki-zotero-sync` | `/sync` | yes | no | ~5s |
| `wiki-stitch-knowledge` | `/stitch` | yes | yes | ~2 min |
| `wiki-audit-paper` | `/audit` | yes | yes | ~2 min |
## 10 · `wiki-extract-modeling` — `/modeling` · 建模拆解

**Trigger:** `建模拆解 [论文]` / `/modeling <citekey>` — for modeling papers (train/val/test protocols matter).

**What it does:** Deep-read of the *training–validation–test protocol*: data splits,
leakage controls, evaluation metrics, baselines. Produces a `## 建模拆解` section in the
paper node (with a mermaid pipeline diagram, a three-level explanation, and red flags),
plus the corresponding claims/evidence.

**When:** Modeling-type papers only (keyword + exclusion screening, e.g. exclude pure
decoding papers where the protocol is trivial). Registered in the modeling-paper
registry once ≥5 papers accumulate.
