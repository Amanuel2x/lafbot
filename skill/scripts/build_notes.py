#!/usr/bin/env python3
"""build_notes.py — Phase 6 generic vault notes builder.

Topic-agnostic. Reads dataset.json + narrative files from working dir,
writes Obsidian markdown notes back into the same directory.

Usage:
  python3 build_notes.py <working_dir>
"""
from __future__ import annotations

import json
import os
import sys
from collections import defaultdict


def safe_load(fp, default=None):
    if os.path.exists(fp):
        with open(fp) as f:
            return json.load(f)
    return default


def cat_filename(cat: str) -> str:
    """Convert category slug to filename, e.g. 'cold-outbound' -> 'Cold-Outbound.md'"""
    return "-".join(w.capitalize() for w in cat.split("-")) + ".md"


def cat_wikilink(cat: str) -> str:
    return f"[[{'-'.join(w.capitalize() for w in cat.split('-'))}]]"


def main():
    if len(sys.argv) != 2:
        print("usage: build_notes.py <working_dir>", file=sys.stderr)
        sys.exit(2)
    wd = sys.argv[1]

    dataset = json.load(open(os.path.join(wd, "dataset.json")))
    # narrative-tldr is consumed by the HTML, not the notes (notes link to the report)
    contradictions = safe_load(os.path.join(wd, "narrative-contradictions.json"), {"contradictions": []})
    anomalies_n = safe_load(os.path.join(wd, "narrative-anomalies.json"), {})

    meta = dataset["meta"]
    clusters = list(dataset["clusters"].values())

    # Group by category
    by_cat = defaultdict(list)
    for c in clusters:
        by_cat[c["category"]].append(c)

    # Group by stage
    stage_values = meta.get("axis_stage", {}).get("values", ["general"])
    if "general" not in stage_values:
        stage_values = list(stage_values) + ["general"]
    by_stage = defaultdict(list)
    for c in clusters:
        s = c["primary_stage"] if c["primary_stage"] in stage_values else "general"
        by_stage[s].append(c)

    # ---- 00-Index.md ----
    cat_axis_name = meta.get("axis_category", {}).get("name", "Category")
    stage_axis_name = meta.get("axis_stage", {}).get("name", "Stage")
    lines = [
        f"# {meta['topic']}",
        "",
        f"> Deep research synthesis — {meta.get('date','')}",
        "",
        "## Run metadata",
        "",
        f"- **Topic**: {meta['topic']}",
        f"- **Slug**: `{meta['slug']}`",
        f"- **Date**: {meta.get('date','')}",
        f"- **Videos analyzed**: {meta['videos_processed']}",
        f"- **Distinct channels**: {meta['distinct_channels']}",
        f"- **Raw tactics**: {meta['total_raw_tactics']}",
        f"- **Canonical clusters**: {meta['total_clusters']}",
        f"- **Buckets**: {meta.get('bucket_counts', {})}",
        "",
        "## Report",
        "",
        "- [[Deep-Research-Report.html]] — the HTML report (charts + network graph)",
        "- [[dataset.json]] — canonical structured data",
        "",
        f"## {cat_axis_name} notes",
        "",
    ]
    for cat in sorted(by_cat.keys()):
        lines.append(f"- {cat_wikilink(cat)} — {len(by_cat[cat])} clusters")
    lines.extend([
        "",
        "## Cross-cutting notes",
        "",
        "- [[Anomalies]] — clusters mentioned by 1-2 creators or only commenters",
        "- [[From-the-Comments]] — viewer-sourced insights",
        "- [[Contradictions]] — where sources disagree",
        f"- [[Per-{stage_axis_name}-Playbook]] — clusters grouped by {stage_axis_name.lower()}",
        "",
        "## Knowledge graph context",
        "",
        "This research is part of the cross-topic knowledge graph in [[Research-Master-Index]]. Clusters that appear across multiple research runs are tagged as universal patterns.",
        "",
        "## How to use",
        "",
        "1. Open the HTML for the visual summary.",
        "2. Drill into category notes for tactics you want to try.",
        "3. Cross-reference Anomalies vs Playbook before choosing experiments.",
        "4. Re-run `/lafbot drill {slug}/{cluster-id}` for any cluster you want to triple-click.",
    ])
    with open(os.path.join(wd, "00-Index.md"), "w") as f:
        f.write("\n".join(lines))

    # ---- One MD per category ----
    for cat, clist in by_cat.items():
        clist_sorted = sorted(
            clist,
            key=lambda c: -(c["creator_channel_count"] + 0.5 * c["commenter_channel_count"]),
        )
        ml = [
            f"# {cat.title()}",
            "",
            f"**Total clusters**: {len(clist_sorted)}",
            "",
            "## Clusters",
            "",
        ]
        for c in clist_sorted:
            ml.append(f"### {c['label']}")
            ml.append(f"- **Bucket**: {c['bucket']}  ·  **Stage**: {c['primary_stage']}  ·  **Mentions**: {c['total_mentions']}")
            ml.append(f"- **Source reach**: {c['creator_channel_count']} creators, {c['commenter_channel_count']} commenters")
            ml.append(f"- {c.get('description','')}")
            for q in c.get("quotes", [])[:3]:
                marker = "💬 commenter" if q["source"] == "commenter" else "🎙️ creator"
                ml.append(f"  - {marker} ({q['channel']}): _\"{q['quote']}\"_ — [video]({q['video_url']})")
            ml.append("")
        ml.append("[[00-Index|← back to index]]")
        with open(os.path.join(wd, cat_filename(cat)), "w") as f:
            f.write("\n".join(ml))

    # ---- Anomalies.md ----
    anomalies = sorted(
        [c for c in clusters if c["bucket"] in ("anomaly", "commenter-only")],
        key=lambda c: -(c["creator_channel_count"] + c["commenter_channel_count"]),
    )
    ml = [
        "# Anomalies — what most aren't talking about",
        "",
        f"**Count**: {len(anomalies)} anomaly clusters",
        "",
    ]
    for c in anomalies:
        framing = anomalies_n.get(c["id"], "")
        ml.append(f"### {c['label']}")
        ml.append(f"- **Bucket**: {c['bucket']}  ·  **Category**: {cat_wikilink(c['category'])}  ·  **Stage**: {c['primary_stage']}")
        ml.append(f"- {c.get('description','')}")
        if framing:
            ml.append(f"- **Why this matters**: {framing}")
        for q in c.get("quotes", [])[:3]:
            marker = "💬 commenter" if q["source"] == "commenter" else "🎙️ creator"
            ml.append(f"  - {marker} ({q['channel']}): _\"{q['quote']}\"_ — [video]({q['video_url']})")
        ml.append("")
    ml.append("[[00-Index|← back to index]]")
    with open(os.path.join(wd, "Anomalies.md"), "w") as f:
        f.write("\n".join(ml))

    # ---- From-the-Comments.md ----
    ml = [
        "# From the Comments",
        "",
        "> Viewer-sourced insights. Often higher signal than creator advice alone — practitioners adding specifics or contradicting.",
        "",
    ]
    commenter_pool = sorted(
        [c for c in clusters if c["commenter_channel_count"] >= 1],
        key=lambda c: -c["commenter_channel_count"],
    )
    for c in commenter_pool:
        cq = next((q for q in c["quotes"] if q["source"] == "commenter"), None)
        if not cq:
            continue
        ml.append(f"### {c['label']}")
        ml.append(f"- **Category**: {cat_wikilink(c['category'])}  ·  **Commenter videos**: {c['commenter_channel_count']}")
        ml.append(f"- 💬 _\"{cq['quote']}\"_ — commenter on [{cq['video_title'][:80]}]({cq['video_url']}) ({cq['channel']})")
        ml.append("")
    ml.append("[[00-Index|← back to index]]")
    with open(os.path.join(wd, "From-the-Comments.md"), "w") as f:
        f.write("\n".join(ml))

    # ---- Contradictions.md ----
    ml = ["# Contradictions", ""]
    cons = contradictions.get("contradictions", [])
    if not cons:
        ml.append("_No major contradictions surfaced in this corpus._")
    else:
        ml.append("> Where sources disagree. These are decisions you have to make actively.\n")
        for c in cons:
            ml.append(f"## {c['topic']}")
            ml.append("")
            ml.append(f"**Side A:** {c['side_a']['position']}  ")
            ml.append(f"_Supporters_: {', '.join(c['side_a'].get('supporters', []))}  ")
            ml.append(f"_Evidence_: {c['side_a'].get('evidence','')}")
            ml.append("")
            ml.append(f"**Side B:** {c['side_b']['position']}  ")
            ml.append(f"_Supporters_: {', '.join(c['side_b'].get('supporters', []))}  ")
            ml.append(f"_Evidence_: {c['side_b'].get('evidence','')}")
            ml.append("")
            ml.append(f"**Read:** {c.get('resolution','')}")
            ml.append("")
            ml.append("---")
            ml.append("")
    ml.append("[[00-Index|← back to index]]")
    with open(os.path.join(wd, "Contradictions.md"), "w") as f:
        f.write("\n".join(ml))

    # ---- Per-{Stage}-Playbook.md ----
    playbook_fname = f"Per-{stage_axis_name}-Playbook.md"
    ml = [
        f"# Per-{stage_axis_name} Playbook",
        "",
        f"> Clusters grouped by {stage_axis_name.lower()}. Within each: consensus first, then emerging, then anomalies.",
        "",
    ]
    for stage in stage_values:
        slist = by_stage.get(stage, [])
        if not slist:
            continue
        ml.append(f"## {stage}")
        for bname in ("consensus", "emerging", "anomaly", "commenter-only"):
            items = [c for c in slist if c["bucket"] == bname]
            if not items:
                continue
            ml.append(f"\n### {bname.replace('-', ' ').title()}")
            for c in items[:10]:
                ml.append(f"- **{c['label']}** — {cat_wikilink(c['category'])} — {c['creator_channel_count']}c {c['commenter_channel_count']}cm")
        ml.append("")
    ml.append("[[00-Index|← back to index]]")
    with open(os.path.join(wd, playbook_fname), "w") as f:
        f.write("\n".join(ml))

    print(f"wrote notes to {wd}:")
    for f in sorted(os.listdir(wd)):
        if f.endswith(".md"):
            sz = os.path.getsize(os.path.join(wd, f))
            print(f"  {f} ({sz:,} bytes)")


if __name__ == "__main__":
    main()
