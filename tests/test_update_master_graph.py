"""Tests for skill/scripts/update_master_graph.py."""
from __future__ import annotations

import json
import shutil
import subprocess
import sys


def setup_dataset(working_dir, script_dir):
    subprocess.run(
        [sys.executable, str(script_dir / "build_dataset.py"), str(working_dir)],
        check=True,
        capture_output=True,
    )


def _new_vault_run(working_dir, tmp_path, slug="test-topic", date="2026-01-01"):
    """Copy the fixture working_dir into a sibling vault layout the master graph can detect.

    Also rewrites scoping.json so its slug matches the requested arg — otherwise
    the master graph records the fixture's default slug regardless of dir name.
    """
    vault = tmp_path / "vault-root" / "research"
    vault.mkdir(parents=True)
    new_wd = vault / f"Research-{slug}-{date}"
    shutil.copytree(working_dir, new_wd)
    scoping = json.load(open(new_wd / "scoping.json"))
    scoping["slug"] = slug
    scoping["date"] = date
    json.dump(scoping, open(new_wd / "scoping.json", "w"))
    return vault, new_wd


def test_creates_master_files_on_first_run(working_dir, script_dir, tmp_path):
    vault, wd = _new_vault_run(working_dir, tmp_path)
    setup_dataset(wd, script_dir)
    r = subprocess.run(
        [sys.executable, str(script_dir / "update_master_graph.py"), str(wd)],
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, f"stderr: {r.stderr}"
    assert (vault / "Research-Master-Graph.json").exists()
    assert (vault / "Research-Master-Index.md").exists()
    assert (vault / "Research-Master-Clusters.md").exists()


def test_records_run_in_master_graph(working_dir, script_dir, tmp_path):
    vault, wd = _new_vault_run(working_dir, tmp_path)
    setup_dataset(wd, script_dir)
    subprocess.run(
        [sys.executable, str(script_dir / "update_master_graph.py"), str(wd)],
        check=True,
        capture_output=True,
    )
    master = json.load(open(vault / "Research-Master-Graph.json"))
    assert len(master["runs"]) == 1
    assert master["runs"][0]["slug"] == "test-topic"


def test_cross_topic_clusters_detected(working_dir, script_dir, tmp_path):
    """If the same cluster appears in 2 different runs, it should show up in cross-topic."""
    vault, wd1 = _new_vault_run(working_dir, tmp_path, slug="topic-a", date="2026-01-01")
    setup_dataset(wd1, script_dir)
    subprocess.run(
        [sys.executable, str(script_dir / "update_master_graph.py"), str(wd1)],
        check=True,
        capture_output=True,
    )

    # Second run: clone the same fixture data under a different slug
    wd2 = vault / "Research-topic-b-2026-01-02"
    shutil.copytree(wd1, wd2)
    scoping = json.load(open(wd2 / "scoping.json"))
    scoping["slug"] = "topic-b"
    scoping["topic"] = "Topic B"
    json.dump(scoping, open(wd2 / "scoping.json", "w"))
    # Remove the prior dataset.json so build_dataset writes a fresh one with the new topic
    (wd2 / "dataset.json").unlink(missing_ok=True)
    setup_dataset(wd2, script_dir)
    subprocess.run(
        [sys.executable, str(script_dir / "update_master_graph.py"), str(wd2)],
        check=True,
        capture_output=True,
    )

    master = json.load(open(vault / "Research-Master-Graph.json"))
    assert len(master["runs"]) == 2
    cold = master["clusters"]["cold-email"]
    assert len(cold["runs_appeared_in"]) == 2
    slugs = {r["slug"] for r in cold["runs_appeared_in"]}
    assert slugs == {"topic-a", "topic-b"}

    cross_md = (vault / "Research-Master-Clusters.md").read_text()
    assert "cold email" in cross_md.lower()
