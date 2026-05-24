# Phase 0 — Scoping

Goal: turn the user's free-text topic into a structured plan the rest of the pipeline can execute on. The big new V2 idea: **infer the right categorization/progression axes from the topic** instead of hardcoding them.

## Steps

### 0.1 Parse the user's invocation

- If the invocation is `/lafbot drill <topic-slug>/<cluster-slug>`, go to `drill.md` instead.
- If the invocation is `/lafbot --dry-run <topic>`, set `dry_run=True` and remember to stop after Phase 1.
- Otherwise, the topic is everything after `/lafbot `.

### 0.2 Confirm topic + parameters with one AskUserQuestion call

Ask three things in a single AskUserQuestion call:

1. **Stage/angle focus** (free-text, optional) — anything that should narrow the research. Default: "no specific angle, full breadth."
2. **Comment depth** — `light (20)` / `medium (50, recommended)` / `heavy (100+replies)`.
3. **Creator scope** — `broad diverse mix (recommended)` / `narrow to specific creators` (collect names if so).

Don't ask about the vault path here — that's resolved by the main thread before this phase, per SKILL.md's "Vault location" rule (LAFBOT_VAULT env → ~/.lafbotrc → ~/lafbot-research/).

### 0.3 Build the topic slug

Convert the topic to kebab-case for filenames:
- Strip "how to", "the", "a", "an" from the start.
- Lowercase, replace spaces with `-`, keep only `[a-z0-9-]`.
- Cap at 50 chars.

Example: "how to grow a SaaS waitlist" → `grow-saas-waitlist`. "The psychology of attention" → `psychology-of-attention`.

### 0.4 Create the working directory

```bash
mkdir -p {vault_dir}/Research-{slug}-{YYYY-MM-DD}/
```

Also create the RUN_LOG.md and start logging phase timings + decisions.

### 0.5 Axis inference (NEW in V2)

This is the big change. Spawn ONE Haiku agent (`model: haiku`, `subagent_type: general-purpose`) with this prompt:

```
You are setting up the categorization axes for a research synthesis.

Topic: {TOPIC}
Angle: {ANGLE_OR_"none"}

Your job: propose the best two axes for organizing tactics/insights about this topic.

**Axis 1 — Progression / Stage axis**: an ordered sequence of phases that practitioners go through. Examples:
- For "marketing a SaaS": idea → mvp → beta → v1 → revenue
- For "psychology of attention": orientation → engagement → retention → commitment → loyalty
- For "learning a musical instrument": beginner → intermediate → competent → advanced → mastery
- For "managing a team": individual contributor → first-time manager → manager-of-managers → director
- For "a static topic with no natural progression": [single-stage: "general"]

**Axis 2 — Category axis**: the natural functional groupings of tactics. Examples:
- For "marketing a SaaS": cold-outbound, content, community, seo, ads, psychology, growth-loops, positioning, social-proof, launches, sales
- For "psychology of attention": neuroscience-mechanisms, design-techniques, content-techniques, environmental-design, hijacking-patterns, defensive-techniques
- For "learning piano": technique, theory, repertoire, practice-routines, performance, mental-game

For each axis, list 4-10 distinct values (not too granular, not too sparse).

Return ONLY valid JSON in this exact shape:

{
  "topic": "{TOPIC}",
  "slug": "{SLUG}",
  "axis_stage": {
    "name": "...",
    "description": "what this axis represents",
    "values": ["...", "..."],
    "ordered": true | false
  },
  "axis_category": {
    "name": "...",
    "description": "what this axis represents",
    "values": ["...", "..."],
    "ordered": false
  },
  "search_query_seeds": [
    "list of 15 diverse YouTube search queries that would cover the topic from multiple angles — broad term, contrarian term, tactic-specific terms, stage-specific terms, beginner-vs-expert framings, etc."
  ],
  "expected_creator_archetypes": [
    "list of 5-10 *types* of creators who'd cover this topic. e.g. for SaaS marketing: indie hackers, VC-backed founders, paid-ad operators, marketing operators, contrarians. for piano: classical pedagogues, jazz pianists, self-taught creators, music theory channels, performance coaches."
  ]
}

Write your output to: {WORKING_DIR}/scoping.json
```

The agent's output IS the contract for the rest of the pipeline. Phases 1-4 all read `scoping.json` for axis names/values.

### 0.6 Show the user the axes before committing

After the Haiku agent returns, READ scoping.json and show the user:
- The inferred stage axis values
- The inferred category axis values
- The 15 search queries that will be used

Ask "looks right, or want to tweak?" — they can edit the file directly, or you can re-run the axis agent with their feedback. **Don't proceed to Phase 1 without confirmation.**

### 0.7 Output

Phase 0 completion criteria:
- `scoping.json` exists and validates against `schemas/scoping.schema.json`
- Working directory exists
- RUN_LOG.md has a Phase 0 entry with timestamp + topic + axes inferred
- User has approved the axes

Then go to `01_discovery.md`.
