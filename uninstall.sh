#!/usr/bin/env bash
# lafbot uninstaller — removes the symlink only. Your research data is untouched.
set -euo pipefail

SKILL_LINK="${HOME}/.claude/skills/lafbot"

RED=$'\033[0;31m'
GREEN=$'\033[0;32m'
YELLOW=$'\033[0;33m'
RESET=$'\033[0m'

if [ -L "$SKILL_LINK" ]; then
    rm "$SKILL_LINK"
    echo "${GREEN}✓${RESET} removed ${SKILL_LINK}"
elif [ -e "$SKILL_LINK" ]; then
    echo "${RED}✗${RESET} ${SKILL_LINK} exists but is not a symlink — refusing to remove."
    echo "If you're sure it's safe, delete it manually."
    exit 1
else
    echo "${YELLOW}!${RESET} ${SKILL_LINK} not found — nothing to remove."
fi

echo ""
echo "Your research data in ~/lafbot-research/ (or your custom vault) is untouched."
echo "Your YouTube API key in the MCP config is untouched."
echo "To remove the MCP server, run: claude mcp remove youtube"
