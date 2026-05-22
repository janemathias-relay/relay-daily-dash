# Daily Dash

A personalized "Dear [Name]," daily dashboard for Relay. Pulls from your connected MCPs (Slack, Calendar, Notion, Gmail, Granola) and renders a single-page HTML you can open in your browser or run on localhost.

Built by Jane Mathias; templated for anyone at Relay to spin up their own.

---

## What you get

- A 4-tab dashboard (Today, This Week, Follow-Ups, Q2) personalized with your name.
- Auto-refresh from connected MCPs every time you run `/daily-dash` in Claude Code.
- Empty-state cards for tools you haven't connected — connect them later by editing one config file.
- Optional localhost mode: leave notes on any card and they're picked up by Claude Code on the next refresh.

No vault required. No prior setup. Setup wizard takes ~5 minutes.

> **Preview before you install:** open `assets/example-dashboard.html` in your browser. It shows what the dashboard looks like with sample data, so you know what you're getting.

---

## Install (3 steps)

### 1. Drop the skill folder into your Claude Code skills directory

If you received a zip: unzip into `~/.claude/skills/`. If you received a folder, copy it there:

```
mkdir -p ~/.claude/skills
cp -R /path/to/daily-dash ~/.claude/skills/
```

You should end up with `~/.claude/skills/daily-dash/SKILL.md` and `~/.claude/skills/daily-dash/assets/`. Restart Claude Code so the new skill is registered.

> If Claude Code doesn't pick up the skill, check Settings → Skills to confirm the path. On older versions the path may be `~/.config/claude/skills/`.

### 2. Run the skill in Claude Code

In any Claude Code session:

```
/daily-dash
```

First run = setup wizard. It will ask you ~6 questions:

1. Your name (for the "Dear [Name]," header)
2. Where to put the dashboard files — pick an existing vault folder, or create a new `~/dear-me/`
3. Which tools you use daily (Slack, Calendar, Notion, Gmail, Granola — multi-select)
4. Per-tool setup (Slack channels to monitor, Notion tickets DB URL, etc.)
5. File-open mode vs localhost mode
6. Optional: a one-sentence Q2 north-star

### 3. Open the dashboard

After the wizard, the skill prints either an `open <file>` command or a 4-step localhost copy-paste block, depending on the mode you chose.

---

## Daily use

Run `/daily-dash` in Claude Code whenever you want fresh data. The skill will:

- Pull from each connected MCP for the last 24 hours
- Rewrite the data block inside `dashboard.html`
- Tell you to refresh your browser

That's it. No other commands.

---

## Adding a tool later

Three steps:

1. **Connect the MCP.** In Claude Code: Settings → Connectors → Add (Slack / Notion / Calendar / Gmail / Granola).
2. **Edit `<vault>/dear-me/config.json`.** Set `tools.<tool>.enabled: true` and fill in any tool-specific params (Slack channels, Notion DB URL, Notion Meeting Notes parent page URL).
3. **Run `/daily-dash`.** The next refresh starts pulling from the newly enabled tool.

The skill probes each enabled MCP at refresh time and gracefully degrades if it's not actually connected — you'll see a "Connect <Tool>" card on the dashboard instead of an error.

---

## Updating Daily Dash to a new version

Auto-updates. Every time you run `/daily-dash`, the skill checks the public repo for a newer version. If one exists, it pulls + installs it before refreshing your dashboard, then continues normally. You'll see a one-liner like "Updated to v1.2.0" inline.

Your config, dashboard, and memory live in `<vault>/dear-me/` — never in the skills folder — so updates never touch your data.

If you'd rather pin a version, edit `~/.claude/skills/daily-dash/.skill-version` to a higher number than the published one and the updater will skip.

If you'd rather disable auto-update entirely, delete the "Pre-step — silent auto-update check" section from `SKILL.md`.

---

## Privacy

- Everything lives on your machine. No data leaves your laptop unless you open an MCP integration that does (Slack, Notion, etc. — same scope as the connector).
- **Don't share raw screenshots of `dashboard.html` externally.** Channel names, ticket DB URLs, and meeting titles are visible in the source. If you want to show off the dashboard, take a cropped screenshot of just one section.
- Your `dear-me/config.json` contains channel names + DB URLs in plain text. Treat it like any other local config file.

---

## File-open vs localhost: which mode?

**File-open** (simpler): double-click the HTML or use `open <path>`. Comments you leave on cards stay in your browser only.

**Localhost** (two-way): runs a tiny Python server on port 3000. Comments on cards get written to a file Claude Code reads on the next refresh. Lets you tell future-you (via Claude Code) things like "pausing this", "killed", or "follow up Thursday" without leaving the dashboard.

Switch any time by editing `mode.kind` in `config.json`.

---

## What's in the folder after setup

```
<vault>/dear-me/
├── dashboard.html           # The dashboard itself
├── config.json              # Your name, tools, channels, mode
├── memory/
│   └── context.md           # Persistent context for Claude Code (last refresh, etc.)
├── scripts/
│   └── serve-dashboard.py   # Localhost server (only used in localhost mode)
└── state/
    └── dashboard-interactions.json   # Card-comments waiting to be picked up (localhost only)
```

---

## FAQ

**Does this share data with anyone?** No. Everything lives locally. Your config, your vault, your MCPs.

**Can I customize the HTML?** Yes — but anything inside the `window.DAILY_DASH_DATA = {…}` block gets overwritten on every refresh. Edit the surrounding CSS/JSX freely.

**Can I share my dashboard with a teammate?** Not built in. The whole point is each person runs their own. If demand is high we'll look at a "share read-only snapshot" feature later.

**I'm getting an empty dashboard.** Check `<vault>/dear-me/config.json` — make sure at least one tool has `enabled: true` and the corresponding MCP is connected in Claude Code (Settings → Connectors).

**Localhost server won't start — port 3000 in use.** Run `kill $(lsof -ti tcp:3000) 2>/dev/null` and try again.

---

## Feedback

Built by Jane Mathias. Ping her in Slack with issues, requests, or "this is great, here's what I'd add next." This is v1 — rough edges expected.
