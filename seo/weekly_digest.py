#!/usr/bin/env python3
"""Weekly digest emailed to the owner every Monday.

Two layers, by design:

  Always works, no setup
    leads    new bookings this week vs last, broken out by service. This is
             the number that actually matters -- did the site produce work.
    health   a one-line site-health summary (mail DNS, pages, API, cert).
    indexing how many pages are in the sitemap / being crawled.

  Activates once a Search Console service-account key is present
    search   top queries, top pages, clicks, impressions, avg position for
             the last 7 days, pulled from the Search Console API.

The Search Console part needs a service account (see SETUP below). Until the
key file exists the digest still sends with the leads + health sections and a
short note that search data will appear once it's connected. GSC also has a
2-3 day lag and near-zero history on a new site, so that section stays sparse
for the first few weeks regardless -- expected, not a bug.

Dependency-free: JWT signing uses the openssl binary, everything else is
stdlib. Reuses SMTP config from server/.env (same as health_check.py).

SETUP for the search section (one time):
  1. console.cloud.google.com -> create/pick a project
  2. Enable "Google Search Console API"
  3. Create a Service Account -> add a JSON key -> download it
  4. Save that JSON on the droplet as seo/gsc-service-account.json (chmod 600)
  5. In Search Console -> Settings -> Users and permissions -> add the service
     account's client_email as a Full or Restricted user of the
     nemoseamlessgutter.com property
"""
import os
import re
import ssl
import json
import base64
import socket
import smtplib
import sqlite3
import datetime
import tempfile
import subprocess
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from email.message import EmailMessage

WEB_ROOT = os.environ.get("WEB_ROOT", "/var/www/nemo-seamless-gutter")
HOST = "nemoseamlessgutter.com"
BASE = f"https://{HOST}"
DB = os.path.join(WEB_ROOT, "server", "bookings.sqlite")
SA_KEY = os.path.join(WEB_ROOT, "seo", "gsc-service-account.json")
GSC_PROPERTY = f"sc-domain:{HOST}"   # Domain property in Search Console
TIMEOUT = 25

SERVICE_LABELS = {
    "estimate": "Free estimate",
    "cleaning": "Gutter cleaning / repair",
    "consult": "Phone consultation",
}


def load_env():
    p = os.path.join(WEB_ROOT, "server", ".env")
    if not os.path.exists(p):
        return
    for line in open(p):
        m = re.match(r"\s*([A-Z0-9_]+)\s*=\s*(.*)\s*$", line)
        if m and not os.environ.get(m.group(1)):
            os.environ[m.group(1)] = m.group(2).strip().strip("'\"")


def week_bounds(now):
    """Rolling 7-day windows: the last 7 days, and the 7 days before that.

    Rolling (not calendar) windows so the numbers are meaningful no matter
    which day the cron actually fires -- a Monday-morning send would show an
    almost-empty calendar week, which is not what "this week" should mean.
    Returns (prev_start, boundary, now): prior week is [prev_start, boundary),
    current week is [boundary, now)."""
    boundary = now - datetime.timedelta(days=7)
    prev_start = now - datetime.timedelta(days=14)
    return prev_start, boundary, now


# --- leads -----------------------------------------------------------------
def leads_section():
    if not os.path.exists(DB):
        return "Bookings\n  (booking database not found)\n", 0
    # Naive UTC: the DB stores created_at as ISO with a trailing Z, and these
    # window bounds only need to sort lexicographically against those strings.
    now = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
    prev_mon, mon, _ = week_bounds(now)
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    def count(lo, hi):
        rows = con.execute(
            "select service, count(*) c from bookings "
            "where created_at >= ? and created_at < ? group by service",
            (lo.isoformat(), hi.isoformat())).fetchall()
        return {r["service"]: r["c"] for r in rows}
    this_wk = count(mon, now)
    last_wk = count(prev_mon, mon)
    con.close()

    this_total = sum(this_wk.values())
    last_total = sum(last_wk.values())
    lines = ["New booking requests"]
    lines.append(f"  This week: {this_total}    (last week: {last_total})")
    if this_wk:
        for svc, n in sorted(this_wk.items(), key=lambda x: -x[1]):
            lines.append(f"    - {SERVICE_LABELS.get(svc, svc)}: {n}")
    if this_total == 0:
        lines.append("    No requests through the site this week.")
    return "\n".join(lines) + "\n", this_total


# --- health ----------------------------------------------------------------
def health_section():
    issues = []
    # mail DNS
    try:
        mx = subprocess.run(["dig", "+short", "MX", HOST, "@8.8.8.8"],
                            capture_output=True, text=True, timeout=15).stdout
        if not mx.strip() or re.fullmatch(r"0\s+\.?\s*", mx.strip()):
            issues.append("mail MX record missing")
        txt = subprocess.run(["dig", "+short", "TXT", HOST, "@8.8.8.8"],
                             capture_output=True, text=True, timeout=15).stdout
        if "v=spf1" not in txt:
            issues.append("SPF record missing")
    except Exception:
        pass
    # homepage + api
    for path, label in (("/", "homepage"), ("/api/health", "booking system")):
        try:
            req = urllib.request.Request(BASE + path, method="HEAD")
            with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
                if r.status != 200:
                    issues.append(f"{label} returned {r.status}")
        except Exception:
            issues.append(f"{label} unreachable")
    # cert
    try:
        ctx = ssl.create_default_context()
        with socket.create_connection((HOST, 443), timeout=TIMEOUT) as s:
            with ctx.wrap_socket(s, server_hostname=HOST) as ss:
                na = ss.getpeercert()["notAfter"]
        exp = datetime.datetime.strptime(na, "%b %d %H:%M:%S %Y %Z").replace(
            tzinfo=datetime.timezone.utc)
        days = (exp - datetime.datetime.now(datetime.timezone.utc)).days
        if days < 14:
            issues.append(f"HTTPS certificate expires in {days} days")
    except Exception:
        issues.append("could not check HTTPS certificate")

    if issues:
        return "Site health\n" + "\n".join(f"  ! {i}" for i in issues) + "\n"
    return "Site health\n  All good -- site up, email routing, HTTPS valid.\n"


# --- indexing --------------------------------------------------------------
def indexing_section():
    try:
        with urllib.request.urlopen(f"{BASE}/sitemap.xml", timeout=TIMEOUT) as r:
            root = ET.fromstring(r.read())
        ns = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
        n = sum(1 for _ in root.iter(ns + "loc"))
        return f"Pages\n  {n} pages published and in the sitemap for Google.\n"
    except Exception:
        return "Pages\n  (could not read sitemap)\n"


# --- Search Console (optional) ---------------------------------------------
def _b64url(b):
    return base64.urlsafe_b64encode(b).rstrip(b"=")


def _gsc_token(sa):
    """Mint an OAuth access token from the service account, signing the JWT
    with openssl so we need no crypto library."""
    now = int(_utcnow_epoch())
    header = _b64url(json.dumps({"alg": "RS256", "typ": "JWT"}).encode())
    claim = _b64url(json.dumps({
        "iss": sa["client_email"],
        "scope": "https://www.googleapis.com/auth/webmasters.readonly",
        "aud": "https://oauth2.googleapis.com/token",
        "iat": now, "exp": now + 3600,
    }).encode())
    signing_input = header + b"." + claim

    keyfd, keypath = tempfile.mkstemp(suffix=".pem")
    try:
        os.write(keyfd, sa["private_key"].encode()); os.close(keyfd)
        os.chmod(keypath, 0o600)
        proc = subprocess.run(
            ["openssl", "dgst", "-sha256", "-sign", keypath],
            input=signing_input, capture_output=True, timeout=20)
        if proc.returncode != 0:
            raise RuntimeError("openssl signing failed: " + proc.stderr.decode()[:120])
        sig = _b64url(proc.stdout)
    finally:
        try: os.unlink(keypath)
        except OSError: pass

    assertion = (signing_input + b"." + sig).decode()
    body = urllib.parse.urlencode({
        "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
        "assertion": assertion,
    }).encode()
    req = urllib.request.Request("https://oauth2.googleapis.com/token", data=body,
                                 headers={"Content-Type": "application/x-www-form-urlencoded"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return json.loads(r.read())["access_token"]


def _utcnow_epoch():
    return datetime.datetime.now(datetime.timezone.utc).timestamp()


def _gsc_query(token, start, end, dimensions, limit=5):
    url = (f"https://www.googleapis.com/webmasters/v3/sites/"
           f"{urllib.parse.quote(GSC_PROPERTY, safe='')}/searchAnalytics/query")
    payload = json.dumps({
        "startDate": start, "endDate": end,
        "dimensions": dimensions, "rowLimit": limit,
    }).encode()
    req = urllib.request.Request(url, data=payload, headers={
        "Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return json.loads(r.read()).get("rows", [])


def search_section():
    if not os.path.exists(SA_KEY):
        return ("Search performance\n"
                "  Not connected yet. Add a Search Console service-account key\n"
                "  (seo/gsc-service-account.json) to include weekly search terms,\n"
                "  clicks and ranking here. See SETUP in seo/weekly_digest.py.\n")
    try:
        sa = json.load(open(SA_KEY))
        token = _gsc_token(sa)
        today = datetime.date.today()
        end = today - datetime.timedelta(days=3)      # GSC ~3-day lag
        start = end - datetime.timedelta(days=6)
        totals = _gsc_query(token, start.isoformat(), end.isoformat(), [], limit=1)
        queries = _gsc_query(token, start.isoformat(), end.isoformat(), ["query"], 5)
        pages = _gsc_query(token, start.isoformat(), end.isoformat(), ["page"], 5)
    except urllib.error.HTTPError as e:
        detail = e.read().decode()[:160]
        return f"Search performance\n  (Search Console API error {e.code}: {detail})\n"
    except Exception as e:
        return f"Search performance\n  (could not fetch: {type(e).__name__}: {e})\n"

    out = [f"Search performance  ({start:%b %d} - {end:%b %d})"]
    if totals:
        t = totals[0]
        out.append(f"  {int(t['clicks'])} clicks, {int(t['impressions'])} impressions, "
                   f"avg position {t['position']:.1f}")
    else:
        out.append("  No search impressions yet -- normal for a new site; "
                   "this fills in over the coming weeks.")
    if queries:
        out.append("  Top search terms:")
        for r in queries:
            out.append(f"    - \"{r['keys'][0]}\"  {int(r['clicks'])} clicks, "
                       f"{int(r['impressions'])} shown, pos {r['position']:.0f}")
    if pages:
        out.append("  Top pages:")
        for r in pages:
            path = r["keys"][0].replace(BASE, "") or "/"
            out.append(f"    - {path}  {int(r['clicks'])} clicks")
    return "\n".join(out) + "\n"


# --- compose + send --------------------------------------------------------
def send(subject, body):
    host = os.environ.get("SMTP_HOST")
    user = os.environ.get("SMTP_USER")
    pw = os.environ.get("SMTP_PASS")
    to = os.environ.get("OWNER_EMAIL")
    frm = os.environ.get("FROM_EMAIL") or user
    if not (host and user and pw and to):
        print("[digest] SMTP not configured; digest not sent. Body follows:\n")
        print(body)
        return
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = f"NEMO Website <{frm}>"
    msg["To"] = to
    msg.set_content(body)
    with smtplib.SMTP(host, int(os.environ.get("SMTP_PORT", 587)), timeout=30) as s:
        s.starttls()
        s.login(user, pw)
        s.send_message(msg)
    print(f"[digest] sent to {to}")


def main():
    load_env()
    today = datetime.date.today()
    leads, lead_count = leads_section()
    body = (
        f"NEMO Seamless Gutter -- weekly website report\n"
        f"Week ending {today:%B %d, %Y}\n"
        f"{'='*44}\n\n"
        f"{leads}\n"
        f"{search_section()}\n"
        f"{indexing_section()}\n"
        f"{health_section()}\n"
        f"{'-'*44}\n"
        f"See the site: {BASE}\n"
        f"This report is generated automatically each Monday.\n"
    )
    subject = f"NEMO website: {lead_count} booking request(s) this week"
    print(body)
    send(subject, body)
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
