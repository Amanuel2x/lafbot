---
name: lafbot
description: Learn Anything Fast. A robust, subject-agnostic multi-agent research pipeline for any topic. Searches YouTube, extracts insights from transcripts AND viewer comments, builds a semantic knowledge graph, identifies consensus and anomalies, and produces a self-contained HTML report plus markdown notes that integrate into any Obsidian-style vault. Works on any subject — marketing, psychology, persuasion, technical topics, history, philosophy, niche skills — without hardcoded keywords. Each run grows a persistent cross-topic knowledge graph. Supports drill-down mode for digging deeper on a specific finding from a previous run. Examples — "/lafbot the psychology of attention", "/lafbot how to grow a B2B SaaS waitlist", "/lafbot drill saas-marketing/loom-video-outreach".
---

# lafbot — Learn Anything Fast

A production-grade research pipeline that turns YouTube into a structured knowledge graph for any topic.

The output is NEVER a generic web summary. It's a synthesis of consensus claims, anomaly claims, and "from the comments" insights extracted from real creator transcripts and viewer discussion — all clustered semantically per-topic, not via hardcoded keywords.

## Core principles

1. **Subject-agnostic.** No hardcoded keywords, axes, or stages. Every artifact is inferred from the topic and the actual data.
2. **Evidence-traceable.** Every claim in the report links back to a verbatim quote and a video URL.
3. **Robust.** JSON schema validation per agent output, retry-on-failure, false-positive detection.
4. **Iterative.** Drill-down mode lets you triple-click on any anomaly to spawn a focused mini-run.
5. **Cumulative.** All runs feed a master knowledge graph in the vault, so cross-topic patterns surface over time.

## Pipeline overview

```
Phase 0 (Scoping)         ← user input + axis inference
       ↓
Phase 1 (Discovery)       ← 1 Haiku agent: search → rank → ~65 videos
       ↓
Phase 2 (Extraction)      ← 10 Sonnet agents in parallel: transcript + comments → tactics JSON
       ↓                     [JSON validation + retry per agent]
Phase 3 (Clustering)      ← 1 Sonnet "Cluster Architect" agent: semantic dedup → canonical clusters
       ↓                     [false-positive detection]
Phase 4 (Synthesis)       ← Opus (main thread): TLDR + contradictions + anomalies + graph
       ↓
Phase 5 (Report)          ← Generic HTML builder reads dataset.json
       ↓
Phase 6 (Notes)           ← Markdown notes into vault + update master graph
```

Each phase is documented in detail in its own file under `pipeline/`. Read those when running the phase — not all at once.

## When to use

- User asks for research on a topic where video creators are a strong signal source.
- User wants both "what everyone says" AND "what's contrarian / underrepresented."
- User wants an artifact (HTML + vault notes) they can keep, not just a chat answer.

## When NOT to use

- Topic is academic / peer-reviewed-source-only — use WebSearch + scholarly sources instead.
- User wants a quick chat answer — this is heavy (30-60 min, multi-agent, ~$5-15 in tokens).
- YouTube coverage of the topic is genuinely sparse (very technical niche, obscure history).

## Prerequisites (check before starting)

1. **YouTube MCP installed and Connected.** Run `claude mcp list`. If the `youtube` server isn't Connected, stop and instruct the user to follow `docs/youtube-api-setup.md`. They need their OWN YouTube Data API v3 key from Google Cloud Console — never share keys. Required MCP tools: `mcp__youtube__search_videos`, `mcp__youtube__get_clean_transcript`, `mcp__youtube__get_video_comments`, `mcp__youtube__get_video_metadata`.

2. **Vault location.** Resolve the working directory in this order:
   - If `LAFBOT_VAULT` environment variable is set, use that.
   - Else if `~/.lafbotrc` exists with a `vault_path:` line, use it.
   - Else default to `~/lafbot-research/` (create if missing).
   - On first run, confirm the path with the user. Save their choice to `~/.lafbotrc` so future runs don't ask again.

3. **Python 3.9+** for the scripts. Run `python3 --version` to verify.

## Invocation modes

### Full run (default)
`/lafbot <topic>` — runs the full 6-phase pipeline.

### Drill-down
`/lafbot drill <topic-slug>/<cluster-slug>` — spawns a focused mini-run on one cluster from a prior topic. See `pipeline/drill.md`.

Example: `/lafbot drill saas-marketing/loom-video-outreach` pulls 5-10 more videos specifically about Loom video DM outreach, extracts deeper tactics, and appends to the existing report.

### Dry run
`/lafbot --dry-run <topic>` — runs Phases 0-1 only (scoping + discovery), reports the video list, and stops. Lets the user inspect/prune before paying for Phase 2.

## Phase-by-phase docs

When executing each phase, READ the corresponding `pipeline/*.md` file. Each is self-contained and includes the agent prompt templates, JSON schemas, model assignments, and error handling.

| Phase | Doc | Model |
|-------|-----|-------|
| 0 — Scoping | `pipeline/00_scoping.md` | Main thread + 1 Haiku axis-inference agent |
| 1 — Discovery | `pipeline/01_discovery.md` | 1 Haiku agent |
| 2 — Extraction | `pipeline/02_extraction.md` | 10 Sonnet agents in parallel |
| 3 — Clustering | `pipeline/03_clustering.md` | 1 Sonnet Cluster Architect agent |
| 4 — Synthesis | `pipeline/04_synthesis.md` | Opus (main thread) |
| 5 — Report | `pipeline/05_html.md` | Main thread runs `scripts/build_html.py` |
| 6 — Notes | `pipeline/06_notes.md` | Main thread runs `scripts/build_notes.py` + `scripts/update_master_graph.py` |
| Drill-down | `pipeline/drill.md` | 1 Sonnet agent (focused) |

## Cost and time

- Full run: 30-60 min wall time, ~$8-15 in tokens (medium comment depth).
- Drill-down: 5-10 min, ~$1-2.

If the user is budget-sensitive, you can downgrade Phase 2 agents to Haiku (cheaper but loses nuance in tactic extraction). Default is Sonnet.

## Failure modes and recovery

- **MCP not connected**: stop early, instruct user to set up the YouTube MCP per `docs/youtube-api-setup.md`.
- **YouTube quota exhausted (10k units/day default)**: stop and tell user to wait until tomorrow or request a quota increase in Google Cloud Console. A full run uses ~1,500-3,000 units.
- **Extraction agent returns malformed JSON**: re-run that single agent with the same slice (cheap). Failure isolated to one slice doesn't kill the pipeline.
- **Cluster Architect produces obviously bad clusters** (>30% unclassified, or single cluster claiming >50% of tactics): re-prompt with a tighter constraint, or fall back to per-creator inspection.
- **Pipeline crashes mid-run**: every phase writes its output to disk before the next starts. To resume, look at which file is missing and re-run only that phase.

## Output artifacts (per run)

Every run produces a folder at `{vault_dir}/Research-{topic-slug}-{YYYY-MM-DD}/` containing:

- `Deep-Research-Report.html` — the main artifact, self-contained, opens offline.
- `00-Index.md` — Obsidian entry point.
- One `.md` per cluster category.
- `Anomalies.md`, `From-the-Comments.md`, `Contradictions.md`, `Per-Axis-Playbook.md` — cross-cutting notes.
- `dataset.json` — canonical structured data.
- `discovery.json`, `extraction-*.json`, `clusters.json` — raw pipeline intermediates (useful for drill-downs and debugging).
- `RUN_LOG.md` — what each phase did, how long it took, what failed.

And updates the master graph at: `{vault_dir}/Research-Master-Index.md` + `Research-Master-Graph.json`.

## Universal rule

Read the relevant `pipeline/*.md` file BEFORE executing that phase. Don't try to do everything from memory of this file. Each phase doc has the specific JSON schemas, prompt templates, and edge cases the orchestrator file deliberately doesn't.
