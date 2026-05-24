#!/usr/bin/env python3
"""build_html.py — Phase 5 generic HTML report builder.

Reads from <working_dir>:
  - dataset.json
  - narrative-tldr.json
  - narrative-contradictions.json
  - narrative-anomalies.json (optional)

Writes:
  - Deep-Research-Report.html

Topic-agnostic. Works for any subject.
"""
from __future__ import annotations

import json
import os
import sys

# Color palette — auto-assigned to categories at runtime
PALETTE = [
    "#7c3aed", "#06b6d4", "#ef4444", "#f59e0b", "#10b981",
    "#3b82f6", "#ec4899", "#a855f7", "#84cc16", "#f97316",
    "#dc2626", "#14b8a6", "#6366f1", "#8b5cf6", "#0ea5e9",
    "#22c55e", "#eab308", "#d946ef", "#06b6d4", "#64748b",
]


def assign_colors(categories: list[str]) -> dict[str, str]:
    """Deterministic color assignment for each category."""
    out = {}
    for i, c in enumerate(sorted(set(categories))):
        out[c] = PALETTE[i % len(PALETTE)]
    return out


def safe_load(fp, default=None):
    if os.path.exists(fp):
        with open(fp) as f:
            return json.load(f)
    return default


def best_quote(cluster):
    if not cluster.get("quotes"):
        return None
    # Anomalies/commenter-only: prefer commenter quote if present
    if cluster["bucket"] in ("anomaly", "commenter-only"):
        for q in cluster["quotes"]:
            if q["source"] == "commenter":
                return q
    return cluster["quotes"][0]


def trunc(s, n=90):
    s = s or ""
    return s if len(s) <= n else s[:n].rstrip() + "…"


def render(wd):
    dataset = json.load(open(os.path.join(wd, "dataset.json")))
    tldr = safe_load(os.path.join(wd, "narrative-tldr.json"), {"findings": []})
    contradictions = safe_load(os.path.join(wd, "narrative-contradictions.json"), {"contradictions": []})
    anomalies_narrative = safe_load(os.path.join(wd, "narrative-anomalies.json"), {})

    meta = dataset["meta"]
    clusters_list = list(dataset["clusters"].values())
    categories = [c["category"] for c in clusters_list]
    color_map = assign_colors(categories)

    # Sort clusters once by composite reach
    by_reach = sorted(
        clusters_list,
        key=lambda c: -(c["creator_channel_count"] + 0.5 * c["commenter_channel_count"]),
    )

    # Buckets — only `anomalies` is used downstream; the others are reachable via by_reach + filter.
    anomalies = [c for c in by_reach if c["bucket"] in ("anomaly", "commenter-only")]

    # Stage map
    stage_axis = meta.get("axis_stage", {})
    stage_values = stage_axis.get("values", ["general"])
    if "general" not in stage_values:
        stage_values = list(stage_values) + ["general"]
    stage_to_clusters = {s: [] for s in stage_values}
    for c in by_reach:
        s = c["primary_stage"] if c["primary_stage"] in stage_to_clusters else "general"
        stage_to_clusters.setdefault(s, []).append(c)

    # Category map
    cat_axis = meta.get("axis_category", {})
    cat_values = cat_axis.get("values", [])
    cat_to_clusters = {cat: [] for cat in cat_values}
    for c in by_reach:
        cat_to_clusters.setdefault(c["category"], []).append(c)

    # Chart data — top 20 clusters
    top20 = by_reach[:20]
    chart_data = {
        "labels": [c["label"] for c in top20],
        "creator_counts": [c["creator_channel_count"] for c in top20],
        "commenter_counts": [c["commenter_channel_count"] for c in top20],
        "colors": [color_map.get(c["category"], "#64748b") for c in top20],
        "categories": [c["category"] for c in top20],
    }

    # Diversity chart
    diversity = dataset.get("channel_diversity", {})
    top_channels = list(diversity.items())[:15]
    diversity_data = {
        "labels": [k for k, _ in top_channels],
        "counts": [v for _, v in top_channels],
    }

    # Network graph
    graph_nodes = []
    for c in by_reach:
        size = 10 + c["creator_channel_count"] * 4 + c["commenter_channel_count"] * 2
        graph_nodes.append({
            "id": c["id"],
            "label": c["label"],
            "title": f"{c['label']} — {c['creator_channel_count']} creators, {c['commenter_channel_count']} commenters",
            "color": color_map.get(c["category"], "#64748b"),
            "size": min(size, 60),
            "group": c["category"],
        })
    graph_edges = [
        {"from": e["source"], "to": e["target"], "value": e["weight"]}
        for e in dataset.get("edges", [])
    ]

    # Build HTML
    title = meta["topic"]
    date = meta.get("date") or ""
    cluster_count = meta["total_clusters"]
    bucket_counts = meta.get("bucket_counts", {})

    axis_stage_desc = meta.get('axis_stage', {}).get('description', '')
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width,initial-scale=1" />
<title>Deep Research — {trunc(title, 80)}</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<script src="https://unpkg.com/vis-network@9.1.9/standalone/umd/vis-network.min.js"></script>
<style>
:root {{
  --bg: #0a0a0a; --bg-elev: #141414; --bg-elev-2: #1c1c1c; --border: #2a2a2a;
  --text: #e7e7e7; --text-muted: #888; --accent: #7c3aed; --accent-2: #06b6d4;
}}
@media (prefers-color-scheme: light) {{
  :root {{ --bg:#fafafa; --bg-elev:#fff; --bg-elev-2:#f4f4f4; --border:#e5e5e5; --text:#18181b; --text-muted:#71717a; }}
}}
* {{ box-sizing: border-box; }}
html, body {{ margin: 0; padding: 0; }}
body {{ background: var(--bg); color: var(--text); font-family: -apple-system, BlinkMacSystemFont, "Inter", "Segoe UI", sans-serif; line-height: 1.6; font-size: 15px; }}
.container {{ max-width: 1200px; margin: 0 auto; padding: 40px 24px; }}
header {{ border-bottom: 1px solid var(--border); padding-bottom: 24px; margin-bottom: 32px; }}
h1 {{ font-size: 32px; margin: 0 0 8px; font-weight: 700; }}
h2 {{ font-size: 22px; margin: 48px 0 16px; font-weight: 600; border-bottom: 1px solid var(--border); padding-bottom: 8px; }}
h3 {{ font-size: 17px; margin: 24px 0 8px; font-weight: 600; }}
.meta-bar {{ display:flex; gap:24px; flex-wrap:wrap; margin-top:12px; color: var(--text-muted); font-size:13px; }}
.meta-bar span strong {{ color: var(--text); font-weight: 600; }}
.tldr {{ background: var(--bg-elev); border:1px solid var(--border); border-left:3px solid var(--accent); padding: 20px 24px; border-radius: 8px; margin-bottom: 32px; }}
.tldr h2 {{ margin-top:0; border:none; padding:0; }}
.tldr-finding {{ margin: 16px 0; padding-left: 24px; position: relative; }}
.tldr-finding::before {{ content:"→"; position:absolute; left:0; color: var(--accent); font-weight:700; }}
.tldr-finding strong {{ display:block; margin-bottom:4px; }}
.tldr-finding span {{ color: var(--text-muted); font-size:14px; }}
.tldr-finding .evidence {{ font-size:12px; color: var(--text-muted); margin-top:6px; font-style: italic; }}
.card {{ background: var(--bg-elev); border:1px solid var(--border); border-radius: 8px; padding: 20px; margin: 16px 0; }}
.tactic-card .name {{ font-weight: 600; font-size: 15px; }}
.tactic-card .description {{ color: var(--text-muted); font-size: 13px; margin: 4px 0 8px; }}
.tactic-card .framing {{ background: var(--bg-elev-2); padding: 8px 12px; border-radius: 6px; font-size: 13px; margin: 6px 0; }}
.tactic-card .quote {{ color: var(--text-muted); font-style: italic; font-size: 14px; border-left: 2px solid var(--border); padding-left: 12px; margin: 6px 0; }}
.tactic-card .source {{ font-size: 12px; color: var(--text-muted); }}
.tactic-card .source a {{ color: var(--accent-2); text-decoration: none; }}
.tactic-card .source a:hover {{ text-decoration: underline; }}
.badges {{ display:flex; gap:6px; flex-wrap:wrap; margin-bottom: 8px; }}
.badge {{ display:inline-block; padding:2px 8px; border-radius:4px; font-size:11px; font-weight:600; text-transform:uppercase; letter-spacing:0.3px; background: var(--bg-elev-2); color: var(--text-muted); border:1px solid var(--border); }}
.badge.category {{ color:white; border-color:transparent; }}
.badge.bucket-consensus {{ background:#064e3b; color:#d1fae5; }}
.badge.bucket-anomaly,.badge.bucket-commenter-only {{ background:#7c2d12; color:#fed7aa; }}
.badge.bucket-emerging {{ background:#1e3a8a; color:#dbeafe; }}
.badge.source-commenter {{ background:#581c87; color:#f3e8ff; }}
.grid-2 {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(420px, 1fr)); gap: 16px; }}
.chart-container {{ background: var(--bg-elev); border:1px solid var(--border); border-radius: 8px; padding: 20px; position: relative; height: 720px; }}
.chart-container.short {{ height: 500px; }}
.network-container {{ background: var(--bg-elev); border:1px solid var(--border); border-radius: 8px; padding:0; height:600px; overflow:hidden; }}
#network {{ width:100%; height:600px; }}
.contradiction {{ border:1px solid var(--border); border-radius:8px; margin: 16px 0; overflow:hidden; }}
.contradiction-header {{ background: var(--bg-elev-2); padding: 12px 20px; font-weight:600; border-bottom:1px solid var(--border); }}
.contradiction-sides {{ display: grid; grid-template-columns: 1fr 1fr; }}
.side {{ padding:16px 20px; }}
.side.a {{ border-right:1px solid var(--border); background: rgba(59,130,246,0.05); }}
.side.b {{ background: rgba(239,68,68,0.05); }}
.side h4 {{ margin:0 0 8px; font-size:13px; text-transform:uppercase; color:var(--text-muted); }}
.side p {{ margin: 4px 0; font-size: 14px; }}
.side .creators {{ font-size: 12px; color: var(--text-muted); margin-top:8px; }}
.resolution {{ background: var(--bg-elev-2); padding: 12px 20px; border-top:1px solid var(--border); font-size:14px; }}
.resolution strong {{ color: var(--accent); }}
details {{ background: var(--bg-elev); border:1px solid var(--border); border-radius:8px; padding: 12px 16px; margin: 8px 0; }}
details summary {{ cursor:pointer; font-weight:600; padding: 4px 0; user-select:none; }}
details[open] summary {{ margin-bottom: 12px; }}
.toc {{ background: var(--bg-elev); border:1px solid var(--border); border-radius:8px; padding: 16px 24px; margin-bottom:32px; }}
.toc a {{ display:inline-block; margin-right:12px; color: var(--accent-2); text-decoration:none; font-size: 14px; }}
.toc a:hover {{ text-decoration: underline; }}
.method-list {{ font-size: 13px; color: var(--text-muted); }}
.method-list a {{ color: var(--accent-2); text-decoration: none; }}
.method-list a:hover {{ text-decoration: underline; }}
@media (max-width: 720px) {{
  .container {{ padding:20px 14px; }}
  .grid-2 {{ grid-template-columns: 1fr; }}
  .contradiction-sides {{ grid-template-columns: 1fr; }}
  .side.a {{ border-right:none; border-bottom:1px solid var(--border); }}
  h1 {{ font-size: 24px; }}
}}
</style>
</head>
<body>
<div class="container">
  <header>
    <h1>{title}</h1>
    <div style="color:var(--text-muted); font-size:14px;">Deep research synthesis — {axis_stage_desc}</div>
    <div class="meta-bar">
      <span>Date: <strong>{date}</strong></span>
      <span>Videos analyzed: <strong>{meta['videos_processed']}</strong></span>
      <span>Channels: <strong>{meta['distinct_channels']}</strong></span>
      <span>Raw tactics: <strong>{meta['total_raw_tactics']}</strong></span>
      <span>Canonical clusters: <strong>{cluster_count}</strong></span>
      <span>Consensus / Emerging / Anomaly: <strong>{bucket_counts.get('consensus',0)} / {bucket_counts.get('emerging',0)} / {bucket_counts.get('anomaly',0)+bucket_counts.get('commenter-only',0)}</strong></span>
    </div>
  </header>
  <nav class="toc">
    <a href="#tldr">TLDR</a>
    <a href="#frequency">Frequency</a>
    <a href="#network">Network</a>
    <a href="#anomalies">Anomalies</a>
    <a href="#from-comments">From the comments</a>
    <a href="#contradictions">Contradictions</a>
    <a href="#stages">{stage_axis.get('name','Stage')} playbook</a>
    <a href="#categories">{cat_axis.get('name','Category')} breakdown</a>
    <a href="#diversity">Source diversity</a>
    <a href="#methodology">Methodology</a>
  </nav>

  <section class="tldr" id="tldr">
    <h2>TLDR</h2>
"""

    for f in tldr.get("findings", []):
        evidence_text = ""
        if f.get("evidence"):
            evidence_text = '<div class="evidence">Evidence: ' + " · ".join(
                f'"{trunc(e, 100)}"' for e in f["evidence"][:3]
            ) + '</div>'
        html += f"""    <div class="tldr-finding"><strong>{f['headline']}</strong><span>{f.get('detail','')}</span>{evidence_text}</div>\n"""

    html += """  </section>

  <section id="frequency">
    <h2>What everyone is saying — top 20 clusters</h2>
    <p style="color:var(--text-muted)">Bar length = distinct creators. Orange overlay = commenters who independently validated.</p>
    <div class="chart-container"><canvas id="frequencyChart"></canvas></div>
  </section>

  <section id="network">
    <h2>Knowledge graph — how clusters connect</h2>
    <p style="color:var(--text-muted)">Nodes = clusters, edges = co-occurrence in 3+ videos. Drag to untangle.</p>
    <div class="network-container"><div id="network"></div></div>
  </section>

  <section id="anomalies">
    <h2>Anomalies — what most aren't talking about</h2>
    <p style="color:var(--text-muted)">Mentioned by only 1-2 creators (or only by commenters). Highest-leverage edges.</p>
    <div class="grid-2">
"""

    for c in anomalies[:24]:
        q = best_quote(c)
        if not q:
            continue
        framing = anomalies_narrative.get(c["id"], "")
        framing_html = f'<div class="framing">{framing}</div>' if framing else ''
        html += f"""    <div class="card tactic-card">
      <div class="badges">
        <span class="badge category" style="background:{color_map.get(c['category'], '#64748b')}">{c['category']}</span>
        <span class="badge">{c['primary_stage']}</span>
        <span class="badge bucket-{c['bucket']}">{c['bucket']}</span>
        {'<span class="badge source-commenter">commenter source</span>' if q['source']=='commenter' else ''}
      </div>
      <div class="name">{c['label']}</div>
      <div class="description">{c.get('description','')}</div>
      {framing_html}
      <div class="quote">"{q['quote']}"</div>
      <div class="source">— {q['channel']} · <a href="{q['video_url']}" target="_blank">{trunc(q['video_title'], 80)}</a></div>
    </div>
"""

    html += """    </div>
  </section>

  <section id="from-comments">
    <h2>From the comments — viewer insights</h2>
    <p style="color:var(--text-muted)">Clusters with commenter validation. Often higher signal than creator advice alone.</p>
    <div class="grid-2">
"""

    commenter_pool = sorted(
        [c for c in by_reach if c["commenter_channel_count"] >= 1],
        key=lambda c: -c["commenter_channel_count"],
    )[:20]
    for c in commenter_pool:
        cq = next((q for q in c["quotes"] if q["source"] == "commenter"), None)
        if not cq:
            continue
        html += f"""    <div class="card tactic-card">
      <div class="badges">
        <span class="badge category" style="background:{color_map.get(c['category'], '#64748b')}">{c['category']}</span>
        <span class="badge source-commenter">{c['commenter_channel_count']} commenter video(s)</span>
      </div>
      <div class="name">{c['label']}</div>
      <div class="description">{c.get('description','')}</div>
      <div class="quote">"{cq['quote']}"</div>
      <div class="source">— commenter on <a href="{cq['video_url']}" target="_blank">{trunc(cq['video_title'], 80)}</a> ({cq['channel']})</div>
    </div>
"""

    html += """    </div>
  </section>

  <section id="contradictions">
    <h2>Where sources disagree</h2>
"""
    cons = contradictions.get("contradictions", [])
    if not cons:
        html += '<p style="color:var(--text-muted)">No major contradictions surfaced in this corpus.</p>'
    for c in cons:
        html += f"""    <div class="contradiction">
      <div class="contradiction-header">{c['topic']}</div>
      <div class="contradiction-sides">
        <div class="side a">
          <h4>Side A</h4>
          <p><strong>{c['side_a']['position']}</strong></p>
          <p>{c['side_a'].get('evidence','')}</p>
          <div class="creators">— {', '.join(c['side_a'].get('supporters', []))}</div>
        </div>
        <div class="side b">
          <h4>Side B</h4>
          <p><strong>{c['side_b']['position']}</strong></p>
          <p>{c['side_b'].get('evidence','')}</p>
          <div class="creators">— {', '.join(c['side_b'].get('supporters', []))}</div>
        </div>
      </div>
      <div class="resolution"><strong>Read:</strong> {c.get('resolution','')}</div>
    </div>
"""

    html += f"""  </section>

  <section id="stages">
    <h2>{stage_axis.get('name','Stage')} playbook</h2>
    <p style="color:var(--text-muted)">{stage_axis.get('description','')}</p>
"""
    for s in stage_values:
        slist = stage_to_clusters.get(s, [])
        if not slist:
            continue
        html += f'<details {"open" if s == stage_values[0] else ""}><summary>{s} ({len(slist)} clusters)</summary><ul>'
        for c in slist[:15]:
            html += f'<li><strong>{c["label"]}</strong> <span class="badge category" style="background:{color_map.get(c["category"], "#64748b")};font-size:10px">{c["category"]}</span> <span style="color:var(--text-muted);font-size:13px">({c["creator_channel_count"]}c, {c["commenter_channel_count"]}cm)</span></li>'
        html += "</ul></details>"

    html += f"""  </section>

  <section id="categories">
    <h2>{cat_axis.get('name','Category')} breakdown</h2>
    <p style="color:var(--text-muted)">{cat_axis.get('description','')}</p>
"""
    for cat in cat_values + sorted(set(c["category"] for c in by_reach) - set(cat_values)):
        clist = cat_to_clusters.get(cat, [])
        if not clist:
            continue
        html += f'<details><summary>{cat} ({len(clist)} clusters)</summary><ul>'
        for c in clist:
            html += f'<li><strong>{c["label"]}</strong> <span style="color:var(--text-muted);font-size:13px">({c["creator_channel_count"]}c, {c["commenter_channel_count"]}cm, {c["bucket"]})</span> — {trunc(c.get("description",""), 100)}</li>'
        html += "</ul></details>"

    html += """  </section>

  <section id="diversity">
    <h2>Source diversity</h2>
    <p style="color:var(--text-muted)">Top 15 channels by # videos contributed. Spread tells you if you're in an echo chamber.</p>
    <div class="chart-container short"><canvas id="diversityChart"></canvas></div>
  </section>

  <section id="methodology">
    <h2>Methodology + sources</h2>
    <details>
      <summary>Pipeline</summary>
      <div style="padding:8px 0; font-size:14px; color:var(--text-muted)">
        <p>This report was generated by the <code>/lafbot</code> skill — a multi-agent YouTube research pipeline.</p>
        <p>Phase 1 (Haiku): 15 topic-specific YouTube searches → ranked 65 videos.<br>
        Phase 2 (10 Sonnet agents in parallel): extracted tactics from transcripts + top comments, tagged with source/stage/category/confidence.<br>
        Phase 3 (Sonnet Cluster Architect): semantic clustering of raw tactics into canonical groups.<br>
        Phase 4 (Opus): synthesis — TLDR, contradictions, anomaly framing, knowledge graph.<br>
        Phase 5: this HTML report.</p>
      </div>
    </details>
    <details>
      <summary>All source videos</summary>
      <div class="method-list">
"""
    # Source video list - reconstruct from clusters' member_tactic_ids via dataset
    # We need to get the videos from the raw data; reconstruct from cluster quotes for simplicity
    seen_videos = {}
    for c in clusters_list:
        for q in c.get("quotes", []):
            url = q.get("video_url")
            if url and url not in seen_videos:
                seen_videos[url] = {
                    "title": q.get("video_title", "Unknown"),
                    "channel": q.get("channel", "?"),
                }
    for url, info in sorted(seen_videos.items(), key=lambda x: x[1]["channel"]):
        html += f'<div style="margin:4px 0">• <strong>{info["channel"]}</strong> — <a href="{url}" target="_blank">{trunc(info["title"], 90)}</a></div>'

    html += """      </div>
    </details>
  </section>
</div>

<script>
const chartData = """ + json.dumps(chart_data) + """;
new Chart(document.getElementById('frequencyChart').getContext('2d'), {
  type: 'bar',
  data: {
    labels: chartData.labels,
    datasets: [
      { label: 'Creators', data: chartData.creator_counts, backgroundColor: chartData.colors, borderWidth: 1 },
      { label: 'Commenters', data: chartData.commenter_counts, backgroundColor: '#f97316cc', borderColor: '#f97316', borderWidth: 1 },
    ],
  },
  options: {
    indexAxis: 'y', responsive: true, maintainAspectRatio: false,
    plugins: {
      legend: { labels: { color: getComputedStyle(document.body).getPropertyValue('--text') } },
      tooltip: { callbacks: { afterLabel: (ctx) => 'category: ' + chartData.categories[ctx.dataIndex] } },
    },
    scales: {
      x: { stacked: true, ticks: { color: getComputedStyle(document.body).getPropertyValue('--text-muted') }, grid: { color: getComputedStyle(document.body).getPropertyValue('--border') } },
      y: { stacked: true, ticks: { color: getComputedStyle(document.body).getPropertyValue('--text') }, grid: { display: false } },
    },
  },
});

const diversityData = """ + json.dumps(diversity_data) + """;
new Chart(document.getElementById('diversityChart').getContext('2d'), {
  type: 'bar',
  data: { labels: diversityData.labels, datasets: [{ label: '# videos', data: diversityData.counts, backgroundColor: '#7c3aedcc', borderWidth: 1 }] },
  options: {
    indexAxis: 'y', responsive: true, maintainAspectRatio: false,
    plugins: { legend: { labels: { color: getComputedStyle(document.body).getPropertyValue('--text') } } },
    scales: {
      x: { ticks: { color: getComputedStyle(document.body).getPropertyValue('--text-muted') }, grid: { color: getComputedStyle(document.body).getPropertyValue('--border') } },
      y: { ticks: { color: getComputedStyle(document.body).getPropertyValue('--text') }, grid: { display: false } },
    },
  },
});

const nodes = new vis.DataSet(""" + json.dumps(graph_nodes) + """);
const edges = new vis.DataSet(""" + json.dumps(graph_edges) + """);
new vis.Network(document.getElementById('network'), { nodes, edges }, {
  nodes: { shape: 'dot', font: { color: getComputedStyle(document.body).getPropertyValue('--text'), size: 12 }, borderWidth: 0 },
  edges: { color: { color: getComputedStyle(document.body).getPropertyValue('--border'), opacity: 0.6 }, smooth: { type: 'continuous' }, scaling: { min: 1, max: 6 } },
  physics: { barnesHut: { gravitationalConstant: -8000, centralGravity: 0.2, springLength: 150, springConstant: 0.04 }, stabilization: { iterations: 200 } },
  interaction: { hover: true, tooltipDelay: 100 },
});
</script>
</body>
</html>
"""

    out = os.path.join(wd, "Deep-Research-Report.html")
    with open(out, "w") as f:
        f.write(html)
    print(f"wrote {out} ({len(html):,} bytes)")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: build_html.py <working_dir>", file=sys.stderr)
        sys.exit(2)
    render(sys.argv[1])
