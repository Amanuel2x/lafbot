# Changelog

All notable changes to lafbot will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-05-24

### Added
- Initial public release.
- 7-phase pipeline: scoping → discovery → parallel extraction → semantic clustering → synthesis → HTML report → vault notes.
- Subject-agnostic axis inference (Phase 0) — no hardcoded stages or categories per topic.
- 10-agent parallel extraction (Phase 2) with JSON schema validation and per-agent retry.
- Sonnet "Cluster Architect" semantic clustering (Phase 3) replacing all keyword-based grouping.
- Auto-generated TLDR + contradictions + anomaly framing (Phase 4) — no hardcoded narrative.
- Generic HTML report builder with Chart.js bar chart, vis-network knowledge graph, anomaly cards, contradiction comparator, per-axis playbook.
- Cross-run master knowledge graph (`Research-Master-Index.md` + `Research-Master-Graph.json`).
- Drill-down mode: `/lafbot drill <topic-slug>/<cluster-id>` for focused mini-runs on a specific finding.
- `install.sh` + `uninstall.sh` — symlinks the skill into `~/.claude/skills/lafbot/`.
- JSON schemas for scoping + extraction outputs.
- Example output: sanitized SaaS marketing report in `examples/saas-marketing/`.
- Docs: YouTube API setup (with key restriction guidance), architecture, extending, troubleshooting.
- Test suite for the Python scripts.
- GitHub Actions CI: ruff + pytest on push/PR.
- MIT License.
