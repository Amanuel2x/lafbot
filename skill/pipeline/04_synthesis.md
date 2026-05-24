# Phase 4 — Synthesis (Opus, main thread)

Goal: turn `clusters.json` + `all-tactics.json` into the canonical `dataset.json` + a written narrative (TLDR, contradictions, anomaly framing) — all generated, not hardcoded.

## Prerequisites

- `clusters.json`, `all-tactics.json`, `scoping.json` all valid.

## Steps

### 4.1 Build the canonical dataset

Run `scripts/build_dataset.py {WORKING_DIR}`. This script (see below for what it does) reads the three input files and writes `{WORKING_DIR}/dataset.json` with:

- Per-cluster stats: # creator channels, # commenter channels, primary stage, primary category, all quotes (best 8), all source URLs
- Bucket assignment: `consensus` (≥5 creator channels), `emerging` (3-4), `anomaly` (1-2), `commenter-only` (0 creators but ≥1 commenter)
- Co-occurrence edges: pairs of clusters that appear together in 3+ videos, weighted by count
- Channel diversity stats
- Stage map: clusters grouped by primary_stage
- Meta: topic, slug, date, source counts

`build_dataset.py` is in `scripts/` — generic, no topic-specific code.

### 4.2 Generate the written narrative

The narrative is what made V1 feel polished — TLDR with 7 findings, 5 contradictions, anomaly framing. V2 GENERATES this from the dataset.

Spawn ONE Opus task on the main thread (you, in fact) — no agent needed. You have the dataset, you write the narrative.

#### 4.2.1 TLDR

Read `dataset.json`. Identify the 5-7 most surprising findings. Surprising = at least one of:
- Cluster has high creator support AND high commenter support (validated from two sides)
- Cluster has low creator support but HIGH commenter support (creators are missing it — high value)
- Cluster contradicts another high-frequency cluster
- Cluster has unusually specific numerical evidence ("got 500 signups in 7 days")
- Cluster is in a category most other clusters aren't (rare angle)

For each finding, write a 2-3 sentence summary that LEADS with the insight, not with the cluster name. The TLDR should read like a human wrote it from the data.

Write the TLDR to `{WORKING_DIR}/narrative-tldr.json`:

```json
{
  "findings": [
    {"headline": "...", "detail": "...", "cluster_ids": ["..."], "evidence": ["..."]}
  ]
}
```

`evidence` is a list of direct quotes (with attribution) that support the finding.

#### 4.2.2 Contradictions

Read all clusters. Identify pairs where:
- Two clusters describe opposite tactics on the same topic ("do X" vs "don't do X"), AND
- Each side has ≥1 creator OR ≥1 commenter source

Don't fabricate disagreements that aren't in the data. If there are none, write fewer than 5 contradictions — even zero is fine.

For each contradiction, write:
- topic: 1-line description of the disagreement
- side_a: position, supporters (creators + commenter quotes), evidence summary
- side_b: same
- resolution: your synthesis of how to read both — what's actually true / when each applies

Write to `{WORKING_DIR}/narrative-contradictions.json`.

#### 4.2.3 Anomaly framing

For each cluster in the `anomaly` or `commenter-only` bucket, write a 2-3 sentence framing of:
- What the tactic is
- Why it's underrepresented (creators don't talk about it)
- What's the leverage if it's true

These go into `{WORKING_DIR}/narrative-anomalies.json` keyed by cluster id.

### 4.3 Self-check

Before declaring Phase 4 done, READ what you wrote for the TLDR. Ask yourself:
- Could this paragraph have been written without looking at the data? If yes — too generic, rewrite with specifics.
- Are there 3+ verbatim quotes or specific numbers across the TLDR? If no — add evidence.
- Would a smart user read this and think "I would never have thought of that"? That's the bar.

### 4.4 Output

Phase 4 completion criteria:
- `dataset.json`, `narrative-tldr.json`, `narrative-contradictions.json`, `narrative-anomalies.json` exist
- TLDR contains 5-7 findings, each grounded in specific dataset evidence
- Contradictions only include pairs actually in the data (or empty if none)
- RUN_LOG.md updated

Then go to `05_html.md`.
