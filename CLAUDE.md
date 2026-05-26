# Daily Dash — CLAUDE.md

## What this is

Daily Dash is a **public, multi-user Claude Code skill** distributed to Relay teammates. Each teammate runs a setup wizard on first install, then the skill refreshes a local `dashboard.html` from their connected MCPs (Slack, Notion, Calendar, Gmail, Granola).

This repo is the source of truth for the skill. Updates land here, get committed, and propagate to teammates via the auto-updater.

---

## What this is NOT

Daily Dash is **not** Sophie. Sophie is Jane Mathias's private personal AI Chief of Staff and lives at `/Users/jane.mathias/Desktop/Admin - Jane/Sophie/` with its own git remote (`github.com/janeymathias/sophie-cos`, personal account). The two projects share architectural DNA — Daily Dash was built off Sophie's foundation — but they are different artifacts with different audiences, different conventions, and different remotes.

---

## Hard rules for this repo

1. **Out of scope: Sophie vault.** Never read, reference, or import anything from `/Users/jane.mathias/Desktop/Admin - Jane/Sophie/`. That folder contains Jane-specific and Relay-specific information that has no place in a public skill.

2. **No Jane-specific or Relay-specific assumptions.** Daily Dash runs for teammates with different roles, pods, channels, and meeting cadences. Anything hardcoded to Jane's reality is a bug.

3. **Token examples only.** Use generic placeholders in setup-wizard prompts, example dashboards, and documentation:
   - `{{USER_NAME}}` not `Jane`
   - `{{CHANNEL_1}}`, `{{CHANNEL_2}}` not `#acquisition-mkt-pod` or `#lcm-team`
   - `{{TEAMMATE_NAME}}` not `Alvin` / `Marissa` / `Shaba`
   - `{{TEAM_NAME}}` not `Lifecycle Marketing` or `MPA`

4. **Strings already scrubbed (do not regress):**
   - `acquisition-mkt-pod` (Sophie's acquisition pod Slack channel)
   - `lcm-team` (Sophie's lifecycle marketing channel)
   - `Jane` in token examples (replaced with `{{USER_NAME}}`)
   - `Strategizer` (Sophie-specific career-visibility hub; Daily Dash explicitly skipped this feature)

5. **Updates → commit → push → propagate.** Every change lands in this repo, gets committed to the `main` branch of `github.com/janemathias-relay/relay-daily-dash`, and reaches teammates via the auto-updater. Never edit a teammate's local install directly.

6. **Single-user assumptions are wrong here.** Sophie assumes always-on MCPs, a single vault, a single user. Daily Dash must handle: first-time setup, missing MCPs (use `AskUserQuestion` fallback), tool-on/off via `window.DAILY_DASH_CONFIG`, and the smart-mode router (setup vs refresh detection).

---

## Working-directory guard

If you find yourself in a Claude Code session that was started from `/Users/jane.mathias/Desktop/Admin - Jane/Sophie/`, **stop**. That session is Sophie's. Close it and start a new session from `~/.claude/skills/daily-dash/` before doing any Daily Dash work.

Sophie's slash commands (`/sweep`, `/refresh`, `/meeting-prep`, etc.) refuse to run from inside this folder. Daily Dash's `/dailydash` (or equivalent) refuses to run from inside the Sophie vault. The guard is intentional — keep the boundary clean.

---

## What lives where

| Concept | Sophie | Daily Dash |
|---|---|---|
| Audience | Jane Mathias only | Any Relay teammate |
| Naming | Sophie-flavored (`SOPHIE_DATA`, `notes/now.md`, etc.) | Generic (`DAILY_DASH_CONFIG`, `DASH_DATA`, etc.) |
| Strategizer | Core feature (`notes/strategizer/`) | Explicitly skipped — not portable |
| MCP probe | Always-on, no fallback | Two-tier with `AskUserQuestion` fallback |
| Voice files | `wiki/voices/internal.md` + `external.md` | None (different teammates → different voices) |
| Smart layer | Backported from Daily Dash (May 2026) | Original implementation |
| Auto-update | None (Sophie is the master copy) | Pulls from this repo |
| Distribution | Single-user, local | Multi-user, via auto-updater |

---

## Reference: features explicitly NOT backported into Sophie

These exist in Daily Dash because Daily Dash needs them. Sophie skipped them on purpose:

- Two-tier MCP probe with `AskUserQuestion` fallback
- `EmptyState` `Connect <Tool>` components
- Auto-update from public repo
- Genericized component names (`DashRead` instead of `SophieRead`, no Strategizer)
- `window.DAILY_DASH_CONFIG` enabled-flags snapshot
- Smart-mode routing (setup vs refresh detection)
- Token substitution table (`{{USER_NAME}}` etc.)
- `example-dashboard.html` preview file

Do not remove these from Daily Dash. They are load-bearing for the multi-user / shareable-install context.

---

## Versioning

Current version: `1.1.0` (as of 2026-05-26).

Bump on every published change. The auto-updater compares versions; teammates pull on mismatch.

Auto-update logic lives in `SKILL.md` (steps 1–3 of the entrypoint). The `.skill-version` file is the source of truth for the local version; the GitHub `main` branch's `.skill-version` is the source of truth for the published version. Don't re-derive this elsewhere — update `SKILL.md` if the flow changes.
