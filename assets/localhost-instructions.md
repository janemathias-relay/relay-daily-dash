# Daily Dash — Localhost Startup

Copy-paste these into Terminal. Bookmark Step 3 in your browser.

**Step 1 — Free port 3000** (paste, hit Enter):
```
kill $(lsof -ti tcp:3000) 2>/dev/null; sleep 1
```

**Step 2 — Start the dashboard server** (paste, hit Enter — leave the Terminal tab open):
```
python3 "{{VAULT_ROOT}}/dear-me/scripts/serve-dashboard.py"
```

**Step 3 — Open in browser** (paste into address bar, then bookmark it):
```
http://localhost:3000/dashboard.html
```

**Step 4 — At EOD, shut down the server:** click back into the Terminal tab from Step 2 and press `Ctrl + C`.

---

## Why use localhost mode?

When you leave a comment on any card in the dashboard, the server writes it to `dear-me/state/dashboard-interactions.json`. The next time you run `/daily-dash`, Claude Code picks up those comments and acts on them — marking items done, moving them between columns, or flagging follow-ups based on what you wrote.

If you open the dashboard as a plain file (`file://...`) instead of localhost, comments live only in your browser's localStorage and **never reach Claude Code**. Pick localhost if you plan to use the dashboard as a two-way surface.

## File-open mode (simpler)

If you skipped localhost during setup, just double-click `{{VAULT_ROOT}}/dear-me/dashboard.html` or run:
```
open "{{VAULT_ROOT}}/dear-me/dashboard.html"
```

You can switch modes any time by editing `mode.kind` in `dear-me/config.json` from `"file"` to `"localhost"` (or vice versa).
