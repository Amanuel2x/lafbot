#!/usr/bin/env python3
"""build_dataset.py — Phase 4.1 generic dataset builder.

Reads clusters.json + all-tactics.json + scoping.json from the working dir.
Writes dataset.json with stats, bucket assignments, co-occurrence edges, etc.

Topic-agnostic. No hardcoded keywords or stages.

Usage:
  python3 build_dataset.py <working_dir>
"""
from __future__ import annotations

import json
import os
import sys
from collections import Counter, defaultdict
from itertools import combinations


def main():
    if len(sys.argv) != 2:
        print("usage: build_dataset.py <working_dir>", file=sys.stderr)
        sys.exit(2)
    wd = sys.argv[1]

    clusters = json.load(open(os.path.join(wd, "clusters.json")))
    all_tactics = json.load(open(os.path.join(wd, "all-tactics.json")))
    scoping = json.load(open(os.path.join(wd, "scoping.json")))

    # Build a lookup tactic_id -> tactic
    tactic_by_id = {t["id"]: t for t in all_tactics}

    # For each cluster, expand member ids to full tactic objects + compute stats
    cluster_objs = []
    for c in clusters["clusters"]:
        members = []
        for tid in c.get("member_tactic_ids", []):
            t = tactic_by_id.get(tid)
            if t:
                members.append(t)

        creator_channels = set()
        commenter_channels = set()
        creator_videos = set()
        commenter_videos = set()
        stage_counter = Counter()
        confidence_counter = Counter()
        claim_type_counter = Counter()
        quotes = []
        for m in members:
            ch = m.get("channel") or "?"
            if m.get("source") == "creator":
                creator_channels.add(ch)
                creator_videos.add(m.get("videoId"))
            else:
                commenter_channels.add(ch)
                commenter_videos.add(m.get("videoId"))
            stage_counter[m.get("stage") or "general"] += 1
            confidence_counter[m.get("confidence") or "medium"] += 1
            if m.get("claim_type"):
                claim_type_counter[m["claim_type"]] += 1
            if m.get("quote"):
                quotes.append({
                    "quote": m["quote"],
                    "channel": ch,
                    "source": m["source"],
                    "video_title": m.get("video_title", ""),
                    "video_url": m.get("video_url", ""),
                    "text": m.get("text", ""),
                })

        # Bucket
        c_count = len(creator_channels)
        cm_count = len(commenter_channels)
        if c_count >= 5:
            bucket = "consensus"
        elif c_count >= 3:
            bucket = "emerging"
        elif c_count >= 1 and cm_count >= 0:
            bucket = "anomaly"
        elif c_count == 0 and cm_count > 0:
            bucket = "commenter-only"
        else:
            bucket = "anomaly"

        # Sort quotes: prefer high-confidence + commenter for variety
        quotes.sort(
            key=lambda q: (
                0 if q["source"] == "commenter" else 1,
                -len(q["quote"]),
            )
        )

        cluster_objs.append({
            "id": c["id"],
            "label": c.get("label", c["id"].replace("-", " ").title()),
            "description": c.get("description", ""),
            "category": c["category"],
            "primary_stage": (
                c.get("primary_stage")
                or (stage_counter.most_common(1)[0][0] if stage_counter else "general")
            ),
            "stage_distribution": dict(stage_counter),
            "confidence_distribution": dict(confidence_counter),
            "claim_type_distribution": dict(claim_type_counter),
            "creator_channels": sorted(creator_channels),
            "commenter_channels": sorted(commenter_channels),
            "creator_channel_count": c_count,
            "commenter_channel_count": cm_count,
            "creator_video_count": len(creator_videos),
            "commenter_video_count": len(commenter_videos),
            "total_mentions": len(members),
            "bucket": bucket,
            "quotes": quotes[:10],
            "member_tactic_ids": c.get("member_tactic_ids", []),
        })

    # Co-occurrence edges
    # For each video, the set of clusters that touched it
    tactic_to_cluster = {}
    for c in cluster_objs:
        for tid in c["member_tactic_ids"]:
            tactic_to_cluster[tid] = c["id"]

    video_to_clusters = defaultdict(set)
    for t in all_tactics:
        c_id = tactic_to_cluster.get(t["id"])
        if c_id:
            video_to_clusters[t["videoId"]].add(c_id)

    edge_counts = Counter()
    for clusters_in_video in video_to_clusters.values():
        for a, b in combinations(sorted(clusters_in_video), 2):
            edge_counts[(a, b)] += 1
    edges = [
        {"source": a, "target": b, "weight": w}
        for (a, b), w in edge_counts.items()
        if w >= 3
    ]

    # Channel diversity
    channel_video_counts = Counter()
    for t in all_tactics:
        if t.get("channel"):
            channel_video_counts[t["channel"]] += 1

    # Meta
    meta = {
        "topic": scoping["topic"],
        "slug": scoping["slug"],
        "date": clusters.get("date") or scoping.get("date") or "",
        "axis_stage": scoping["axis_stage"],
        "axis_category": scoping["axis_category"],
        "videos_processed": len(set(t["videoId"] for t in all_tactics)),
        "distinct_channels": len(set(t.get("channel") for t in all_tactics if t.get("channel"))),
        "total_raw_tactics": len(all_tactics),
        "total_clusters": len(cluster_objs),
        "bucket_counts": dict(Counter(c["bucket"] for c in cluster_objs)),
    }

    dataset = {
        "meta": meta,
        "clusters": {c["id"]: c for c in cluster_objs},
        "edges": edges,
        "channel_diversity": dict(channel_video_counts.most_common(30)),
    }

    out_fp = os.path.join(wd, "dataset.json")
    with open(out_fp, "w") as f:
        json.dump(dataset, f, indent=2)
    print(f"wrote {out_fp}")
    print()
    print(f"clusters: {len(cluster_objs)}")
    print(f"edges (w>=3): {len(edges)}")
    print(f"buckets: {meta['bucket_counts']}")
    print()
    by_size = sorted(cluster_objs, key=lambda c: -(c['creator_channel_count'] + 0.5 * c['commenter_channel_count']))
    print("Top 10 clusters by creator+0.5*commenter channel reach:")
    for c in by_size[:10]:
        print(
            f"  {c['creator_channel_count']:2d}c {c['commenter_channel_count']:2d}cm | "
            f"{c['id']:45s} [{c['bucket']}]"
        )


if __name__ == "__main__":
    main()
