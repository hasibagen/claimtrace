# ClaimTrace Demo Vault

A **complete, machine-validated mini wiki** built from 3 fictional fNIRS papers.

> [!WARNING]
> All three papers in this vault are **synthetic** (written for this demo).
> Authors, journals, DOIs (`10.0000/...`), results and statistics are invented.
> Never cite them.

## What to look at

| Start here | What it shows |
|---|---|
| [`index.md`](index.md) | The vault's entry point — everything reachable by wikilink |
| [`claims/caffeine-restores-wm-accuracy-after-total-sleep-deprivation.md`](claims/caffeine-restores-wm-accuracy-after-total-sleep-deprivation.md) | A claim node: atomic statement, scope, reasoning bridge, typed edges |
| [`evidence/chen-2024-caffeine-3back-accuracy.md`](evidence/chen-2024-caffeine-3back-accuracy.md) | An evidence node: verbatim quote + stats + provenance (section-level) |
| [`syntheses/does-caffeine-improve-working-memory.md`](syntheses/does-caffeine-improve-working-memory.md) | Cross-paper synthesis: Evidence × Claim matrix, GRADE, ABT narrative |
| [`raw/chen_2024_neurophotonics/full.md`](raw/chen_2024_neurophotonics/full.md) | The immutable source layer every quote greps back to |

## The 30-second trace

The core promise of ClaimTrace: **every claim traces back to a verbatim quote
that you can verify with grep**.

1. Open the claim above — its `evidence_targets` points to `[[chen-2024-caffeine-3back-accuracy]]`.
2. Open that evidence — `prov_source_text` holds the verbatim sentence, `prov_section` says where it lives.
3. Verify it against the raw source:

```bash
grep -F "3-back accuracy was higher after caffeine" raw/chen_2024_neurophotonics/full.md
```

That check — plus 7 more layers (naming, schema, semantics, numeric grounding,
wikilink integrity, …) — is what `wiki lint` automates, and what the repo's CI
runs on this vault on every push:

```bash
python scripts/wiki_common.py lint --wiki-root demo
# ✓ All 8 layer(s) clean
```

## How the demo was built

```
synthetic raw full.md ×3  (MinerU-style markdown, hand-written)
        │
        ├─ paperinfo ×3   (Zotero-style metadata)
        ├─ papers ×3      (structured reading notes + transclusion index)
        ├─ claims ×4      (atomic propositions, typed edges)
        ├─ evidence ×4    (verbatim quotes, stats, provenance)
        ├─ topic ×1       (map of content)
        └─ synthesis ×1   (Evidence × Claim matrix, GRADE, ABT)
                │
   wiki_render_nodes.py  → bodies rendered from frontmatter
   wiki_normalize_terms.py → terminology gate
   wiki lint --wiki-root demo → 8/8 layers clean
```

Everything under `papers/ claims/ evidence/` was produced with the **same
toolchain you would use on real papers** — the demo is not mocked up, it is
generated and validated by the repo's own scripts (see
[`.github/workflows/ci.yml`](../.github/workflows/ci.yml)).
