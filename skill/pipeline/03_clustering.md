# Phase 3 — Semantic clustering (Cluster Architect)

Goal: take the 400-700 raw tactics from Phase 2 and group them into 30-80 canonical semantic clusters. This is the V2 fix that makes the skill subject-agnostic — no hardcoded keyword dictionaries.

## Prerequisites

- All `extraction-*.json` files exist and validated.
- `scoping.json` exists.

## Steps

### 3.1 Compile all raw tactics into one input file

Run via Bash:

```python
import json, glob, os
WORKING_DIR = "{WORKING_DIR}"
all_tactics = []
for fp in sorted(glob.glob(f"{WORKING_DIR}/extraction-*.json")):
    with open(fp) as f:
        for v in json.load(f):
            if v.get("skipped"):
                continue
            for i, t in enumerate(v.get("tactics", [])):
                all_tactics.append({
                    "id": f"{v['videoId']}#{i}",
                    "text": t.get("text"),
                    "quote": t.get("quote"),
                    "source": t.get("source"),
                    "stage": t.get("stage"),
                    "category_raw": t.get("category"),
                    "confidence": t.get("confidence"),
                    "claim_type": t.get("claim_type"),
                    "videoId": v["videoId"],
                    "channel": v.get("channel"),
                    "video_title": v.get("title"),
                    "video_url": v.get("url"),
                })
json.dump(all_tactics, open(f"{WORKING_DIR}/all-tactics.json", "w"), indent=2)
print(f"compiled {len(all_tactics)} tactics into all-tactics.json")
```

### 3.2 Spawn ONE Sonnet "Cluster Architect" agent

`model: sonnet`, `subagent_type: general-purpose`. Big context window required — agent will see all 400-700 tactics at once.

Prompt:

```
You are the Cluster Architect for a lafbot synthesis on: "{TOPIC}".

## Your inputs

1. The full list of raw tactics: {WORKING_DIR}/all-tactics.json — read this with the Read tool.
2. The scoping config: {WORKING_DIR}/scoping.json — defines the stage and category axes.

## Your job

Group the raw tactics into canonical SEMANTIC clusters. Two raw tactics belong in the same cluster if they describe essentially the same idea/technique/move, even if worded differently. Examples:
- "cold email" / "cold outreach via email" / "outbound email campaign" / "Instantly email automation" → one cluster "cold-email"
- "build in public" / "share your journey" / "post daily updates" / "transparent metrics" → one cluster "build-in-public"

Each canonical cluster gets:
- **id**: kebab-case slug (e.g. "cold-email", "loom-video-dms")
- **label**: human-readable name (e.g. "Cold email outreach")
- **description**: 1-2 sentence summary of what the cluster represents
- **category**: ONE of the values from scoping.axis_category.values. If none truly fit, propose a new category and add it to a `new_categories` field at the top level (use sparingly — try to fit the existing categories first)
- **primary_stage**: ONE of the values from scoping.axis_stage.values, or "general"
- **member_tactic_ids**: list of the `id` values from all-tactics.json that belong to this cluster

## Constraints

1. Aim for 30-80 clusters total. Fewer than 30 = too coarse (you're conflating distinct tactics). More than 80 = too fine (you're not deduping enough).
2. EVERY raw tactic must be assigned to exactly one cluster. Use a cluster "miscellaneous-{category}" if you genuinely can't categorize.
3. A cluster's members should pass this test: "if I read 2 random members' quotes, are they about the same idea?" If no, split the cluster.
4. Do NOT create a cluster with just 1 member unless the tactic is clearly unique and high-signal — those go into a "singletons" bucket per category for the anomaly section.

## Anti-patterns to avoid (these came up in V1)

- Don't cluster tactics together just because they share a short keyword. "Press release" and "press the button" are NOT the same.
- Don't make giant catch-all clusters like "marketing-stuff" that hold >50 tactics. Split.
- Don't fabricate clusters that have no members.

## Output

Write to: {WORKING_DIR}/clusters.json

Schema:
{
  "topic": "{TOPIC}",
  "clusters": [
    {
      "id": "cold-email",
      "label": "Cold email outreach",
      "description": "Sending unsolicited email to a targeted list, typically using sequencing tools and warmup infrastructure.",
      "category": "cold-outbound",
      "primary_stage": "v1",
      "member_tactic_ids": ["abc123#0", "def456#3", ...]
    },
    ...
  ],
  "new_categories": [
    {"name": "...", "rationale": "..."}
  ],
  "stats": {
    "total_raw_tactics": 620,
    "total_assigned": 620,
    "total_clusters": 65,
    "largest_cluster": "cold-email (42 members)",
    "smallest_cluster": "..."
  }
}

VALIDATION before writing:
- Every raw tactic id from all-tactics.json must appear in exactly one cluster's member_tactic_ids.
- stats.total_assigned must equal stats.total_raw_tactics.
- All cluster.category values must be in scoping.axis_category.values OR in new_categories.

In your final message, just report: total clusters, largest 5 clusters by size with member counts, any new categories you proposed, and the path to clusters.json.
```

### 3.3 Validate clusters

Run via Bash:

```python
import json
clusters = json.load(open('{WORKING_DIR}/clusters.json'))
all_tactics = json.load(open('{WORKING_DIR}/all-tactics.json'))
scoping = json.load(open('{WORKING_DIR}/scoping.json'))

# 1. Every tactic must appear exactly once
all_ids = set(t['id'] for t in all_tactics)
assigned = []
for c in clusters['clusters']:
    assigned.extend(c['member_tactic_ids'])
assigned_set = set(assigned)

missing = all_ids - assigned_set
dup_count = len(assigned) - len(assigned_set)
unknown = assigned_set - all_ids

if missing:
    print(f"FAIL: {len(missing)} tactics unassigned")
if dup_count:
    print(f"FAIL: {dup_count} duplicate assignments")
if unknown:
    print(f"FAIL: {len(unknown)} unknown ids in clusters")

# 2. Cluster categories must be in scoping or new_categories
allowed_cats = set(scoping['axis_category']['values']) | {nc['name'] for nc in clusters.get('new_categories', [])}
bad_cats = [c['id'] for c in clusters['clusters'] if c['category'] not in allowed_cats]
if bad_cats:
    print(f"FAIL: clusters with unknown categories: {bad_cats}")

# 3. Sanity: no cluster >40% of all tactics (giant catch-all)
n_total = len(all_tactics)
biggest = max(clusters['clusters'], key=lambda c: len(c['member_tactic_ids']))
if len(biggest['member_tactic_ids']) > 0.40 * n_total:
    print(f"WARN: cluster '{biggest['id']}' has {len(biggest['member_tactic_ids'])} members ({len(biggest['member_tactic_ids'])/n_total:.1%}) — likely too broad")

# 4. Cluster count in target range
n = len(clusters['clusters'])
if n < 20 or n > 100:
    print(f"WARN: {n} clusters (target 30-80)")
else:
    print(f"OK: {n} clusters")
```

If validation fails, re-prompt the Cluster Architect with the specific issue (missing ids, duplicate ids, oversized cluster, etc.).

### 3.4 False-positive detection

Spot-check the 3 largest clusters by sampling 5 random members each and confirming they're actually about the same thing. If not, re-prompt with: "Cluster X looks heterogeneous. Sample members: [...]. Split into more focused sub-clusters."

You can do this spot-check yourself in the main thread — read 5 quotes per large cluster and judge. No agent needed.

### 3.5 Output

Phase 3 completion criteria:
- `clusters.json` exists and validates (no missing/dup/unknown ids, sensible cluster count, no oversized cluster)
- Spot check on 3 largest clusters passed (or one round of fix applied)
- RUN_LOG.md updated

Then go to `04_synthesis.md`.
