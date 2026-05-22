#!/usr/bin/env python3
"""Serve the Daily Dash dashboard with a state write-back endpoint.

GET requests serve static files from DASH_ROOT (default behaviour).
POST /state accepts a JSON body and writes it to state/dashboard-interactions.json
so that the next /daily-dash refresh can read browser interactions
(done checkboxes, kanban drags, comments left on cards).
"""

import json
import os
import sys
from datetime import datetime, timezone
from http.server import HTTPServer, SimpleHTTPRequestHandler


# Serve from the dear-me folder that contains this script's parent directory.
# scripts/serve-dashboard.py → parent is dear-me/. Fully portable.
DASH_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
STATE_DIR = os.path.join(DASH_ROOT, "state")
STATE_FILE = os.path.join(STATE_DIR, "dashboard-interactions.json")
PORT = 3000


class DashboardHandler(SimpleHTTPRequestHandler):
    def do_POST(self):  # noqa: N802 - http.server convention
        if self.path != "/state":
            self.send_error(404, "Only POST /state is supported")
            return

        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0:
            self.send_error(400, "Empty body")
            return

        body = self.rfile.read(length)
        try:
            payload = json.loads(body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            self.send_error(400, f"Invalid JSON: {exc}")
            return

        os.makedirs(STATE_DIR, exist_ok=True)
        payload["_writtenAt"] = datetime.now(timezone.utc).isoformat()
        with open(STATE_FILE, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2, sort_keys=True)

        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

    def do_OPTIONS(self):  # noqa: N802
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        super().end_headers()

    def log_message(self, format, *args):  # noqa: A002 - keep stdlib signature
        # Quieter logs; only print writes and errors.
        if args and isinstance(args[0], str) and args[0].startswith("POST"):
            sys.stderr.write("%s - %s\n" % (self.address_string(), format % args))


def main():
    os.chdir(DASH_ROOT)
    os.makedirs(STATE_DIR, exist_ok=True)
    print(f"Serving Daily Dash from: {DASH_ROOT}")
    print(f"Open: http://localhost:{PORT}/dashboard.html")
    print(f"State writes go to: {STATE_FILE}")
    print("Stop with Ctrl+C.\n")
    HTTPServer(("127.0.0.1", PORT), DashboardHandler).serve_forever()


if __name__ == "__main__":
    main()
