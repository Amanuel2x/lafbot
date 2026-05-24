# Drill-down mode

Goal: triple-click on a specific cluster from a prior run. Pulls 5-10 more videos focused on JUST that cluster, deeper extraction, appends to the existing report.

## Invocation

`/lafbot drill <topic-slug>/<cluster-id>`

Example:
- `/lafbot drill saas-marketing/loom-video-outreach` — drill into the Loom video DM cluster from the SaaS marketing run
- `/lafbot drill psychology-of-attention/scarcity-hijack` — drill into a specific anomaly from a psychology run

## Prerequisites

- The prior run's working directory exists at `{VAULT_ROOT}/Research-{topic-slug}-{date}/`
- `dataset.json` from that run contains the cluster id

## Steps

### D.1 Locate the prior run

```bash
# Find the most recent run matching this slug
find {VAULT_ROOT} -type d -name "Research-{topic-slug}-*" | sort -r | head -1
```

If multiple dates exist, pick the most recent. If none exist, stop and tell the user the topic slug doesn't match any prior run.

### D.2 Read the existing cluster

```python
import json
prior = json.load(open(f"{PRIOR_RUN_DIR}/dataset.json"))
if "{cluster-id}" not in prior["clusters"]:
    raise ValueError(f"cluster {cluster-id} not in this run")
target = prior["clusters"]["{cluster-id}"]
print(f"Drilling: {target['label']}")
print(f"Description: {target['description']}")
print(f"Existing reach: {target['creator_channel_count']}c {target['commenter_channel_count']}cm")
print(f"Existing quotes: {len(target['quotes'])}")
```

### D.3 Generate focused search queries (3-5)

Spawn ONE Haiku agent (`model: haiku`) with this prompt:

```
We're drilling into a specific cluster from a prior research run.

Cluster: {target.label}
Description: {target.description}
Category: {target.category}
Existing quotes (for context, do not re-search these):
{[q.quote for q in target.quotes[:5]]}

Generate 5-7 highly focused YouTube search queries that would surface NEW videos specifically about this tactic. Avoid generic queries — be precise.

Output a JSON array of strings to: {PRIOR_RUN_DIR}/drill-{cluster-id}-queries.json

Examples for "loom-video-outreach" might be:
- "loom cold email reply rate"
- "video DM B2B sales"
- "personalized video outreach examples"
- "screen recording in cold outbound"
```

### D.4 Run focused discovery

Spawn ONE Haiku agent that runs each search via `mcp__youtube__search_videos`, takes top 3-5 results per query, deduplicates against the videos ALREADY in `prior.dataset.json` (extract videoIds from the existing cluster's member tactics), and outputs 5-10 new videos to drill on. Save to `drill-{cluster-id}-discovery.json`.

### D.5 Focused extraction (1 Sonnet agent)

Spawn ONE Sonnet agent with this prompt:

```
You are doing a drill-down extraction on cluster "{target.label}" ({target.description}).

Read your video list from: {PRIOR_RUN_DIR}/drill-{cluster-id}-discovery.json

For each video:
1. mcp__youtube__get_clean_transcript
2. mcp__youtube__get_video_comments maxResults=50
3. Extract tactics RELATED TO THIS CLUSTER specifically — be much narrower than a full extraction. Goal: deep variants, edge cases, contradictions, specific numbers, novel angles.
4. Tag each tactic with source/confidence/quote like before.

Output JSON to: {PRIOR_RUN_DIR}/drill-{cluster-id}-extraction.json

Same schema as full extraction. Aim for 5-15 tactics per video, all directly about {target.label} or its near-neighbors.
```

### D.6 Merge into the existing dataset

Run a small merge script (inline):

```python
import json
wd = "{PRIOR_RUN_DIR}"
dataset = json.load(open(f"{wd}/dataset.json"))
drill = json.load(open(f"{wd}/drill-{cluster-id}-extraction.json"))

# Append new quotes + recompute counts
target = dataset["clusters"]["{cluster-id}"]
new_quotes = []
new_creator_channels = set(target["creator_channels"])
new_commenter_channels = set(target["commenter_channels"])

for v in drill:
    if v.get("skipped"):
        continue
    for t in v.get("tactics", []):
        ch = v.get("channel") or "?"
        if t.get("source") == "creator":
            new_creator_channels.add(ch)
        else:
            new_commenter_channels.add(ch)
        new_quotes.append({
            "quote": t.get("quote"),
            "channel": ch,
            "source": t["source"],
            "video_title": v.get("title"),
            "video_url": v.get("url"),
            "text": t.get("text"),
            "drill_added": True,
        })

target["creator_channels"] = sorted(new_creator_channels)
target["commenter_channels"] = sorted(new_commenter_channels)
target["creator_channel_count"] = len(new_creator_channels)
target["commenter_channel_count"] = len(new_commenter_channels)
target["quotes"] = (target["quotes"] + new_quotes)[:30]  # cap

json.dump(dataset, open(f"{wd}/dataset.json", "w"), indent=2)
```

### D.7 Append a drill-down section to the HTML

Re-run `scripts/build_html.py {PRIOR_RUN_DIR}`. The cluster will now have richer data, so the anomaly card / from-the-comments section auto-updates.

Also append a `Drill-{cluster-id}.md` note to the working dir with all the new quotes + a summary of what changed.

### D.8 Update master graph

Re-run `scripts/update_master_graph.py {PRIOR_RUN_DIR}` so the cross-topic graph reflects the updated cluster stats.

### D.9 Final message

Tell the user:
- How many new videos were drilled
- Cluster's new reach (e.g. "was 2c 1cm → now 6c 4cm")
- 2-3 specific new insights from the drill
- Path to updated report
