#!/usr/bin/env bash
# lafbot installer — symlinks the skill into ~/.claude/skills/
set -euo pipefail

# Resolve script location, even via symlinks
SOURCE="${BASH_SOURCE[0]}"
while [ -L "$SOURCE" ]; do
    DIR="$(cd -P "$(dirname "$SOURCE")" >/dev/null 2>&1 && pwd)"
    SOURCE="$(readlink "$SOURCE")"
    [[ "$SOURCE" != /* ]] && SOURCE="$DIR/$SOURCE"
done
REPO_DIR="$(cd -P "$(dirname "$SOURCE")" >/dev/null 2>&1 && pwd)"

SKILL_SRC="${REPO_DIR}/skill"
CLAUDE_SKILLS_DIR="${HOME}/.claude/skills"
SKILL_LINK="${CLAUDE_SKILLS_DIR}/lafbot"

# Colors
RED=$'\033[0;31m'
GREEN=$'\033[0;32m'
YELLOW=$'\033[0;33m'
BLUE=$'\033[0;34m'
BOLD=$'\033[1m'
RESET=$'\033[0m'

echo "${BOLD}lafbot installer${RESET}"
echo ""

# --- Step 1: prerequisites ---

echo "${BLUE}Step 1/4:${RESET} Checking prerequisites..."

# Python
if ! command -v python3 >/dev/null 2>&1; then
    echo "${RED}✗${RESET} python3 not found. Install Python 3.9 or newer first."
    exit 1
fi
PY_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
PY_MAJOR=$(echo "$PY_VERSION" | cut -d. -f1)
PY_MINOR=$(echo "$PY_VERSION" | cut -d. -f2)
if [ "$PY_MAJOR" -lt 3 ] || { [ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 9 ]; }; then
    echo "${RED}✗${RESET} python3 version ${PY_VERSION} found. Need 3.9 or newer."
    exit 1
fi
echo "  ${GREEN}✓${RESET} python3 ${PY_VERSION}"

# Node (for the YouTube MCP)
if ! command -v node >/dev/null 2>&1; then
    echo "  ${YELLOW}!${RESET} node not found. The YouTube MCP server needs Node 18+. See docs/youtube-api-setup.md."
else
    NODE_VERSION=$(node --version | sed 's/v//')
    NODE_MAJOR=$(echo "$NODE_VERSION" | cut -d. -f1)
    if [ "$NODE_MAJOR" -lt 18 ]; then
        echo "  ${YELLOW}!${RESET} node ${NODE_VERSION} found. The YouTube MCP needs 18+."
    else
        echo "  ${GREEN}✓${RESET} node ${NODE_VERSION}"
    fi
fi

# Claude Code
if ! command -v claude >/dev/null 2>&1; then
    echo "  ${YELLOW}!${RESET} 'claude' CLI not found. lafbot needs Claude Code: https://claude.com/claude-code"
else
    echo "  ${GREEN}✓${RESET} claude CLI present"
fi

echo ""

# --- Step 2: create symlink ---

echo "${BLUE}Step 2/4:${RESET} Linking skill into ~/.claude/skills/..."

mkdir -p "$CLAUDE_SKILLS_DIR"

if [ -e "$SKILL_LINK" ] || [ -L "$SKILL_LINK" ]; then
    if [ -L "$SKILL_LINK" ]; then
        EXISTING_TARGET="$(readlink "$SKILL_LINK")"
        if [ "$EXISTING_TARGET" = "$SKILL_SRC" ]; then
            echo "  ${GREEN}✓${RESET} already installed (symlink points here)"
        else
            echo "  ${YELLOW}!${RESET} ${SKILL_LINK} already symlinks to ${EXISTING_TARGET}"
            read -rp "  Overwrite? [y/N] " yn
            if [[ "$yn" =~ ^[Yy]$ ]]; then
                rm "$SKILL_LINK"
                ln -s "$SKILL_SRC" "$SKILL_LINK"
                echo "  ${GREEN}✓${RESET} symlinked"
            else
                echo "  ${RED}✗${RESET} install aborted"
                exit 1
            fi
        fi
    else
        echo "  ${RED}✗${RESET} ${SKILL_LINK} exists and is NOT a symlink. Remove or back up before installing."
        exit 1
    fi
else
    ln -s "$SKILL_SRC" "$SKILL_LINK"
    echo "  ${GREEN}✓${RESET} symlinked ${SKILL_SRC} → ${SKILL_LINK}"
fi

echo ""

# --- Step 3: check YouTube MCP ---

echo "${BLUE}Step 3/4:${RESET} Checking YouTube MCP server..."

if command -v claude >/dev/null 2>&1; then
    if claude mcp list 2>/dev/null | grep -qE '^\s*youtube[^:]*:\s.*Connected'; then
        echo "  ${GREEN}✓${RESET} YouTube MCP is connected"
    else
        echo "  ${YELLOW}!${RESET} YouTube MCP is not connected"
        echo ""
        echo "  To set it up:"
        echo "  1. Get a YouTube Data API v3 key — see docs/youtube-api-setup.md"
        echo "  2. Install the MCP server: https://github.com/wynandw87/claude-code-youtube-mcp"
        echo "  3. Run: claude mcp add -s user youtube -e YOUTUBE_API_KEY=YOUR_KEY -- node /path/to/dist/index.js"
        echo ""
        echo "  lafbot will not work until this is connected."
    fi
else
    echo "  ${YELLOW}!${RESET} Skipping MCP check (claude CLI not on PATH)"
fi

echo ""

# --- Step 4: done ---

echo "${BLUE}Step 4/4:${RESET} ${GREEN}Done!${RESET}"
echo ""
echo "${BOLD}Try it:${RESET} in a Claude Code session, run:"
echo "  ${GREEN}/lafbot how to grow an audience on Twitter from zero${RESET}"
echo ""
echo "${BOLD}Docs:${RESET}"
echo "  README              ${REPO_DIR}/README.md"
echo "  YouTube API setup   ${REPO_DIR}/docs/youtube-api-setup.md"
echo "  Architecture        ${REPO_DIR}/docs/architecture.md"
echo "  Troubleshooting     ${REPO_DIR}/docs/troubleshooting.md"
echo ""
echo "${BOLD}Uninstall:${RESET} run ${REPO_DIR}/uninstall.sh"
