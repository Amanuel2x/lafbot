"""Tests for skill/scripts/validate_extraction.py."""
from __future__ import annotations

import json
import subprocess
import sys


def run_validator(working_dir, script_dir):
    return subprocess.run(
        [sys.executable, str(script_dir / "validate_extraction.py"), str(working_dir)],
        capture_output=True,
        text=True,
    )


def test_validates_good_extraction(working_dir, script_dir):
    r = run_validator(working_dir, script_dir)
    assert r.returncode == 0, f"stdout: {r.stdout}\nstderr: {r.stderr}"
    assert "OK" in r.stdout
    assert "FAIL" not in r.stdout


def test_rejects_missing_required_keys(working_dir, script_dir):
    bad = [{"videoId": "v1", "tactics": [{"text": "x"}]}]  # missing source/stage/etc
    with open(working_dir / "extraction-00.json", "w") as f:
        json.dump(bad, f)
    r = run_validator(working_dir, script_dir)
    assert r.returncode == 1


def test_rejects_invalid_source(working_dir, script_dir):
    bad = [{
        "videoId": "v1",
        "tactics": [{
            "text": "test tactic",
            "source": "robot",  # invalid
            "stage": "alpha",
            "category": "red",
            "confidence": "high",
            "quote": "q",
        }],
    }]
    with open(working_dir / "extraction-00.json", "w") as f:
        json.dump(bad, f)
    r = run_validator(working_dir, script_dir)
    assert r.returncode == 1
    assert "bad source" in r.stdout.lower()


def test_rejects_non_list_root(working_dir, script_dir):
    with open(working_dir / "extraction-00.json", "w") as f:
        f.write('{"not": "an array"}')
    r = run_validator(working_dir, script_dir)
    assert r.returncode == 1


def test_accepts_skipped_video_without_tactics(working_dir, script_dir):
    data = [{"videoId": "v1", "skipped": True, "skip_reason": "no transcript"}]
    with open(working_dir / "extraction-00.json", "w") as f:
        json.dump(data, f)
    r = run_validator(working_dir, script_dir)
    assert r.returncode == 0


def test_rejects_malformed_json(working_dir, script_dir):
    with open(working_dir / "extraction-00.json", "w") as f:
        f.write("{not valid json")
    r = run_validator(working_dir, script_dir)
    assert r.returncode == 1
    assert "JSONDecodeError" in r.stdout or "fail" in r.stdout.lower()
