---
name: Bug report
about: Something broke. Help us reproduce and fix it.
title: '[bug] '
labels: bug
assignees: ''
---

## What happened

A clear, specific description of what went wrong.

## Topic you ran lafbot on

The exact topic string you passed to `/lafbot`.

## Phase that failed

Which pipeline phase? (Check `RUN_LOG.md` in your working dir.)

- [ ] Phase 0 — Scoping
- [ ] Phase 1 — Discovery
- [ ] Phase 2 — Extraction
- [ ] Phase 3 — Clustering
- [ ] Phase 4 — Synthesis
- [ ] Phase 5 — HTML
- [ ] Phase 6 — Notes
- [ ] Drill-down
- [ ] Unknown

## Error message

Verbatim — copy/paste from the terminal or RUN_LOG, do not paraphrase.

```
PASTE HERE
```

## What you expected

What should have happened instead?

## Reproduction steps

1.
2.
3.

## Environment

- OS:
- Python version: `python3 --version`
- Claude Code version:
- YouTube MCP server version / commit:
- lafbot version (commit hash or release tag):

## Attachments

If possible, attach the `RUN_LOG.md` from your failed run. **Remove any sensitive info** (API keys, private vault paths, etc.) before posting.

## Anything else

Logs, screenshots, related issues.
