<p align="center">
  <img src="assets/lafbot-banner.jpg" alt="lafbot — Learn Anything Fast" width="240">
</p>

# lafbot — Learn Anything Fast

> Multi-agent YouTube research pipeline for Claude Code. Pick any topic, walk away 30 minutes later with a knowledge-graph-style HTML report + Obsidian vault notes synthesized from 60+ videos and their viewer comments.

<p align="center">
  <a href="https://github.com/Amanuel2x/lafbot/actions/workflows/ci.yml"><img src="https://github.com/Amanuel2x/lafbot/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT"></a>
  <a href="https://claude.com/claude-code"><img src="https://img.shields.io/badge/Claude%20Code-Skill-7c3aed" alt="Claude Code Skill"></a>
</p>

---

## What this does

You give it a topic. It:

1. Runs ~15 YouTube searches across the topic
2. Picks ~65 high-signal videos and ranks them
3. Spawns **10 Claude agents in parallel** to extract tactics from each video's transcript AND top 50 viewer comments
4. Semantically clusters 500+ raw tactics into ~50 canonical groups
5. Identifies **consensus tactics** (what everyone says) vs **anomaly tactics** (what most aren't talking about) vs **commenter-only tactics** (the goldmine — what viewers say that creators don't)
6. Auto-generates a **self-contained HTML report** with charts + a knowledge graph
7. Drops markdown notes into your Obsidian vault, cross-linked

It works on **any topic** — marketing, psychology, persuasion, niche skills, philosophy, history. No hardcoded keywords. The clustering, axis inference, and category system are all generated per-topic by the LLM.

> **Demo GIF placeholder** — animated walkthrough coming. See [`examples/saas-marketing/`](examples/saas-marketing/) for a complete sanitized example output.

## Why this exists

YouTube has the highest-signal research material on most "how to" topics — but watching 60 videos and taking structured notes is 50+ hours of work. lafbot compresses that to ~30 minutes and ~$5-10 in tokens. The comments are where the gold is — practitioners adding specifics, contradictions, and tactics that creators leave out. Most research tools ignore them entirely.

## Prerequisites

Before you can run lafbot, you need:

1. **[Claude Code](https://claude.com/claude-code)** installed
2. **Python 3.9+** (`python3 --version`)
3. **Node.js 18+** (for the YouTube MCP server)
4. **Your own YouTube Data API v3 key** — see [`docs/youtube-api-setup.md`](docs/youtube-api-setup.md). Takes 5 minutes, free up to 10,000 API units/day.
5. **The [claude-code-youtube-mcp](https://github.com/wynandw87/claude-code-youtube-mcp)** server installed and connected.

> **Security note.** Your API key stays on your machine. lafbot does NOT ship with any keys, and does NOT phone home. Read [`docs/youtube-api-setup.md`](docs/youtube-api-setup.md) for how to restrict your key so even if it leaks it can only be used for YouTube searches.

## Install

```bash
git clone https://github.com/Amanuel2x/lafbot.git
cd lafbot
./install.sh
```

That's it. The installer:
- Symlinks `skill/` into `~/.claude/skills/lafbot/`
- Verifies Python 3.9+ and Node.js 18+ are present
- Verifies the YouTube MCP is connected (warns if not — directs you to setup docs)
- Does NOT touch your API keys

To uninstall: `./uninstall.sh`.

## First run

In any Claude Code session:

```
/lafbot how to grow an audience on Twitter from zero
```

It'll ask you 3 quick questions (comment depth, creator scope, save location), then run the pipeline. The full run takes 30-60 minutes and uses roughly $5-15 in Anthropic tokens depending on comment depth.

When it's done, it opens the HTML report in your browser and prints the path to the markdown notes.

## Drill-down mode

Once you've done a run, you can triple-click on any specific finding:

```
/lafbot drill twitter-growth/reply-guy-strategy
```

This spawns a focused mini-run on just that one cluster — pulls 5-10 additional videos specifically about it, deeper extraction, appends to the existing report.

## What you get

Every run produces a folder like `Research-<topic>-<date>/` containing:

- **`Deep-Research-Report.html`** — single-file, opens offline, has:
  - 7-finding TLDR with verbatim evidence
  - Stacked bar chart of top 20 clusters (creators + commenters)
  - Interactive network graph showing how clusters relate
  - Anomaly cards (1-2 creator findings — the contrarian gold)
  - "From the comments" section (viewer-only insights)
  - Contradictions where creators disagree, with both sides
  - Per-stage playbook (axes inferred per topic)
  - Source diversity chart

- **`00-Index.md`** + per-category markdown notes for Obsidian
- **`dataset.json`** — full canonical data, queryable
- **`Research-Master-Index.md`** in your vault root — **cross-run knowledge graph** that surfaces patterns appearing across multiple research runs

## Example output

See [`examples/saas-marketing/`](examples/saas-marketing/) for a complete run on "marketing a B2B SaaS from idea to revenue":
- 65 videos analyzed across 49 distinct creators
- 620 raw tactics → 69 canonical clusters
- 22 consensus tactics, 35 anomalies, 12 emerging tactics, 1 commenter-only

## How it works (for the curious)

lafbot is a 7-phase pipeline. Each phase has its own doc in [`skill/pipeline/`](skill/pipeline/).

```
Phase 0 (Scoping)         ← user input + Haiku axis inference
       ↓
Phase 1 (Discovery)       ← 1 Haiku agent: ~15 searches → 65 ranked videos
       ↓
Phase 2 (Extraction)      ← 10 Sonnet agents in parallel: transcript + comments → tactics JSON
       ↓                     [JSON schema validation + auto-retry per agent]
Phase 3 (Clustering)      ← 1 Sonnet "Cluster Architect": semantic dedup → canonical clusters
       ↓                     [false-positive detection]
Phase 4 (Synthesis)       ← Opus: TLDR + contradictions + anomaly framing
       ↓
Phase 5 (Report)          ← Generic HTML builder
       ↓
Phase 6 (Notes)           ← Vault markdown + master knowledge graph update
```

Read [`docs/architecture.md`](docs/architecture.md) for the deep dive.

## Cost

Default settings (medium comment depth, 65 videos):
- **Wall time**: 30-45 minutes
- **API cost**: ~$5-12 in Anthropic tokens
- **YouTube API**: ~2,000 units (free quota is 10,000/day)

Cheaper modes documented in [`docs/extending.md`](docs/extending.md).

## Contributing

PRs welcome. See [`CONTRIBUTING.md`](CONTRIBUTING.md). Good first contributions:
- New issue templates for niche topics that work especially well/poorly
- Improvements to the false-positive detection in clustering
- Multi-source support (Reddit, blog posts, podcasts — see [`docs/extending.md`](docs/extending.md))
- Better HTML/CSS for the report

## Troubleshooting

See [`docs/troubleshooting.md`](docs/troubleshooting.md). Most common issues:
- **MCP not connected** — re-run the YouTube MCP setup from `docs/youtube-api-setup.md`
- **YouTube quota exhausted** — wait 24h or request a quota increase
- **Extraction agent returns garbage** — `validate_extraction.py` will auto-retry up to 2x; check `RUN_LOG.md` if a slice fails

## License

MIT. See [`LICENSE`](LICENSE).

## Acknowledgments

Built on top of:
- [Claude Code](https://claude.com/claude-code) and the Anthropic API
- [claude-code-youtube-mcp](https://github.com/wynandw87/claude-code-youtube-mcp) by @wynandw87
- [Chart.js](https://www.chartjs.org/) and [vis-network](https://visjs.github.io/vis-network/) for the report visualizations

If lafbot helps you ship something, drop a star on the repo. That's the whole ROI loop.
