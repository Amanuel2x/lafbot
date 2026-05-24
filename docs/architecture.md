# Architecture

How lafbot turns a topic into a knowledge graph.

## High-level flow

```
user types: /lafbot how to write a screenplay
                    │
                    ▼
        ┌──────────────────────┐
        │  Phase 0: Scoping    │  Haiku infers:
        │                      │   - Stage axis (e.g., concept → outline → draft → polish → market)
        │                      │   - Category axis (e.g., structure, dialogue, character, plot, business)
        │                      │   - 15 topic-specific search queries
        └──────────┬───────────┘
                   ▼
        ┌──────────────────────┐
        │ Phase 1: Discovery   │  Haiku runs the 15 searches,
        │                      │  dedupes, ranks by views×recency,
        │                      │  picks top 65 across ≥25 channels.
        └──────────┬───────────┘
                   ▼
        ┌──────────────────────┐
        │ Phase 2: Extraction  │  10 Sonnet agents in parallel.
        │  (parallel)          │  Each pulls transcript + 50 comments
        │  ▢▢▢▢▢▢▢▢▢▢          │  for 6-7 videos. Tags every tactic
        │                      │  with source/stage/category/quote.
        │                      │  Validates JSON; retries failed slices.
        └──────────┬───────────┘
                   ▼
        ┌──────────────────────┐
        │ Phase 3: Clustering  │  1 Sonnet "Cluster Architect" reads
        │                      │  all 400-700 raw tactics, groups them
        │                      │  semantically into 30-80 canonical
        │                      │  clusters. No keyword matching.
        └──────────┬───────────┘
                   ▼
        ┌──────────────────────┐
        │ Phase 4: Synthesis   │  Opus (main thread):
        │                      │   - Builds dataset.json
        │                      │   - Writes TLDR from data
        │                      │   - Detects contradictions
        │                      │   - Frames anomalies
        └──────────┬───────────┘
                   ▼
        ┌──────────────────────┐
        │ Phase 5: HTML report │  Self-contained Deep-Research-Report.html
        │                      │  with Chart.js + vis-network.
        └──────────┬───────────┘
                   ▼
        ┌──────────────────────┐
        │ Phase 6: Vault notes │  Per-cluster markdown, anomalies,
        │                      │  contradictions, per-axis playbook.
        │                      │  Updates Research-Master-Index.md.
        └──────────────────────┘
```

## Model assignment

| Phase | Model | Why |
|-------|-------|-----|
| 0 (scoping, axis inference) | Haiku 4.5 | Cheap and good enough for axis generation |
| 1 (discovery) | Haiku 4.5 | Mostly mechanical search + ranking |
| 2 (extraction × 10 parallel) | Sonnet 4.6 | Needs nuance to distinguish tactics from filler |
| 3 (cluster architect) | Sonnet 4.6 | Semantic grouping is hard; Haiku would over-cluster |
| 4 (synthesis) | Opus 4.7 (you, main thread) | Writing the TLDR + contradictions is the most creative work |
| 5 (HTML) | None (Python) | No LLM needed |
| 6 (notes) | None (Python) | No LLM needed |

You can override models in `~/.lafbotrc`:

```yaml
models:
  scoping: haiku
  discovery: haiku
  extraction: sonnet  # or haiku if budget-sensitive (loses nuance)
  clustering: sonnet
```

## Key data structures

### `scoping.json` (Phase 0 output)

```json
{
  "topic": "How to write a screenplay",
  "slug": "write-a-screenplay",
  "axis_stage": {
    "name": "Stage",
    "values": ["concept", "outline", "draft", "polish", "market"],
    "ordered": true
  },
  "axis_category": {
    "name": "Craft",
    "values": ["structure", "dialogue", "character", "plot", "business"],
    "ordered": false
  },
  "search_query_seeds": ["how to write a screenplay", "..."]
}
```

### `discovery.json` (Phase 1 output)

JSON array of 65 ranked videos with `{videoId, title, channel, viewCount, publishedAt, durationSeconds, url, score, matched_query}`.

### `extraction-NN.json` (Phase 2 output, 10 files)

Per-video extraction. Schema in `skill/schemas/extraction.schema.json`. Each tactic:

```json
{
  "text": "Use the Save the Cat 15-beat structure for your outline",
  "source": "creator",
  "stage": "outline",
  "category": "structure",
  "confidence": "high",
  "claim_type": "actionable",
  "quote": "Save the Cat is the cleanest beatsheet for first-timers..."
}
```

### `all-tactics.json` (Phase 3 input)

Flat list of every tactic from every extraction, with a stable `id` like `{videoId}#{tactic_index}`.

### `clusters.json` (Phase 3 output)

The semantic clustering decision. Each cluster has `id`, `label`, `description`, `category`, `primary_stage`, and `member_tactic_ids`.

### `dataset.json` (Phase 4 output — the canonical artifact)

The merged, enriched, bucketed dataset. Every cluster gets a `bucket` (consensus / emerging / anomaly / commenter-only), quote samples, channel/video counts, and co-occurrence edges to other clusters.

### `Research-Master-Graph.json` (cross-run)

Maintained by `update_master_graph.py`. Tracks every cluster across every run. Clusters appearing in 2+ runs become "universal patterns" surfaced in `Research-Master-Clusters.md`.

## What makes this subject-agnostic

Three explicit design choices:

1. **No keyword dictionaries.** V1 had a hardcoded `TACTIC_CLUSTERS` keyword map. V2 deleted it. The Cluster Architect agent groups semantically based on what the data actually says.
2. **Axis inference per topic.** A SaaS marketing run gets `idea → mvp → beta → v1 → revenue`. A "learning piano" run gets `beginner → intermediate → competent → advanced → mastery`. Both come from the same skill.
3. **Search queries generated, not stored.** The 15 search queries are produced by Haiku in Phase 0 based on the topic. No hardcoded query lists per topic type.

## What's NOT in the pipeline

- **Web search / blog posts / podcasts.** Only YouTube. See `extending.md` for how to add sources.
- **Real-time updates.** Each run is a snapshot. Re-run periodically (the schedule skill in Claude Code can automate this).
- **Multi-language support beyond what YouTube returns.** Transcripts are pulled in their native language. The agent extracts in whatever language they're written.
- **Video downloads.** lafbot only reads transcripts + metadata via the YouTube API. It does NOT download videos.

## Failure modes the design handles

| Failure | Recovery |
|---------|----------|
| Sonnet agent returns invalid JSON | `validate_extraction.py` flags it; auto-retry up to 2x with a corrective prompt |
| Cluster Architect produces a giant catch-all cluster | Sanity check: any cluster >40% of all tactics triggers a re-prompt |
| Topic too niche, YouTube returns <30 videos | Phase 1 validation hard-stops and tells the user |
| YouTube API quota exhausted | Stop, tell user, point at quota dashboard |
| Pipeline crashes mid-run | Every phase writes to disk before the next starts. Re-run the missing phase. |

## Where the cost is

Per-run rough breakdown:

```
Phase 0 (Haiku scoping):       ~$0.05
Phase 1 (Haiku discovery):     ~$0.20
Phase 2 (10× Sonnet extract):  ~$3-7   ← the bulk
Phase 3 (Sonnet cluster arch): ~$0.50
Phase 4 (Opus synthesis):      ~$1-3
Phase 5 (Python HTML):         $0
Phase 6 (Python notes):        $0
                              -------
Total:                         ~$5-12
```

To cut cost ~50%, set extraction model to Haiku in `~/.lafbotrc`. You'll lose some nuance in tactic extraction but the pipeline still works.
