"""Tests for skill/scripts/build_html.py."""
from __future__ import annotations

import json
import subprocess
import sys


def setup_dataset(working_dir, script_dir):
    """Run build_dataset.py + write minimal narrative stubs."""
    subprocess.run(
        [sys.executable, str(script_dir / "build_dataset.py"), str(working_dir)],
        check=True,
        capture_output=True,
    )
    with open(working_dir / "narrative-tldr.json", "w") as f:
        json.dump({"findings": [
            {"headline": "Test finding", "detail": "details", "cluster_ids": [], "evidence": ["sample"]}
        ]}, f)
    with open(working_dir / "narrative-contradictions.json", "w") as f:
        json.dump({"contradictions": []}, f)
    with open(working_dir / "narrative-anomalies.json", "w") as f:
        json.dump({}, f)


def test_builds_html(working_dir, script_dir):
    setup_dataset(working_dir, script_dir)
    r = subprocess.run(
        [sys.executable, str(script_dir / "build_html.py"), str(working_dir)],
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, f"stderr: {r.stderr}"
    html_path = working_dir / "Deep-Research-Report.html"
    assert html_path.exists()
    assert html_path.stat().st_size > 10000  # >10KB minimum


def test_html_contains_required_sections(working_dir, script_dir):
    setup_dataset(working_dir, script_dir)
    subprocess.run(
        [sys.executable, str(script_dir / "build_html.py"), str(working_dir)],
        check=True,
        capture_output=True,
    )
    html = (working_dir / "Deep-Research-Report.html").read_text()
    assert "TLDR" in html
    assert "Test finding" in html
    assert "frequencyChart" in html
    assert "network" in html
    assert "Test topic" in html


def test_html_handles_empty_contradictions(working_dir, script_dir):
    """HTML build shouldn't break when contradictions list is empty."""
    setup_dataset(working_dir, script_dir)
    r = subprocess.run(
        [sys.executable, str(script_dir / "build_html.py"), str(working_dir)],
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0
    html = (working_dir / "Deep-Research-Report.html").read_text()
    assert "No major contradictions" in html
