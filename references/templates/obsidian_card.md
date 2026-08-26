---
title: "{{title}}"
citekey: "{{citekey}}"
authors:
{{authors}}
year: {{year}}
venue: "{{venue}}"
doi: "{{doi}}"
url: "{{url}}"
type: {{type}}
zotero_key: "{{zotero_key}}"
created: {{today}}
tags:
  - literature-note
  - {{citekey}}
---

# {{title}}

> **{{authors}}** ({{year}}). {{title}}. *{{venue}}*. {{doi}}
> 📎 [Zotero item]({{url}}) | 🗝️ `{{citekey}}`

## Abstract

{{abstract}}

---

## Notes

<!-- LLM-extracted content goes here -->

## Linked Notes

```dataview
LIST
FROM ""
WHERE contains(authors, "{{author_short}}")
```

## Citations

```zotero
@{{citekey}}
```
