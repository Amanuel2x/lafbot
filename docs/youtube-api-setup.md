# YouTube Data API v3 Setup

lafbot needs a **YouTube Data API v3 key**. The key stays on your machine. lafbot never sees it, never transmits it, and the install script doesn't touch it.

> **Security first.** Do NOT use someone else's API key. Do NOT commit your key to any repo. Do NOT paste it in a chat with another person — including AI assistants you don't control. Always restrict your key (Step 6 below) so even if it leaks, it can only be used for YouTube searches and is rate-limited to your quota.

This whole setup takes about 5 minutes. The API is **free** up to 10,000 quota units per day, which is plenty — a full lafbot run uses ~2,000 units.

---

## Step 1 — Create a Google Cloud project

1. Go to https://console.cloud.google.com/
2. Sign in with any Google account (personal works fine; you don't need a Workspace account)
3. Click the project dropdown at the top of the page → **New Project**
4. Name it anything you want (e.g. `lafbot-personal`)
5. Click **Create**, wait ~10 seconds, then make sure the new project is selected in the dropdown

## Step 2 — Enable the YouTube Data API v3

1. In the search bar at the top, type `YouTube Data API v3`
2. Click the result
3. Click the blue **Enable** button
4. Wait for it to activate (~5 seconds)

## Step 3 — Create the API key

1. In the left sidebar, navigate to **APIs & Services** → **Credentials**
2. Click **+ Create Credentials** at the top → **API Key**
3. A dialog appears with your new key. **DON'T copy it yet** — restricting it first is safer.
4. Click **Edit API key** (or close this dialog and click the key in the list)

## Step 4 — Name the key

In the **Name** field, enter something memorable like `lafbot-youtube`.

## Step 5 — Restrict the key (CRITICAL)

This is the security step. Without it, anyone who gets your key can use it for any Google API tied to your project — billable APIs included.

Under **API restrictions**:

1. Select **Restrict key**
2. In the dropdown, find and check **YouTube Data API v3**
3. (Do NOT check "Authenticate API calls through a service account" — that's for other APIs.)

Under **Application restrictions** (optional but recommended):

- If you'll only run lafbot from one machine, choose **IP addresses** and add your home/office IP
- Otherwise leave it as **None** — the API restriction above is the most important guard

Click **Save** at the bottom.

## Step 6 — Copy the key

Go back to the **Credentials** page. Click the eye icon next to your key, or click **SHOW KEY**, then copy the value. It looks like `AIzaSy...` (39 characters).

**Store it somewhere safe.** A password manager is best. If you lose it, you can always create a new one — they're free.

## Step 7 — Install the YouTube MCP server

Now you wire the key into the [claude-code-youtube-mcp](https://github.com/wynandw87/claude-code-youtube-mcp) server.

```bash
# Clone the MCP server repo
mkdir -p ~/mcp
cd ~/mcp
git clone https://github.com/wynandw87/claude-code-youtube-mcp.git
cd claude-code-youtube-mcp

# Install dependencies + build
npm install

# Register the MCP server with Claude Code
# Replace YOUR_KEY_HERE with the key you copied
claude mcp add -s user youtube \
  -e YOUTUBE_API_KEY=YOUR_KEY_HERE \
  -- node "$(pwd)/dist/index.js"

# Verify it connected
claude mcp list
```

You should see a line like:
```
youtube: node /Users/you/mcp/claude-code-youtube-mcp/dist/index.js - ✓ Connected
```

If not, see [`troubleshooting.md`](troubleshooting.md).

## Step 8 — Verify the key works

Open Claude Code and try:

```
search YouTube for "lafbot test query"
```

If the MCP can return results, your key is wired correctly.

## Step 9 — Install lafbot

```bash
cd ~/lafbot
./install.sh
```

You're done. Run `/lafbot some topic` in any Claude Code session.

---

## Cost and quota

- **Free quota**: 10,000 units/day, resets at midnight Pacific
- **What 1 unit costs**: a transcript fetch = 1 unit, a comment fetch = 1 unit, a search = 100 units
- **Per lafbot run**: ~15 searches (1,500 units) + 65 transcript pulls (65 units) + 65 comment pulls (65 units) = ~1,650 units
- You can do **5-6 full lafbot runs per day** on the free quota
- If you hit the quota, wait 24 hours OR request a quota increase in **APIs & Services** → **Quotas**

## Rotating the key

If you ever suspect your key leaked:

1. Go to **APIs & Services** → **Credentials**
2. Click your key → **Regenerate key** → confirm
3. Re-run the `claude mcp add` command from Step 7 with the new key
4. (Optional) Delete the old key after a day if no errors

## What lafbot does NOT do

- Does not transmit your API key anywhere except the YouTube MCP server you installed locally
- Does not log your key to disk
- Does not phone home or send telemetry
- Does not require an account for lafbot itself

If you see lafbot ever asking for your key, or trying to read it from somewhere other than the MCP server's env var, **that's a bug — file an issue immediately.**
