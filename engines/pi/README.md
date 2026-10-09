# Engine pack: pi coding agent

ClaimTrace is engine-agnostic (see [`INVOKE.md`](../../INVOKE.md)), but it grew up
inside the [pi](https://github.com/badlogic/pi-mono) coding agent, whose integration
files are collected here:

```
engines/pi/
├── prompts/            # 10 slash-commands (/extract /claim /evidence /topic /query
│                       #  /lint /sync /stitch /audit /batch /migrate)
└── extensions/
    └── wiki-tools.ts   # 5 custom tools exposed to pi:
                        #   wiki_check_wikilinks · wiki_match_paperinfo
                        #   wiki_zotero_sync · wiki_status · wiki_render
```

## Wiring

```bash
# inside your vault (which contains the claimtrace checkout as .skill/ — see install.sh)
mkdir -p ~/.pi/prompts ~/.pi/extensions
cp engines/pi/prompts/*.md   ~/.pi/prompts/
cp engines/pi/extensions/wiki-tools.ts ~/.pi/extensions/
```

Batch extraction goes through the engine-agnostic runner:

```bash
.skill/scripts/wiki_run_extract.sh --engine pi -- <citekey> ...
```
