# Phase 6 — Vault notes + master graph

Goal: write Obsidian-compatible markdown notes into the working dir, then update the cross-run master knowledge graph.

## Prerequisites

- `dataset.json` and the narrative files exist.

## Steps

### 6.1 Generate per-run notes

```bash
python3 {SKILL_DIR}/scripts/build_notes.py {WORKING_DIR}
```

This writes the following files into the working dir:

- `00-Index.md` — entry point, table of contents
- One `.md` per cluster CATEGORY (e.g. `Cold-Outbound.md`, `Psychology.md`) with all clusters in that category and their quotes
- `Anomalies.md` — anomaly clusters with framing
- `From-the-Comments.md` — commenter insights
- `Contradictions.md` — disagreements
- `Per-Stage-Playbook.md` (or whatever the stage axis name is) — clusters grouped by primary_stage

All notes use Obsidian `[[wikilinks]]` to cross-reference each other AND to reference the master index.

### 6.2 Update the master knowledge graph

```bash
python3 {SKILL_DIR}/scripts/update_master_graph.py {WORKING_DIR}
```

This script:
- Locates the vault root (the parent of the working dir's `Research-{slug}-{date}` folder)
- Reads or creates `{VAULT_ROOT}/Research-Master-Index.md`
- Adds an entry for this run with date, topic slug, link to working dir
- Reads or creates `{VAULT_ROOT}/Research-Master-Graph.json`
- For each cluster in this run, checks if there's already a cluster with the same `id` in any prior run; if so, increment the `runs_appeared_in` count
- Writes a `Research-Master-Clusters.md` index that shows clusters appearing in 2+ runs (cross-topic patterns) — these are universal truths surfacing

The master graph lets you ask cross-topic questions over time. Example: after running this on 5 topics, `Research-Master-Clusters.md` might show that "build-in-public" appears in marketing AND in psychology-of-attention AND in creator-economy research, marking it as a universal cluster.

### 6.3 Write the RUN_LOG.md

Finalize `RUN_LOG.md` with:
- Total runtime
- Per-phase timings
- Counts at each phase (videos, tactics, clusters, etc.)
- Any failures / retries / skipped videos
- Cost estimate (rough)
- Links to artifacts

### 6.4 Tell the user

Final message to the user includes:
1. Path to the HTML report
2. Path to the working directory (for vault browsing)
3. Path to `Research-Master-Index.md` (for cross-run patterns)
4. The 3-5 most interesting findings from the TLDR (preview to motivate them to open the report)
5. Suggestion: "want to drill on X?" naming the most interesting anomaly cluster

### 6.5 Output

Phase 6 completion criteria:
- All notes exist and have content
- Master index updated
- RUN_LOG.md finalized
- User has been told where everything is

Pipeline complete.
