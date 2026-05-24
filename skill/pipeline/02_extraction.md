# Phase 2 — Parallel extraction

Goal: extract tactics/insights from each video's transcript and top comments, separately tagged. Robust to bad JSON, missing transcripts, disabled comments.

## Prerequisites

- `scoping.json` and `discovery.json` exist from earlier phases.

## Steps

### 2.1 Split discovery into slices

Run via Bash:

```python
import json
d = json.load(open('{WORKING_DIR}/discovery.json'))
slices = [[] for _ in range(10)]
for i, v in enumerate(d):
    slices[i % 10].append(v)
for idx, sl in enumerate(slices):
    json.dump(sl, open(f'{WORKING_DIR}/slice-{idx:02d}.json', 'w'), indent=2)
```

### 2.2 Spawn 10 Sonnet agents IN A SINGLE MESSAGE (all parallel)

`model: sonnet`, `subagent_type: general-purpose`. **One Agent tool call per slice, all in the same response.**

Prompt template (replace `{N}`, `{SLICE_NUM}`, `{TOPIC}`, `{COMMENT_DEPTH}`, `{WORKING_DIR}`, `{AXIS_STAGE_VALUES}`, `{AXIS_CATEGORY_VALUES}`):

```
You are Phase 2 extraction agent #{SLICE_NUM} for deep research on: "{TOPIC}".

## Your slice
Read your video list from: {WORKING_DIR}/slice-{SLICE_NUM}.json ({N} videos).

## Axes you must tag against
Stage axis values (from scoping): {AXIS_STAGE_VALUES}
Category axis values (from scoping): {AXIS_CATEGORY_VALUES}

If a value doesn't fit any of these, use "general" for stage or invent a one-word kebab-case category and note it — the Cluster Architect in Phase 3 will normalize. Do NOT add ad-hoc stages beyond the provided list.

## Per video, in this exact order

1. Call `mcp__youtube__get_clean_transcript` with the videoId. If it fails (no transcript), mark video as skipped and continue.
2. Call `mcp__youtube__get_video_comments` with videoId, maxResults={COMMENT_DEPTH}.
3. From the TRANSCRIPT, extract distinct tactics/insights/claims. Source = "creator".
4. From the COMMENTS, extract distinct tactics/insights/claims. Source = "commenter". These are often the highest-signal items — pay extra attention.

## Tag each tactic

- **text**: 1-2 sentence description of the tactic (be specific, not vague)
- **source**: "creator" or "commenter"
- **stage**: one of the stage axis values (or "general" if none fit)
- **category**: one of the category axis values (or a new kebab-case label you propose)
- **confidence**: "high" (specific tactic with evidence/numbers), "medium" (claim with rationale), "low" (vibes)
- **quote**: verbatim quote (≤30 words) from transcript or comment that supports this tactic
- **claim_type**: "actionable" (specific tactic to try), "data-point" (a number or statistic), "framing" (a mental model or reframe), "warning" (something to avoid), or "story" (a case study or anecdote)

## Output schema — VERY STRICT

Write a JSON array to: {WORKING_DIR}/extraction-{SLICE_NUM}.json

The file MUST be valid JSON. The first character MUST be `[`. The last character MUST be `]`. No markdown fences, no commentary outside the JSON.

Per video:
```json
{
  "videoId": "...",
  "title": "...",
  "channel": "...",
  "url": "...",
  "tactics": [
    {
      "text": "...",
      "source": "creator|commenter",
      "stage": "...",
      "category": "...",
      "confidence": "high|medium|low",
      "claim_type": "actionable|data-point|framing|warning|story",
      "quote": "..."
    }
  ],
  "skipped": false,
  "skip_reason": null
}
```

Skipped video:
```json
{ "videoId": "...", "title": "...", "skipped": true, "skip_reason": "no transcript available" }
```

## Critical rules
- Return ONLY valid JSON in the file. Validate before writing — if your output isn't valid JSON, you MUST fix it before exiting.
- 5-25 tactics per video. Be specific, not padded.
- Aggressively extract commenter tactics — these are why this pipeline exists.
- Capture SPECIFIC numbers when commenters share them ("got 500 signups in 3 days from X" stays specific, doesn't get genericized).
- Prefer concrete tactics ("use a Loom video in cold email") over vague advice ("be authentic").
- Don't fabricate. If transcript is thin, return fewer tactics. Better 5 strong than 20 mediocre.

## Final message

Just report: videos processed, videos skipped (with reasons), total tactics (creator vs commenter breakdown), and any notable findings to flag for the synthesis phase. Output path: {WORKING_DIR}/extraction-{SLICE_NUM}.json
```

### 2.3 After all 10 agents return: validate each output

For each `extraction-{NN}.json`:

```python
import json, jsonschema

with open('{SKILL_DIR}/schemas/extraction.schema.json') as f:
    schema = json.load(f)

for nn in range(10):
    try:
        with open(f'{WORKING_DIR}/extraction-{nn:02d}.json') as f:
            data = json.load(f)
        for video in data:
            jsonschema.validate(video, schema)
        print(f"slice {nn}: ok ({len(data)} videos)")
    except (json.JSONDecodeError, jsonschema.ValidationError) as e:
        print(f"slice {nn}: FAILED — {e}")
        # mark for retry
```

If `jsonschema` isn't installed, fall back to basic validation: load JSON, check `isinstance(data, list)`, check each video has the required keys.

### 2.4 Retry failed slices

For any slice that failed validation, re-spawn the same Sonnet agent with this additional instruction at the top:

```
IMPORTANT: The previous run of this slice produced invalid JSON. The error was: {ERROR_MESSAGE}.

Read the slice file again. This time, ensure:
1. Your output file starts with `[` and ends with `]` (a JSON array)
2. No markdown code fences anywhere in the file
3. No commentary outside the JSON
4. All required fields present for every tactic

Validate your output mentally before writing. If you can't fit it all in one valid JSON document, return fewer tactics rather than malformed JSON.
```

Up to 2 retries per slice. If a slice still fails after 2 retries, log it in RUN_LOG.md as a failed slice and continue with the rest.

### 2.5 Output

Phase 2 completion criteria:
- 10 `extraction-{NN}.json` files exist (or up to 2 are marked failed)
- All passing files validate against `schemas/extraction.schema.json`
- Combined: ≥80% of discovery videos processed successfully
- RUN_LOG.md has Phase 2 entry with per-slice counts and any retries

Then go to `03_clustering.md`.
