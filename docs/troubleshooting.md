# Troubleshooting

Common failures and how to fix them. If your issue isn't here, [file a bug](../.github/ISSUE_TEMPLATE/bug_report.md).

## "MCP server youtube is not Connected"

`claude mcp list` shows youtube as ✗ or missing.

**Likely causes**:
1. You never ran the install — see `docs/youtube-api-setup.md` Step 7.
2. The MCP server crashed. Check: `node ~/mcp/claude-code-youtube-mcp/dist/index.js` — does it error?
3. Your API key is invalid or unrestricted. Re-create it (Step 3 of the setup guide).

**Fix**:
```bash
claude mcp remove youtube
claude mcp add -s user youtube -e YOUTUBE_API_KEY=YOUR_KEY -- node /full/path/to/dist/index.js
```

## "YouTube quota exhausted"

Error mentions `quotaExceeded` or HTTP 403.

**Fix**:
- Wait 24 hours — quota resets at midnight Pacific
- OR request a quota increase: Google Cloud Console → APIs & Services → Quotas → YouTube Data API v3 → request higher limit
- Don't increase comment depth unless you've expanded quota — `heavy (100+ replies)` doubles your usage

## Phase 2 agent returns malformed JSON

`validate_extraction.py` reports `slice-NN.json: FAIL`.

**Likely causes**:
1. Sonnet wrapped the output in markdown code fences (```json ... ```).
2. Trailing commas / unescaped quotes in a tactic.
3. The agent included commentary outside the JSON.

**Fix**:
The skill already auto-retries up to 2x. If after 2 retries it still fails:

1. Read the actual `extraction-NN.json` file. Often the problem is one bad video that broke the rest.
2. Either fix the JSON manually and re-run from Phase 3, OR delete the bad slice and re-run that slice with a tighter prompt.

## Cluster Architect produces a giant "miscellaneous" cluster

Phase 3 output has one cluster with >40% of all tactics.

**Cause**: the Cluster Architect bailed and dumped everything into a catch-all.

**Fix**:
1. Open `clusters.json` and read the giant cluster's `member_tactic_ids`.
2. Read 5-10 random members from `all-tactics.json`. Are they actually related?
3. If yes (the topic is just broad), accept and move on.
4. If no, re-run Phase 3 with this added to the prompt: "The previous run produced one cluster with X% of members. That's a catch-all bail. Split it into 4-6 more specific clusters."

## HTML report has no charts

Open the file in browser. Charts are blank canvases.

**Cause**: CDN failed to load (offline, firewall blocking jsdelivr/unpkg).

**Fix**:
- Open browser DevTools → Console. Look for blocked-resource errors.
- If you're offline, download chart.js + vis-network locally and edit `build_html.py` to use local paths.

## Network graph is unreadable (all nodes on top of each other)

vis-network couldn't stabilize.

**Fix**:
- Try dragging individual nodes to spread them out. The graph is interactive.
- For long-term fix, edit `build_html.py` and adjust the `barnesHut` physics constants:
  ```js
  gravitationalConstant: -12000,  // more repulsive = more spread
  springLength: 200,              // longer = more spread
  ```

## "Permission denied: install.sh"

```bash
chmod +x install.sh uninstall.sh
./install.sh
```

## "Skill loaded but /lafbot does nothing"

`/lafbot some topic` returns without doing anything.

**Likely causes**:
1. The symlink isn't right. Check: `ls -la ~/.claude/skills/lafbot` should show a symlink to your cloned repo.
2. The SKILL.md frontmatter is malformed. Verify the `name: lafbot` line is intact.
3. Claude Code didn't reload the skill list. Restart Claude Code.

## Run crashed mid-pipeline, can I resume?

Yes. Every phase writes to disk before the next starts. Look at what's in your working dir:

- Missing `discovery.json` → re-run Phase 1
- Missing `extraction-NN.json` → re-run Phase 2 for just the missing slices
- Missing `clusters.json` → re-run Phase 3
- Missing `dataset.json` → re-run `build_dataset.py`
- Missing `Deep-Research-Report.html` → re-run `build_html.py`
- Missing markdown notes → re-run `build_notes.py`

You don't have to start over.

## Vault notes are scattered across folders

`update_master_graph.py` wrote to the wrong root.

**Cause**: the vault-root detection heuristic guessed wrong.

**Fix**: set `LAFBOT_VAULT=/path/to/your/vault/root` in your env, or add `vault_path: /path/...` to `~/.lafbotrc`.

## Cost is higher than expected

Check `RUN_LOG.md` for the per-phase breakdown.

**Common culprits**:
- Set extraction depth to `heavy` — that's 2-3x more comment volume
- Re-ran Phase 2 because of JSON validation failures — each retry is a full re-extraction
- Phase 4 (Opus synthesis) accidentally re-ran multiple times — check timestamps

**Mitigation**: set `models.extraction: haiku` in `~/.lafbotrc`. Cuts cost ~60%, loses ~15% nuance.

## Still stuck?

File an issue using the bug template. Attach your RUN_LOG.md (redact any sensitive info first).
