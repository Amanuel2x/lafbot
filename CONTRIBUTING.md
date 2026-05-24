# Contributing to lafbot

Thanks for considering a contribution. This doc explains how to file issues, propose changes, and submit PRs.

## TL;DR

- Found a bug? File an issue using the bug template.
- Want a feature? Open a feature request first. Don't surprise-PR a large change.
- Want to submit a fix? Fork, branch, PR. CI must be green.

## Before you contribute

- **Read the architecture doc**: `docs/architecture.md`. Understand the 7-phase pipeline before changing core logic.
- **Don't commit your API key.** Ever. We have a `.gitignore` to help, but check `git diff` before committing.
- **Test on a real run.** If you change a script, run the full pipeline on at least one topic before opening a PR. Output stub data isn't good enough — semantic clustering can only be validated against real raw tactics.

## Setup

```bash
git clone https://github.com/YOUR_USERNAME/lafbot.git
cd lafbot

# Install dev dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt

# Run the test suite
pytest tests/

# Lint
ruff check skill/scripts/

# Install the skill locally
./install.sh
```

## What we want

**Good contributions (highest signal first):**

1. **Better clustering prompts.** The Cluster Architect agent in `skill/pipeline/03_clustering.md` is the highest-leverage piece. If you can make it produce tighter clusters with fewer false positives, that helps every user.
2. **Multi-source extraction.** Adding Reddit / blog post / podcast extraction phases. See `docs/extending.md`.
3. **Better false-positive detection.** Catching bad clusters before they pollute the report.
4. **HTML report improvements.** Better visualizations, accessibility, mobile UX.
5. **More test coverage.** Especially on the `build_dataset.py` semantic merge logic.
6. **Documentation.** Especially `docs/troubleshooting.md` — every new failure mode you hit is one another user will too.

**Bad contributions (please don't):**

- Hardcoding keywords for specific topics. The whole point of V2 was killing keyword dependencies.
- Adding paid third-party services as a dependency.
- "Cleanup" PRs that rename or restructure code without a clear functional benefit.
- Anything that requires the user to share their API key with our infrastructure. lafbot never phones home.

## Code style

- **Python**: ruff config in `pyproject.toml`. 100-char lines, type hints on public functions, no f-strings with literal `{{}}` (look up why — it bit us once).
- **Markdown in skill files**: write for an agent to follow, not a human. Imperative voice, specific schemas, no marketing fluff.
- **Commit messages**: conventional commits format. `feat:`, `fix:`, `docs:`, `test:`, `refactor:`, `chore:`.

## PR checklist

Before requesting review:

- [ ] CI is green (ruff + pytest)
- [ ] If you changed a script, you ran a real full-pipeline test
- [ ] You updated relevant docs (README, architecture, troubleshooting)
- [ ] You added/updated tests for changed logic
- [ ] You did NOT commit any API keys, run output, or personal data
- [ ] CHANGELOG.md has an entry under `[Unreleased]`

## Filing good issues

**For bugs:**
- What topic did you run lafbot on?
- What phase failed? (Look at RUN_LOG.md)
- What was the error message? (Verbatim, not paraphrased)
- What did you expect to happen?
- Attach the `RUN_LOG.md` from the failed run (with any sensitive data removed)

**For feature requests:**
- What problem are you trying to solve? (Not what feature you want — what the underlying need is)
- Why is the current pipeline insufficient?
- Have you checked `docs/extending.md` to see if it's covered there?

## Code of conduct

See `CODE_OF_CONDUCT.md`. Be excellent to each other.
