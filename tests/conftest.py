"""Shared pytest fixtures."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"
SKILL_SCRIPTS = Path(__file__).parent.parent / "skill" / "scripts"


@pytest.fixture
def working_dir(tmp_path):
    """Create a fresh working directory with the minimal files needed for downstream tests.

    Returned as `tmp_path/wd/` so callers can safely build sibling directories
    (e.g. a vault root) without recursing into the working dir.
    """
    wd = tmp_path / "wd"
    wd.mkdir()
    shutil.copy(FIXTURES / "mini_scoping.json", wd / "scoping.json")
    shutil.copy(FIXTURES / "mini_clusters.json", wd / "clusters.json")
    shutil.copy(FIXTURES / "mini_extraction.json", wd / "extraction-00.json")
    with open(FIXTURES / "mini_extraction.json") as f:
        extraction = json.load(f)
    all_tactics = []
    for v in extraction:
        if v.get("skipped"):
            continue
        for i, t in enumerate(v.get("tactics", [])):
            all_tactics.append({
                "id": f"{v['videoId']}#{i}",
                "text": t.get("text"),
                "quote": t.get("quote"),
                "source": t.get("source"),
                "stage": t.get("stage"),
                "category_raw": t.get("category"),
                "confidence": t.get("confidence"),
                "claim_type": t.get("claim_type"),
                "videoId": v["videoId"],
                "channel": v.get("channel"),
                "video_title": v.get("title"),
                "video_url": v.get("url"),
            })
    with open(wd / "all-tactics.json", "w") as f:
        json.dump(all_tactics, f, indent=2)
    return wd


@pytest.fixture
def script_dir():
    return SKILL_SCRIPTS
