# Examples

Sample lafbot runs to show what the output looks like before you run your own.

## saas-marketing/

A full pipeline run on **"how to market a B2B SaaS from idea to first revenue"** with emphasis on getting 0→1000 waitlist signups and uncovering anomaly tactics.

- **Videos analyzed**: 63 (2 skipped)
- **Distinct creators**: 49
- **Raw tactics extracted**: 620
- **Canonical clusters**: 69
- **Buckets**: 22 consensus, 12 emerging, 35 anomalies, 1 commenter-only
- **Runtime**: ~25 minutes
- **Cost**: ~$8 in Anthropic tokens

Files:
- [`Deep-Research-Report.html`](saas-marketing/Deep-Research-Report.html) — open in a browser to see the full report
- [`dataset.json`](saas-marketing/dataset.json) — canonical structured data
- [`00-Index.md`](saas-marketing/00-Index.md) — Obsidian entry point

### Notable findings from this run

- **Distribution > product** — the only tactic with both 8 creator AND 5 commenter mentions
- **Loom video DMs** — anomaly tactic, only 2 creators mentioned it, but cited 4-6x reply rate lift
- **AI search referrals (ChatGPT/Perplexity)** — anomaly, only 1 creator named it, with a 45K-lead case study
- **"Stop doing X" framing** beats "AI-powered Y" — surfaced from a commenter, not a creator

This is exactly the kind of insight that would have taken 50+ hours of manual YouTube watching to produce.

## Want to share your own run?

If you do a great run on an interesting topic, open a [topic idea issue](../.github/ISSUE_TEMPLATE/topic_idea.md) and link your sanitized output. We'd love to grow this examples folder.
