# Phase 1 — Discovery

Goal: produce a high-quality master list of ~65 YouTube videos covering the topic, ranked and diversified.

## Prerequisites

- `scoping.json` exists from Phase 0. It contains `search_query_seeds` (15 queries already generated for this specific topic).

## Steps

### 1.1 Spawn ONE Haiku discovery agent

`model: haiku`, `subagent_type: general-purpose`. Prompt template:

```
You are Phase 1 (Discovery) of a deep YouTube research pipeline.

Read your scoping config from: {WORKING_DIR}/scoping.json

## Your job

1. Run all 15 searches from scoping.search_query_seeds via `mcp__youtube__search_videos` (maxResults=15-20 per search).
2. For each result, capture: videoId, title, channel/channelTitle, viewCount (if available), publishedAt, durationSeconds (or duration in seconds — convert if ISO).
3. Deduplicate by videoId.
4. Filter:
   - DROP duration < 240 seconds (4 min — usually shorts/clickbait)
   - DROP viewCount < 1,000 if known (low signal)
   - DROP videos older than 3 years UNLESS they have > 500k views (evergreen exception)
5. Rank by composite score:
   - views_score = log10(viewCount + 1)  (treat 0 viewCount as median for the topic)
   - recency_multiplier = 2.0 if published in last 90 days, 1.5 if last 365 days, 1.0 if last 3 years, 0.5 if older
   - score = views_score * recency_multiplier
6. Diversify: if any single channel has more than 5 videos in your top 65, demote extras and replace with the next-best videos from underrepresented channels. Goal: 25+ distinct channels.
7. Take the top 65.

## Output

Write JSON array to: {WORKING_DIR}/discovery.json

Each entry:
{
  "videoId": "...",
  "title": "...",
  "channel": "...",
  "viewCount": 123456,
  "publishedAt": "YYYY-MM-DD" or full ISO,
  "durationSeconds": 1234,
  "url": "https://youtube.com/watch?v=VIDEO_ID",
  "score": 12.34,
  "matched_query": "the search query this video came from"
}

## Final report

In your final message:
1. Total raw results, count after dedup, after filter, final count.
2. Number of distinct channels in the final 65.
3. Top 10 titles + channels (for sanity check).
4. Path to discovery.json.
5. Any search queries that returned mostly irrelevant results (flag for user to consider tweaking).
```

### 1.2 Validate the output

After the agent returns:

```bash
python3 -c "import json; d=json.load(open('{WORKING_DIR}/discovery.json')); assert len(d) >= 30, f'too few videos: {len(d)}'; assert len(set(v['channel'] for v in d)) >= 15, 'too few channels'"
```

If this fails:
- Fewer than 30 videos: the topic might be too niche for YouTube. Tell the user — offer to broaden the search queries or use WebSearch instead.
- Fewer than 15 channels: re-run the agent with explicit "diversify harder" instruction.

### 1.3 Sanity check with the user

Show the user the top 10 video titles + channels. Ask:
- Look right? Anything off-topic?
- Any creators you want to specifically include or exclude?

If yes, edit `discovery.json` directly (or have user do it) before proceeding to Phase 2.

### 1.4 If dry-run mode

Stop here. Report the discovery list and exit.

### 1.5 Output

Phase 1 completion criteria:
- `discovery.json` exists with ≥30 entries, ≥15 channels
- User has reviewed the top 10
- RUN_LOG.md has a Phase 1 entry with counts + duration

Then go to `02_extraction.md`.
