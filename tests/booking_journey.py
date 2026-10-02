#!/usr/bin/env python3
"""Browser journey: the homepage booking widget renders, finds open times and
refuses bad details — in a real phone browser and a real desktop browser.

    python3 tests/booking_journey.py            # chromium desktop + webkit iPhone
    python3 tests/booking_journey.py --headed

Needs `pip install playwright && python -m playwright install chromium webkit`
and `npm ci --prefix server`. Not part of scripts/test.sh (it needs browsers);
CI runs it from .github/workflows/journeys.yml when the widget or API changes.

IT NEVER BOOKS ANYTHING AND NEVER EMAILS ANYONE:
  - the page is this checkout's index.html served from a local static server;
    /api/* is proxied to server/server.js booted on a temp SQLite file with
    SMTP, calendar feeds, iCloud and weather forced off (same env as
    server/test/booking_api.test.js);
  - every POST to /api/book is aborted in the browser and counted — the test
    fails if one is ever attempted, so a validation regression can't slip a
    submission through;
  - every request that isn't to the local server (Google Analytics, fonts) is
    aborted, so a run never shows up in the site's analytics.
"""
import argparse
import datetime
import http.server
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def start_api(tmp):
    port = free_port()
    blank = " "  # see booking_api.test.js: blocks server/.env from filling it
    env = dict(os.environ, PORT=str(port), DB_PATH=os.path.join(tmp, "bookings.sqlite"),
               ADMIN_TOKEN="test-admin-token", AGENT_TOKEN=blank, SMTP_HOST=blank,
               SMTP_USER=blank, SMTP_PASS=blank, ICS_FEEDS=blank, ICLOUD_USERNAME=blank,
               ICLOUD_APP_PASSWORD=blank, ICLOUD_CALENDAR_URL=blank, SETUP_TOKEN=blank,
               OWNER_EMAIL="owner@example.invalid", LEAD_EMAIL="owner@example.invalid",
               WEATHER_ENABLED="false", TZ="America/New_York")
    log = open(os.path.join(tmp, "api.log"), "w")
    proc = subprocess.Popen(["node", os.path.join(ROOT, "server", "server.js")], env=env,
                            stdout=log, stderr=subprocess.STDOUT)
    for _ in range(100):
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{port}/api/health", timeout=1)
            break
        except Exception:
            if proc.poll() is not None:
                break
            time.sleep(0.1)
    else:
        proc.kill()
        raise SystemExit("API did not start")
    head = open(os.path.join(tmp, "api.log")).read()
    if "smtp: off" not in head or "feeds: 0" not in head:
        proc.kill()
        raise SystemExit("refusing to run: API started with email or calendars on:\n" + head)
    return proc, port


def start_site(api_port):
    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *a, **k):
            super().__init__(*a, directory=ROOT, **k)

        def log_message(self, *a):
            pass

        def _proxy(self):
            body = None
            if self.command == "POST":
                body = self.rfile.read(int(self.headers.get("content-length") or 0))
            req = urllib.request.Request(f"http://127.0.0.1:{api_port}{self.path}", data=body,
                                         method=self.command,
                                         headers={"content-type": self.headers.get("content-type", "")})
            try:
                r = urllib.request.urlopen(req, timeout=10)
                code, data, ctype = r.status, r.read(), r.headers.get("content-type")
            except urllib.error.HTTPError as e:
                code, data, ctype = e.code, e.read(), e.headers.get("content-type")
            try:
                self.send_response(code)
                self.send_header("content-type", ctype or "application/json")
                self.send_header("content-length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
            except (BrokenPipeError, ConnectionResetError):
                pass  # the widget dropped a superseded request; harmless

        def do_GET(self):
            if self.path.startswith("/api/"):
                return self._proxy()
            return super().do_GET()

        def do_POST(self):
            if self.path.startswith("/api/"):
                return self._proxy()
            self.send_error(404)

    srv = http.server.ThreadingHTTPServer(("127.0.0.1", free_port()), Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def next_weekday(days=3):
    d = datetime.date.today() + datetime.timedelta(days=days)
    while d.weekday() >= 5:
        d += datetime.timedelta(days=1)
    return d.isoformat()


def journey(browser, device, base):
    ctx = browser.new_context(**device)
    page = ctx.new_page()
    book_posts, dialogs, errors = [], [], []

    def route(r):
        url = r.request.url
        if not url.startswith(base):
            return r.abort()
        if "/api/book" in url and r.request.method == "POST":
            book_posts.append(r.request.post_data)
            return r.abort()
        return r.continue_()

    page.route("**/*", route)
    page.on("pageerror", lambda e: errors.append(str(e)))

    def on_dialog(d):
        dialogs.append(d.message)
        d.dismiss()

    page.on("dialog", on_dialog)
    page.goto(base + "/index.html#book", wait_until="domcontentloaded")

    # 1. renders: three services, a date picker, a disabled confirm button.
    page.wait_for_selector("#booking .svc-option", timeout=15000)
    assert page.locator("#booking .svc-option").count() == 3, "expected 3 services"
    assert page.locator("#bk-submit").is_disabled(), "confirm enabled before a slot was chosen"

    # 2. finds open times for an on-site estimate on a weekday.
    page.click('#booking .svc-option[data-svc="estimate"]')
    page.fill("#bk-date", next_weekday())
    page.dispatch_event("#bk-date", "change")
    page.wait_for_selector("#bk-slots .slot", timeout=15000)
    page.locator("#bk-slots .slot").first.click()
    assert not page.locator("#bk-submit").is_disabled(), "confirm still disabled with a slot chosen"
    assert page.locator("#bk-addr-field").is_visible(), "estimate must ask for the job address"

    # 3. validates: each missing field is named, nothing is posted. Wait for
    # each alert before the next click — WebKit delivers them asynchronously.
    def submit_expecting(msg):
        n = len(dialogs)
        page.click("#bk-submit")
        deadline = time.time() + 5
        while len(dialogs) == n and time.time() < deadline:
            page.wait_for_timeout(50)
        assert dialogs[n:] == [msg], f"expected alert {msg!r}, got {dialogs[n:]!r}"
        page.wait_for_timeout(250)  # let WebKit finish closing the alert

    submit_expecting("Please enter your name.")
    page.fill("#bk-name", "Journey Test")
    page.fill("#bk-phone", "123")
    submit_expecting("Please enter a valid phone number.")
    page.fill("#bk-phone", "(717) 555-0100")
    submit_expecting("Please enter the job address for your visit.")
    assert book_posts == [], f"a booking was POSTed: {book_posts!r}"

    # 4. a phone consult hides the address field.
    page.click('#booking .svc-option[data-svc="consult"]')
    assert not page.locator("#bk-addr-field").is_visible(), "consult must not ask for an address"

    assert errors == [], f"page errors: {errors!r}"
    assert book_posts == []
    ctx.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--headed", action="store_true")
    args = ap.parse_args()
    from playwright.sync_api import sync_playwright

    tmp = tempfile.mkdtemp(prefix="nemo-journey-")
    api, api_port = start_api(tmp)
    site = start_site(api_port)
    base = f"http://127.0.0.1:{site.server_address[1]}"
    failed = 0
    try:
        with sync_playwright() as p:
            lanes = [("desktop chromium", p.chromium, {"viewport": {"width": 1280, "height": 900}}),
                     ("iPhone webkit", p.webkit, p.devices["iPhone 13"])]
            for name, engine, device in lanes:
                browser = engine.launch(headless=not args.headed)
                try:
                    journey(browser, device, base)
                    print(f"ok   booking journey — {name}")
                except Exception as e:
                    failed += 1
                    print(f"FAIL booking journey — {name}: {e}")
                finally:
                    browser.close()
    finally:
        site.shutdown()
        api.kill()
        shutil.rmtree(tmp, ignore_errors=True)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
