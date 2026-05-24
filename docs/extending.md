# Extending lafbot

How to customize the pipeline for your needs without forking.

## Add a new data source (e.g., Reddit, blogs)

Right now lafbot only reads YouTube. To add Reddit:

1. **Create a new extraction phase.** Copy `skill/pipeline/02_extraction.md` to `skill/pipeline/02b_reddit_extraction.md`. Adjust the agent prompt to call a Reddit MCP server instead of the YouTube one.
2. **Output format must match.** Reddit-sourced tactics should produce the same `extraction-NN.json` schema so Phase 3 can ingest them transparently.
3. **Tag the source.** Add `"discovery_source": "reddit"` to each tactic so the report can distinguish.
4. **Add a discovery sub-phase.** Reddit's "video list" equivalent is the top posts in relevant subreddits. Write a `01b_reddit_discovery.md` similar to the existing one.

The dataset builder + HTML builder are already source-agnostic.

## Override models per phase

Create `~/.lafbotrc`:

```yaml
vault_path: ~/notes/research
models:
  scoping: haiku
  discovery: haiku
  extraction: haiku   # cheaper, faster, less nuance
  clustering: sonnet
  synthesis: sonnet   # cheaper than opus
```

Tradeoffs:
- **Haiku extraction**: ~3x cheaper, ~2x faster, but misses ~15% of nuanced commenter tactics
- **Sonnet synthesis**: ~2x cheaper, but the TLDR + contradictions are noticeably more generic

## Change the report visualization

The HTML builder is `skill/scripts/build_html.py`. It's one file. Edit it:

- **Different chart library**: swap Chart.js for Recharts, D3, etc. Replace the `<script>` tags and the chart-init JS.
- **Different network graph**: swap vis-network for Cytoscape or react-force-graph.
- **Custom branding**: edit the CSS in the `<style>` block at the top.

The data contracts (`dataset.json` shape, narrative JSON files) are stable.

## Add custom buckets

Default buckets are `consensus / emerging / anomaly / commenter-only`. To add `niche-but-high-confidence`:

Edit `skill/scripts/build_dataset.py`, function near line ~95 where bucket assignment happens. Add your condition:

```python
if c_count <= 2 and all(q['confidence'] == 'high' for q in quotes):
    bucket = "niche-high-confidence"
```

Then add the corresponding badge CSS in `build_html.py`.

## Pre-populate the cluster architect

If you run lafbot on the same domain (e.g., always marketing topics) and want consistent cluster labels across runs, you can seed the Cluster Architect:

Create `~/.lafbot/cluster-seeds/marketing.json`:

```json
{
  "preferred_clusters": [
    {"id": "cold-email", "label": "Cold email outreach"},
    {"id": "build-in-public", "label": "Build in public"}
  ]
}
```

Then modify `pipeline/03_clustering.md` to inject this as additional context in the Cluster Architect prompt.

## Use a different LLM provider

The Claude Code agent system is currently Anthropic-only. To use OpenAI or local models, you'd need to:

1. Rewrite the agent spawn calls as direct API calls
2. Recreate the parallelism (Claude Code's parallel-agent semantics aren't trivial to replicate)
3. Port the prompt templates (they're written for Claude's tool-use style)

This is a significant fork. We don't currently support it but PRs are welcome if you build the abstraction cleanly.

## Run lafbot programmatically

You can invoke the Python scripts directly:

```bash
# Assuming you've manually populated extraction-NN.json files
python3 skill/scripts/validate_extraction.py /path/to/working/dir
python3 skill/scripts/build_dataset.py /path/to/working/dir
python3 skill/scripts/build_html.py /path/to/working/dir
python3 skill/scripts/build_notes.py /path/to/working/dir
python3 skill/scripts/update_master_graph.py /path/to/working/dir
```

This is useful for:
- Testing changes to the scripts
- Re-rendering the HTML after editing `dataset.json` by hand
- Bulk-reprocessing old runs after a script improvement

## Schedule recurring runs

Use the Claude Code [`/schedule`](https://docs.claude.com/claude-code) skill to re-run lafbot periodically:

```
/schedule monthly /lafbot psychology of attention
```

This is great for fast-moving topics where new tactics emerge over time.

## Add custom validation

Edit `skill/scripts/validate_extraction.py` to add domain-specific checks. Example: for marketing topics, require every "data-point" claim_type to include a number.
