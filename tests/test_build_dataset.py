"""Tests for skill/scripts/build_dataset.py."""
from __future__ import annotations

import json
import subprocess
import sys


def test_builds_dataset_from_clusters(working_dir, script_dir):
    r = subprocess.run(
        [sys.executable, str(script_dir / "build_dataset.py"), str(working_dir)],
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, f"stderr: {r.stderr}"
    dataset = json.load(open(working_dir / "dataset.json"))
    assert "meta" in dataset
    assert "clusters" in dataset
    assert "edges" in dataset
    assert dataset["meta"]["total_clusters"] == 3


def test_assigns_buckets_correctly(working_dir, script_dir):
    subprocess.run(
        [sys.executable, str(script_dir / "build_dataset.py"), str(working_dir)],
        check=True,
        capture_output=True,
    )
    dataset = json.load(open(working_dir / "dataset.json"))
    # 2 creators on cold-email -> anomaly (need ≥5 for consensus, ≥3 for emerging)
    cold = dataset["clusters"]["cold-email"]
    assert cold["bucket"] == "anomaly"
    # commenter-only would need 0 creators and ≥1 commenter
    spec = dataset["clusters"]["specificity-in-messaging"]
    assert spec["bucket"] == "commenter-only"


def test_computes_channel_diversity(working_dir, script_dir):
    subprocess.run(
        [sys.executable, str(script_dir / "build_dataset.py"), str(working_dir)],
        check=True,
        capture_output=True,
    )
    dataset = json.load(open(working_dir / "dataset.json"))
    assert "channel_diversity" in dataset
    # 2 channels in the fixture
    assert len(dataset["channel_diversity"]) == 2


def test_quotes_preserved(working_dir, script_dir):
    subprocess.run(
        [sys.executable, str(script_dir / "build_dataset.py"), str(working_dir)],
        check=True,
        capture_output=True,
    )
    dataset = json.load(open(working_dir / "dataset.json"))
    cold = dataset["clusters"]["cold-email"]
    assert len(cold["quotes"]) >= 2
    assert all("quote" in q for q in cold["quotes"])
    assert all("video_url" in q for q in cold["quotes"])
