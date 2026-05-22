# memory/context.md — schema reference

`dear-me/memory/context.md` is the persistent memory layer for Daily Dash. It is read at the start of every refresh and written to at the end. It has two regions:

1. **Log** — append-only, one line per refresh. Human-scannable.
2. **Learning blocks** — structured YAML the smart layer reads and updates. Machine-parseable.

The file is plain Markdown so it stays viewable in Obsidian / any editor. Treat it as canonical state; don't hand-edit unless you mean to override a learner.

---

## File shape

```markdown
# Daily Dash memory

## log

- 2026-05-22T10:14:00Z /daily-dash refresh — pulled from slack, calendar, notion; today_hero=4, slack=7, today_calendar=5
- 2026-05-21T17:32:00Z /daily-dash refresh — pulled from slack, calendar; today_hero=3, slack=9, today_calendar=4
- ...

## learning

```yaml
dismissals:
  # Section name → count of dismissals in last 14 days. Older entries auto-decayed.
  slack: 3
  today_hero: 0
  today_calendar: 1
  followups: 0
  shipped: 0
  planning: 2
  watching_p0: 0

channel_scores:
  # Slack channel → { surfaced, responded, dismissed, score }.
  # score = responded / surfaced. Used to deprioritize noisy channels (< 0.15 with surfaced >= 20).
  "#growth-pod":
    surfaced: 24
    responded: 12
    dismissed: 4
    score: 0.50
  "#announcements":
    surfaced: 31
    responded: 4
    dismissed: 18
    score: 0.13

status_snapshot:
  # Notion item ID → last-seen status. Diffed on each refresh to detect status_change.
  "abc-123-def": "in-progress"
  "ghi-456-jkl": "planning"
  "mno-789-pqr": "shipped"

comment_patterns:
  # Pattern phrase → count of card notes matching it. After count >= 3, UI offers quick-action chip.
  "killed": 5
  "pausing": 3
  "follow up": 2
  "done": 8

confidence_history:
  # Per-section freshness log. Last refresh's confidence per surface, used by ConfidenceTag.
  slack: high
  calendar: high
  notion: med
  gmail: low
```
```

---

## Update rules per learner

| Learner | Reads | Writes | Trigger |
|---|---|---|---|
| Dismissal deprioritization | `dismissals` | `dismissals` (++ per dismissed card, grouped by section) | localhost interactions pickup |
| Channel relevance scoring | `channel_scores` | `channel_scores` (recompute on every Slack pull) | every refresh with Slack enabled |
| Event type autodetect | — | — | computed inline at refresh, not persisted |
| Moment linking | — | — | computed inline at refresh, not persisted |
| Status change flags | `status_snapshot` | `status_snapshot` (overwrite after diff) | every refresh with Notion enabled |
| Confidence indicators | `confidence_history` | `confidence_history` (overwrite each refresh) | every refresh |
| Comment pattern learning | `comment_patterns` | `comment_patterns` (++ per pattern match in notes) | localhost interactions pickup |

---

## Decay rules

- **`dismissals`** — entries older than 14 days are subtracted from the count on each refresh. The log line in the `## log` section is used to determine each dismissal's age.
- **`channel_scores`** — scores are recomputed from scratch each refresh from the rolling 30-day window. No decay logic needed.
- **`comment_patterns`** — no decay; counts accumulate forever. User can manually reset by editing the file.

---

## Disabling a learner

Each learner has a toggle in `config.json` → `learning.<learner_name>`. Setting it to `false` makes the refresh skip both the read and the write for that block. The data stays in `context.md` so re-enabling is non-destructive.

---

## Migration / corruption

If `context.md` is missing or unparseable, the refresh writes a fresh skeleton (header + empty YAML block) and proceeds with all counts at zero. No abort.
