#!/usr/bin/env python3
"""update_master_graph.py — Phase 6 cross-run master knowledge graph.

Reads dataset.json from a single run.
Updates {VAULT_ROOT}/Research-Master-Index.md and Research-Master-Graph.json
so cross-topic patterns surface over time.

Usage:
  python3 update_master_graph.py <working_dir>
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime

VAULT_ROOT_HINT_NAMES = {"lafbot-research", "research", "vault"}


def find_vault_root(working_dir: str) -> str:
    """Walk up from working_dir to find a sensible 'vault root' for master files.

    Heuristic: vault root is the closest parent directory matching either:
      - one of the VAULT_ROOT_HINT_NAMES (e.g. "lafbot-research", "research", "vault"), OR
      - a name starting with two digits and a dash (Obsidian convention, e.g. "08-Marketing")
    Falls back to the parent of the working dir.
    """
    p = os.path.abspath(working_dir)
    parent = os.path.dirname(p)
    parts = parent.split(os.sep)
    for i in range(len(parts) - 1, 0, -1):
        name = parts[i]
        if name in VAULT_ROOT_HINT_NAMES or (
            len(name) > 3 and name[2] == "-" and name[:2].isdigit()
        ):
            return os.sep.join(parts[: i + 1])
    return parent


def main():
    if len(sys.argv) != 2:
        print("usage: update_master_graph.py <working_dir>", file=sys.stderr)
        sys.exit(2)
    wd = sys.argv[1]

    dataset = json.load(open(os.path.join(wd, "dataset.json")))
    meta = dataset["meta"]
    vault_root = find_vault_root(wd)

    master_json_fp = os.path.join(vault_root, "Research-Master-Graph.json")
    master_md_fp = os.path.join(vault_root, "Research-Master-Index.md")
    cross_md_fp = os.path.join(vault_root, "Research-Master-Clusters.md")

    # Load or init master graph
    if os.path.exists(master_json_fp):
        with open(master_json_fp) as f:
            master = json.load(f)
    else:
        master = {"runs": [], "clusters": {}}

    # Add this run
    run_entry = {
        "slug": meta["slug"],
        "topic": meta["topic"],
        "date": meta.get("date", datetime.now().strftime("%Y-%m-%d")),
        "working_dir": wd,
        "videos": meta["videos_processed"],
        "channels": meta["distinct_channels"],
        "clusters": meta["total_clusters"],
        "bucket_counts": meta.get("bucket_counts", {}),
    }
    # Remove any prior entry for this slug+date
    master["runs"] = [r for r in master["runs"]
                       if not (r["slug"] == run_entry["slug"] and r["date"] == run_entry["date"])]
    master["runs"].append(run_entry)

    # Update cluster appearance counts
    for c in dataset["clusters"].values():
        key = c["id"]
        if key not in master["clusters"]:
            master["clusters"][key] = {
                "id": key,
                "label": c["label"],
                "category": c["category"],
                "runs_appeared_in": [],
            }
        appearances = master["clusters"][key]["runs_appeared_in"]
        # Dedupe by slug
        appearances = [a for a in appearances if a["slug"] != meta["slug"]]
        appearances.append({
            "slug": meta["slug"],
            "topic": meta["topic"],
            "date": run_entry["date"],
            "creator_channels": c["creator_channel_count"],
            "commenter_channels": c["commenter_channel_count"],
            "bucket": c["bucket"],
        })
        master["clusters"][key]["runs_appeared_in"] = appearances

    with open(master_json_fp, "w") as f:
        json.dump(master, f, indent=2)

    # Write Research-Master-Index.md
    ml = [
        "# Research Master Index",
        "",
        "> Cross-topic knowledge graph. Every `/lafbot` run is recorded here.",
        "",
        f"**Total runs**: {len(master['runs'])}",
        f"**Distinct clusters tracked**: {len(master['clusters'])}",
        f"**Cross-topic clusters (≥2 runs)**: {sum(1 for c in master['clusters'].values() if len(c['runs_appeared_in']) >= 2)}",
        "",
        "## All runs",
        "",
        "| Date | Topic | Videos | Channels | Clusters | Anomalies |",
        "|------|-------|--------|----------|----------|-----------|",
    ]
    for r in sorted(master["runs"], key=lambda x: x.get("date", "")):
        bc = r.get("bucket_counts", {})
        anomalies = bc.get("anomaly", 0) + bc.get("commenter-only", 0)
        link = f"[[Research-{r['slug']}-{r['date']}/00-Index|{r['topic']}]]"
        ml.append(f"| {r['date']} | {link} | {r['videos']} | {r['channels']} | {r['clusters']} | {anomalies} |")
    ml.extend([
        "",
        "## Cross-topic clusters",
        "",
        "See [[Research-Master-Clusters]] for clusters that appear across 2+ topics. These are universal patterns surfacing over time.",
    ])
    with open(master_md_fp, "w") as f:
        f.write("\n".join(ml))

    # Write Research-Master-Clusters.md (cross-topic patterns)
    cross_topic = sorted(
        [c for c in master["clusters"].values() if len(c["runs_appeared_in"]) >= 2],
        key=lambda c: -len(c["runs_appeared_in"]),
    )
    ml = [
        "# Research Master Clusters",
        "",
        "> Clusters that appear in 2 or more research runs — these are universal patterns surfacing across topics.",
        "",
        f"**Cross-topic clusters**: {len(cross_topic)}",
        "",
    ]
    for c in cross_topic:
        ml.append(f"## {c['label']}")
        ml.append(f"- **Category** (most recent): {c['category']}")
        ml.append(f"- **Runs**: {len(c['runs_appeared_in'])}")
        for r in c["runs_appeared_in"]:
            ml.append(f"  - {r['date']} · [[Research-{r['slug']}-{r['date']}/00-Index|{r['topic']}]] — {r['creator_channels']}c, {r['commenter_channels']}cm, {r['bucket']}")
        ml.append("")
    with open(cross_md_fp, "w") as f:
        f.write("\n".join(ml))

    print(f"updated master graph at {vault_root}/")
    print("  Research-Master-Graph.json")
    print(f"  Research-Master-Index.md  ({len(master['runs'])} runs)")
    print(f"  Research-Master-Clusters.md  ({len(cross_topic)} cross-topic clusters)")


if __name__ == "__main__":
    main()
