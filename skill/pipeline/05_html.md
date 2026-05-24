# Phase 5 — HTML report

Goal: build a self-contained HTML report. Topic-agnostic — all content comes from `dataset.json` + narrative JSON files.

## Prerequisites

- `dataset.json`, `narrative-tldr.json`, `narrative-contradictions.json`, `narrative-anomalies.json` all exist.

## Steps

### 5.1 Run the HTML builder

```bash
python3 {SKILL_DIR}/scripts/build_html.py {WORKING_DIR}
```

This script reads:
- `dataset.json` — clusters, edges, meta, axes
- `narrative-tldr.json` — TLDR findings
- `narrative-contradictions.json` — disagreements
- `narrative-anomalies.json` — anomaly framings (keyed by cluster id)

Writes: `Deep-Research-Report.html` to the working directory.

### 5.2 What the HTML contains (auto-generated)

1. **Header** — topic name, date, video count, channel count, cluster count, etc. from `dataset.meta`.
2. **TLDR** — render `narrative-tldr.findings` as bullet cards.
3. **Frequency bar chart** — Chart.js horizontal stacked bar, top 20 clusters by creator+commenter reach. Colors auto-assigned per category.
4. **Network graph** — vis-network. Nodes = clusters, edges = co-occurrence from `dataset.edges`. Node color = category. Size = mention count.
5. **Anomaly cards** — for each anomaly/commenter-only cluster, render with the framing from `narrative-anomalies.json` + best quote + source link.
6. **From the comments** — clusters where `commenter_channel_count >= 1`, sorted by commenter reach.
7. **Contradictions** — render `narrative-contradictions` side-by-side.
8. **Per-axis playbook** — collapsible sections for each value of `axis_stage`. Skips stages with no clusters. (Generic — works for any axis like "beginner→expert" or "idea→revenue".)
9. **Category breakdown** — collapsible sections for each value of `axis_category`, listing clusters in that category.
10. **Source diversity bar** — horizontal bar of `dataset.channel_diversity` top 15.
11. **Methodology** — collapsible: pipeline description, dataset stats, full source list with links.

### 5.3 Failure handling

- If `build_html.py` crashes, the error usually means a malformed narrative file. Read the traceback, fix the offending JSON, re-run.
- If Chart.js or vis-network CDN fails, the page still renders (charts just show as blank canvas). The HTML is still useful.

### 5.4 Output

Phase 5 completion criteria:
- `Deep-Research-Report.html` exists, > 50KB
- Opens in browser without console errors (spot check on macOS: `open Deep-Research-Report.html`)
- RUN_LOG.md updated

Then go to `06_notes.md`.
