---
name: daily-dash
description: Personalized "Dear [Name]," daily dashboard. First run = setup wizard (asks name, tools, channels). Subsequent runs = refresh dashboard.html from connected MCPs (Slack/Notion/Calendar/Gmail/Granola). Smart mode auto-detects which.
---

The user invoked `/daily-dash`. This is smart mode — detect setup state and route.

## Pre-step — silent auto-update check

Before anything else, check whether a newer version of the skill is published.

1. Read the current local version from `~/.claude/skills/daily-dash/.skill-version` (single line, semver). If the file is missing, treat current version as `0.0.0`.
2. Fetch the published version from GitHub via Bash (timeout 5s, fail silently on no network):
   ```bash
   curl -fsSL --max-time 5 https://raw.githubusercontent.com/janemathias-relay/relay-daily-dash/main/.skill-version 2>/dev/null
   ```
3. Compare semver. If published > local:
   - Tell the user inline: "A newer Daily Dash is available (v<local> → v<published>). Updating now…"
   - Pull the latest into a temp directory and rsync over `~/.claude/skills/daily-dash/` **excluding** any user-generated files (none currently — the skill folder is pure template):
     ```bash
     tmp=$(mktemp -d) && \
     curl -fsSL --max-time 30 https://github.com/janemathias-relay/relay-daily-dash/archive/refs/heads/main.tar.gz | tar -xz -C "$tmp" && \
     rsync -a --delete "$tmp/relay-daily-dash-main/" ~/.claude/skills/daily-dash/ && \
     rm -rf "$tmp"
     ```
   - Re-read `.skill-version` to confirm. Print: "Updated to v<new>."
   - Continue to smart-mode routing using the updated SKILL.md instructions if they differ. If you're unsure whether your in-memory instructions are stale, ask the user to re-run `/daily-dash` once so the new SKILL.md is loaded fresh.
4. If fetch fails (offline, GitHub down, rate-limited): skip silently. Do not block the refresh.
5. If published <= local: skip silently. No message to the user.

User-generated state (`<vault>/dear-me/config.json`, `dashboard.html`, `memory/context.md`, `state/`) lives outside the skill folder and is not touched by updates.

---

## Smart-mode routing

1. Check, in order, for an existing config:
   - `$PWD/dear-me/config.json`
   - `$HOME/dear-me/config.json`
   - Any path the user volunteers in chat
2. If a config exists, branch on completeness:
   - `user.name` set AND at least one `tools.<t>.enabled === true` → run **REFRESH**.
   - `user.name` set but no tools enabled → resume **SETUP** at Step 3.
   - `user.name` missing → restart **SETUP** at Step 1 (config is corrupt or partial).
3. If no config exists → run **SETUP** from Step 1.

After EITHER mode finishes, print the appropriate open-the-dashboard block (see "Open block" at the bottom of this file).

---

# SETUP

Goal: get the user from zero to a working personalized dashboard.html in under 10 minutes.

## Step 1 — Greet + name + timezone

Brief one-liner: "Welcome to Daily Dash. I'll ask a handful of questions, then build your personalized dashboard. About 5 minutes."

Use `AskUserQuestion` to capture:
- **Name** (for the "Dear [Name]," header). Default suggestion: capitalized first part of `$USER` if available. Options: their detected first name, "use a different name". Free-text fallback via "Other".
- **Timezone**. Run `date +%Z` via Bash, surface the result as the recommended option ("Use system timezone: `America/Toronto`"), with "Pick a different timezone" as fallback (free-text via Other, expects an IANA name like `Europe/London`).

## Step 2 — Vault location

Auto-detect existing vault folders. Run exactly:

```bash
find ~/Desktop ~/Documents ~ -maxdepth 2 -type d \
  \( -name '.obsidian' -o -name 'notes' -o -name 'wiki' \) \
  -not -path '*/\.*/.*' 2>/dev/null | head -10
```

Take each match's parent directory, dedupe, present the top 3 via `AskUserQuestion`:
- "Use detected vault at `<path>`" (one per detected vault, max 3)
- "Create a new vault at `~/dear-me/`"

If user picks an existing vault, the skill creates `<vault>/dear-me/` as a subfolder. If user picks "create new", the skill creates `~/dear-me/` and treats it as the vault root.

If an existing vault was picked, also ask:
- "Want me to also scan sibling folders (`notes/`, `work-items/`, etc.) for context on each refresh?" — Yes (Recommended) / No. Saves to `vault.scan_parent`.

## Step 3 — Tools they use

`AskUserQuestion` with `multiSelect: true`:
- Slack
- Google Calendar
- Notion
- Gmail
- Granola (meeting transcripts)

Then a **separate single-select** question (radio, not multi):
- "How do you capture meeting notes?" — Granola / Notion Meeting Notes / Neither
- (Granola + Notion Meeting Notes are mutually exclusive. Whichever is picked here is what feeds calendar-event summaries.)

Tell them: tools they skip render as "Connect [Tool]" placeholder cards in the dashboard. They can enable more later by editing `dear-me/config.json`.

## Step 4 — Per-tool MCP probe + config

For each selected tool, attempt a benign read-only probe to verify the MCP is connected:

| Tool | Probe call |
|---|---|
| Slack | `slack_search_users` with `query: "me"`, `limit: 1` |
| Google Calendar | `list_calendars` (no args) |
| Notion | `notion-get-users` with `limit: 1` |
| Gmail | `list_labels` |
| Granola | `get_account_info` |
| Notion Meeting Notes | `notion-search` with `query: ""`, `page_size: 1` |

Branching:
- **Probe succeeds** → mark `tools.<t>.enabled = true`. Continue to tool-specific follow-up Qs below.
- **Probe fails OR errors ambiguously** → fall back to `AskUserQuestion`: "Is the <Tool> connector configured in Claude Code? (Settings → Connectors)" Options: "Yes, connected (re-try probe)" / "Not yet — pause setup so I can connect it".
- **User picks "Not yet"** → print: "Open Settings → Connectors → Add <Tool>, then say 'continue' when ready." Wait. On "continue", re-run the probe. Loop until success or user opts to skip.

Tool-specific follow-up questions:

**Slack** — `AskUserQuestion`: which 2–3 channels should I monitor? Free-text input — clarify in the prompt: "Paste channel names separated by commas (e.g. `#general, #marketing`). DMs and @mentions are scanned automatically — you don't need to list them." Validate channel names start with `#` or coerce. Save to `tools.slack.channels`.

**Notion** — `AskUserQuestion`: paste the URL of your tickets / operating-system database. Free-text input. Save to `tools.notion.tickets_db_url`. Mention: I'll also scan your Notion notification feed for cross-DB mentions on each refresh (capped at 5/refresh to avoid noise).

**Notion Meeting Notes** (only if selected in Step 3) — paste the parent page URL where you save meeting notes. Save to `tools.notion_meeting_notes.parent_page_url`.

**Calendar / Gmail / Granola** — no extra params. Mark `enabled: true` in config.

## Step 5 — Dashboard mode

`AskUserQuestion`:
- **File-open** (Recommended for first-time) — open the HTML directly. Simpler. Comments left on cards stay in the browser only.
- **Localhost** — run a local server. Lets card-comments sync back to Claude Code on the next `/daily-dash` refresh. Requires keeping a Terminal tab open while you use the dashboard.

Save to `mode.kind` ("file" or "localhost").

## Step 6 — Optional Q2 / quarter north-star

`AskUserQuestion` or free-text via "Other":
- "Set a quarter north-star now (one sentence)" — captures text
- "Skip — leave placeholder" (Recommended for now; can edit `dear-me/config.json` later)

Save to `q2.north_star`.

## Step 7 — Generate files

In the chosen vault location:

1. Create `dear-me/`, `dear-me/memory/`, `dear-me/scripts/`, `dear-me/state/`, `dear-me/state/archive/`.

2. Write `dear-me/config.json` from `~/.claude/skills/daily-dash/assets/config.template.json`, with all answers from Steps 1–6 filled in. Set `_meta.created_at` to ISO now.

3. Copy `~/.claude/skills/daily-dash/assets/serve-dashboard.py` → `dear-me/scripts/serve-dashboard.py`. Make executable (`chmod +x`).

4. Copy `~/.claude/skills/daily-dash/assets/dashboard-template.html` → `dear-me/dashboard.html`. Replace tokens **in order**:

   | Token | Replacement |
   |---|---|
   | `{{USER_NAME}}` | `config.user.name` (e.g. "Alex") |
   | `{{NORTH_STAR_OR_PLACEHOLDER}}` | `config.q2.north_star` if non-empty, else exactly: `Set your quarter north-star — edit dear-me/config.json → q2.north_star` |

   Verify post-substitution: grep the final file for `{{` — there should be **zero** matches.

5. Copy `~/.claude/skills/daily-dash/assets/localhost-instructions.md` → `dear-me/localhost-setup.md`. Replace **every** `{{VAULT_ROOT}}` with the absolute path to the user's vault root (the parent of `dear-me/`). Verify with another `{{` grep.

6. Write `dear-me/memory/context.md` with the initial structure documented at `~/.claude/skills/daily-dash/assets/memory-schema.md`. Seed: a single header line + an empty `## learning` YAML block (zero counts, empty maps).

## Step 8 — First refresh

Immediately call into the REFRESH flow below (skip the config-check; we just created it). This populates the dashboard for the first time.

## Step 9 — Print the open-block

Print the appropriate open-the-dashboard block (see bottom). If localhost mode, also mention: "The same instructions are saved at `<vault>/dear-me/localhost-setup.md` for future reference."

---

# REFRESH

Goal: pull fresh data from each enabled MCP and rewrite the `window.DAILY_DASH_DATA = {…}` literal in `dear-me/dashboard.html`, plus update the `window.DAILY_DASH_CONFIG = {…}` snapshot so empty-state cards know which tools are enabled.

## Step 1 — Load config + memory

Read `dear-me/config.json` and `dear-me/memory/context.md`. Note `mode.kind`, `user.timezone`, the enabled tools, slack channels, notion DB URL, and the smart-layer learning blocks (dismissals, channel_scores, comment_patterns, status_snapshot — see `assets/memory-schema.md`).

## Step 2 — Pick up pending interactions (localhost mode only)

If `mode.kind === "localhost"`:
- Read `dear-me/state/dashboard-interactions.json` if present.
- Apply pending state: `done` toggles, `boardMoves`, `notes`, `notesTs`. Treat any notes left on cards as instructions for this refresh ("pausing this", "killed", free-form context).
- Increment dismissal counters in `memory/context.md` per dismissed card (group by source section).
- After processing, move the file to `dear-me/state/archive/interactions-{ISO}.json`.

If `mode.kind === "file"`: skip.

## Step 3 — Pull from each enabled tool (graceful degrade)

For each tool in `config.tools` where `enabled === true`, attempt the pull. If the MCP isn't connected at the time of refresh, log a one-line warning to chat and leave that section empty — the HTML's `EmptyState` component handles it by rendering a "Connect <Tool>" card (gated on `window.DAILY_DASH_CONFIG.tools.<t>.enabled`).

### Slack (if enabled)
- Search the configured `tools.slack.channels` + the user's DMs + @mentions for the last 24 hours.
- For each thread where the user is awaited (last reply isn't them; question/request pending): build an entry for `slack[]` with `{ id, title, from, when, summary, links, confidence }`.
  - `confidence`: `'high'` if data is < 2h old, `'med'` if < 12h, `'low'` if older.
- Count threads → contributes to `meta.weather` "Needs you" pill.

### Calendar (if enabled)
- List events for today → `today_calendar[]`.
- List events for tomorrow → `tomorrow_calendar[]`.
- List events for Wed/Thu/Fri (or remainder of week) → `restweek_calendar[]`.
- Shape per event: `{ id, start, end, title, kind, tone, attendees, summary, links }`.
- **Auto-classify `kind`** (smart layer):
  - title matches `/\b1:1\b|\b1on1\b/i` OR (`attendees.length === 2` AND `duration ≤ 30min`) → `'1on1'`
  - title matches `/\b(team|sync|standup|weekly)\b/i` OR `attendees.length ≥ 4` (all same domain) → `'team'`
  - any attendee email outside user's domain → `'external'`
  - `attendees.length === 0` → `'focus'`
  - else → `'other'`
- Events removed from the calendar since last refresh should NOT appear (clear them).

### Notion (if enabled)
- Query the configured `tools.notion.tickets_db_url` for items where status is in-progress, planning, or done.
- Populate `today_hero[]` (P0 in-progress), `watching_p0[]`, `planning[]`, `shipped[]`.
- **Status-change detection** (smart layer): compare each item's current status against `memory/context.md → status_snapshot`. If changed, set `item.statusChange = { prev, now }` so `<StatusChangeBadge>` renders in the UI. After pull, overwrite `status_snapshot` with the new map.
- If `tools.notion.scan_notifications === true`:
  - Call `notion-search` with filter for mentions in the last 24h.
  - De-dupe against items already returned by the tickets-DB query.
  - Surface the remainder in `slack[]` with `kind: 'notion-mention'`. **Cap at 5 entries.**

### Gmail (if enabled)
- Search inbox last 24h for direct threads where user hasn't responded.
- Append each as a `slack[]` entry with `kind: 'gmail'`. (Single merged "needs response" surface — never duplicate.)

### Granola (if enabled) OR Notion Meeting Notes (if enabled, mutually exclusive)
- Pull transcripts/summaries from the last 24h.
- For each, find the matching calendar event in `today_calendar` / `restweek_calendar` (timestamp within ±30min) and populate its `summary` field.
- Standalone meetings without a calendar match: surface in `meetingPrepSuggestions[]`.

## Step 4 — Compute derived fields + smart layer

- `meta.refreshedAt` — ISO timestamp now.
- `meta.today`, `meta.todayLong`, `meta.todayShort` — formatted from current date in `config.user.timezone`.
- `meta.weekRange`, `meta.weekStart`, `meta.weekEnd` — Mon–Fri of the current week.
- `meta.weekDays[]` — 5-entry array with `today: true` on the right day.
- `meta.weather[]` — counts with `confidence` per pill: needs-you (slack[].length), overdue (Notion items where `last_updated > 7 days`), drafts-pending (0 for now), calendar-today (today_calendar.length). Confidence high if all source MCPs returned data this refresh; med if any one was stale; low if any failed.
- `meta.dashRead.items` — synthesized 3–5 action-led bullets from the highest-priority items pulled. Verb-led, no recap, no echo-back of obvious info. If nothing surfaced, use a neutral empty-state.
- `q2.glance` — counts inferred from Notion items by status: { in_flight, planning, shipped, blocked }.
- `q2.summary` — use `config.q2.north_star` if set, else "Set your quarter north-star — edit dear-me/config.json → q2.north_star".

### Smart-layer post-processing

After all pulls complete and the basic shape is built:

1. **Dismissal-based section deprioritization.** Read `memory/context.md → dismissals` (counts in last 14 days, per section). For each section with dismissals > 7, set `meta.collapsedSections[section] = true` (UI renders collapsed-by-default). For sections > 15, append a note to `meta.dashRead.items`: "You usually dismiss <section> — want me to hide it for a week?"

2. **Slack channel relevance scoring.** Read `memory/context.md → channel_scores`. For each entry in `slack[]` from a channel with `score < 0.15` AND `surface_count >= 20`, push it to the bottom of `slack[]`. Update the score for every surfaced channel: `score = responded / surfaced` (responded inferred from card notes containing `responded` / `replied`, or from the user no longer being on the awaited-side in the Slack thread).

3. **Cross-tool moment linking.** For each `today_calendar[]` event:
   - If a Granola transcript exists with matching ±30min timestamp → already attached as `summary`. Also set `event.sources = ['calendar', 'granola']`.
   - If a Slack thread in `slack[]` shares ≥2 attendees with the event AND timestamp within ±2h → add `event.sources.push('slack')` and remove the duplicate from `slack[]`.
   - If `event.sources.length >= 2` → mark `event.kind = 'moment'` (overrides the auto-classified kind). UI renders `<MomentMarker sources={event.sources} />`.

4. **Card-comment pattern learning.** Re-read the patterns from `memory/context.md → comment_patterns`. For each card surface, if a pattern's count `>= 3`, attach `card.quickActions = [...]` so the UI renders quick-action chips. (UI support is forward-compat; v1 just records the patterns.)

## Step 5 — Empty-state cards for missing tools

The `EmptyState` component in the template reads from `window.DAILY_DASH_CONFIG.tools.<t>.enabled`. As part of the rewrite (Step 6), inject a fresh `window.DAILY_DASH_CONFIG = { tools: { slack: { enabled: ... }, calendar: { enabled: ... }, ... } }` block above the `DAILY_DASH_DATA` literal, so the EmptyState branch picks the right copy.

## Step 6 — Rewrite the data literal + config snapshot

Read `dear-me/dashboard.html`. Locate the line starting with `window.DAILY_DASH_DATA = {`. Walk braces to find the matching closing `};`. Replace everything between (inclusive of both anchor lines) with the freshly computed object, serialized as readable JS (not minified — use 2-space indent, trailing commas in arrays, single-quoted strings to match existing style).

Immediately above the rewritten `DAILY_DASH_DATA` block, inject (or replace if it already exists) a `window.DAILY_DASH_CONFIG = {…}` block containing just the `tools` enabled-flag map. Use the same anchor approach — start: `window.DAILY_DASH_CONFIG = {`, end: matching `};`.

Preserve the surrounding comments. Do not touch any other part of the HTML (no CSS, no JSX, no React imports, no other consts).

## Step 7 — Update config metadata + memory

- In `dear-me/config.json`, set `_meta.last_refreshed_at` to ISO now.
- In `dear-me/memory/context.md`, append a single-line log entry:
  ```
  - <ISO> /daily-dash refresh — pulled from <comma-separated enabled tools>; today_hero=<n>, slack=<n>, today_calendar=<n>
  ```
- Update the structured YAML blocks (dismissals, channel_scores, comment_patterns, status_snapshot) in-place per `assets/memory-schema.md`.

## Step 8 — Print success + open-block

See below. Keep chat output to 5–8 lines max. No PII / no specific names or thread content.

---

# Open block

After EITHER setup or refresh, print the appropriate block for the user's mode.

## If `mode.kind === "file"`:

```
✓ Daily Dash refreshed.

Open it:
  open "<vault>/dear-me/dashboard.html"

(Or double-click the file in Finder.)

Switch to localhost mode any time by editing dear-me/config.json → mode.kind: "localhost".
Localhost lets card-comments sync back to Claude Code on the next /daily-dash.
```

## If `mode.kind === "localhost"`:

```
✓ Daily Dash refreshed.

Start the localhost server (copy each line into Terminal):

Step 1 — Free port 3000:
  kill $(lsof -ti tcp:3000) 2>/dev/null; sleep 1

Step 2 — Start the server (leave the Terminal tab open):
  python3 "<vault>/dear-me/scripts/serve-dashboard.py"

Step 3 — Open in your browser (and bookmark it):
  http://localhost:3000/dashboard.html

Step 4 — EOD shutdown: back to the Terminal tab from Step 2, press Ctrl + C.

Tip: leave notes on any card while you work — they're picked up on the next /daily-dash refresh.
(Same instructions also saved at <vault>/dear-me/localhost-setup.md.)
```

Substitute `<vault>` with the actual absolute path.

---

# Operating notes

- **Never write to a Notion page or send a Slack message during refresh.** Read-only on external surfaces. The only writes are to `dear-me/` files.
- **Graceful degrade is mandatory.** If a tool's MCP is disconnected at refresh time, log a one-line warning to chat and continue. Never abort the whole refresh.
- **No PII leakage in chat output.** Summarize counts and high-level activity, not specific names/content. Keep chat output to 5–8 lines max after refresh.
- **Token replacements happen only at setup.** Refreshes never re-substitute `{{USER_NAME}}` — that's already baked into the HTML. Refreshes only rewrite the DATA + CONFIG literals.
- **Smart layer never abandons the source of truth.** Dismissal-based collapsing, channel scoring, and moment linking are presentation hints. The underlying data arrays always reflect the latest MCP pulls — no permanent filtering.
- **If config exists but is partial** (per the smart-mode routing tree at the top): resume from the appropriate step rather than overwriting good answers.
