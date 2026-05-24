#!/usr/bin/env python3
"""Validate extraction-*.json files against the extraction schema.

Usage:
  python3 validate_extraction.py <working_dir>

Returns 0 if all files valid, 1 otherwise. Prints per-file status.
"""
import glob
import json
import os
import sys

REQUIRED_VIDEO_KEYS = {"videoId"}
REQUIRED_TACTIC_KEYS = {"text", "source", "stage", "category", "confidence", "quote"}
VALID_SOURCES = {"creator", "commenter"}
VALID_CONFIDENCES = {"high", "medium", "low"}
VALID_CLAIM_TYPES = {"actionable", "data-point", "framing", "warning", "story", None}


def validate_video(v, idx, fp):
    errs = []
    if not isinstance(v, dict):
        errs.append(f"video[{idx}] is not a dict")
        return errs
    missing = REQUIRED_VIDEO_KEYS - set(v.keys())
    if missing:
        errs.append(f"video[{idx}] missing keys: {missing}")
        return errs
    if v.get("skipped"):
        return errs  # skipped videos don't need tactics
    tactics = v.get("tactics", [])
    if not isinstance(tactics, list):
        errs.append(f"video[{idx}].tactics is not a list")
        return errs
    for ti, t in enumerate(tactics):
        if not isinstance(t, dict):
            errs.append(f"video[{idx}].tactics[{ti}] not a dict")
            continue
        missing = REQUIRED_TACTIC_KEYS - set(t.keys())
        if missing:
            errs.append(f"video[{idx}].tactics[{ti}] missing: {missing}")
        if t.get("source") not in VALID_SOURCES:
            errs.append(f"video[{idx}].tactics[{ti}] bad source: {t.get('source')}")
        if t.get("confidence") not in VALID_CONFIDENCES:
            errs.append(f"video[{idx}].tactics[{ti}] bad confidence: {t.get('confidence')}")
        ct = t.get("claim_type")
        if ct not in VALID_CLAIM_TYPES:
            errs.append(f"video[{idx}].tactics[{ti}] bad claim_type: {ct}")
        if not isinstance(t.get("text"), str) or len(t.get("text", "")) < 3:
            errs.append(f"video[{idx}].tactics[{ti}] text too short")
    return errs


def validate_file(fp):
    try:
        with open(fp) as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return False, [f"JSONDecodeError: {e}"]
    except FileNotFoundError:
        return False, ["file does not exist"]
    if not isinstance(data, list):
        return False, ["root is not a JSON array"]
    all_errs = []
    for i, v in enumerate(data):
        all_errs.extend(validate_video(v, i, fp))
    return len(all_errs) == 0, all_errs


def main():
    if len(sys.argv) != 2:
        print("usage: validate_extraction.py <working_dir>", file=sys.stderr)
        sys.exit(2)
    working_dir = sys.argv[1]
    files = sorted(glob.glob(os.path.join(working_dir, "extraction-*.json")))
    if not files:
        print(f"no extraction-*.json files in {working_dir}", file=sys.stderr)
        sys.exit(1)
    n_ok = 0
    n_fail = 0
    failed_files = []
    for fp in files:
        ok, errs = validate_file(fp)
        name = os.path.basename(fp)
        if ok:
            with open(fp) as f:
                data = json.load(f)
            n_videos = len(data)
            n_tactics = sum(len(v.get("tactics", [])) for v in data if not v.get("skipped"))
            n_skipped = sum(1 for v in data if v.get("skipped"))
            print(f"  {name}: OK ({n_videos} videos, {n_tactics} tactics, {n_skipped} skipped)")
            n_ok += 1
        else:
            print(f"  {name}: FAIL")
            for e in errs[:5]:
                print(f"      - {e}")
            if len(errs) > 5:
                print(f"      ... and {len(errs)-5} more errors")
            failed_files.append(name)
            n_fail += 1
    print()
    print(f"Summary: {n_ok}/{len(files)} files valid")
    if failed_files:
        print(f"Failed: {failed_files}")
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
