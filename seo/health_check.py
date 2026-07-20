#!/usr/bin/env python3
"""Daily site health check — catches breakage before a customer does.

Checks, in order of how badly they'd hurt:

  mail DNS     MX + SPF still present. A nameserver change silently wiped
               these on 2026-07-20 and Eric's email bounced for an hour
               before anyone noticed. This is the regression test for that.
  pages        every sitemap URL returns 200
  links        internal links across the site actually resolve
  booking API  /api/health responds
  certificate  days until the TLS cert expires

Emails OWNER_EMAIL when something fails, but only if SMTP is configured in
server/.env -- until then it logs and exits non-zero, which cron surfaces.
That means alerting switches itself on the moment the mail credentials land,
with no change here.

Dependency-free. Run from cron:
  WEB_ROOT=/var/www/nemo-seamless-gutter python3 seo/health_check.py
"""
import os
import re
import ssl
import sys
import json
import socket
import smtplib
import datetime
import subprocess
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from email.message import EmailMessage
from urllib.parse import urljoin, urlparse

WEB_ROOT = os.environ.get("WEB_ROOT", "/var/www/nemo-seamless-gutter")
HOST = "nemoseamlessgutter.com"
BASE = f"https://{HOST}"
SITEMAP = f"{BASE}/sitemap.xml"
TIMEOUT = 20
CERT_WARN_DAYS = 21          # certbot renews at 30; warn if it hasn't by 21
UA = "NemoHealthCheck/1.0 (+https://nemoseamlessgutter.com)"

problems = []   # hard failures -> alert
notes = []      # informational, shown in the log and any alert


def load_env():
    """Read server/.env so SMTP + OWNER_EMAIL come from the same place the
    booking server uses. No override of anything already in the environment."""
    p = os.path.join(WEB_ROOT, "server", ".env")
    if not os.path.exists(p):
        return
    for line in open(p):
        m = re.match(r"\s*([A-Z0-9_]+)\s*=\s*(.*)\s*$", line)
        if m and not os.environ.get(m.group(1)):
            os.environ[m.group(1)] = m.group(2).strip().strip("'\"")


def fetch(url, method="GET"):
    req = urllib.request.Request(url, method=method, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return r.status, r.read() if method == "GET" else b""
    except urllib.error.HTTPError as e:
        return e.code, b""
    except Exception as e:
        return None, str(e).encode()


# --- mail DNS ---------------------------------------------------------------
def dig(record, name):
    try:
        out = subprocess.run(
            ["dig", "+short", record, name, "@8.8.8.8"],
            capture_output=True, text=True, timeout=15,
        )
        return [l.strip() for l in out.stdout.splitlines() if l.strip()]
    except Exception:
        return None


def check_mail_dns():
    mx = dig("MX", HOST)
    if mx is None:
        notes.append("mail DNS: dig unavailable, skipped")
        return
    # "0 ." is a null MX (RFC 7505): a valid record that explicitly refuses all
    # mail. Treat it as down, not as healthy.
    if not mx or all(re.fullmatch(r"0\s+\.?", m) for m in mx):
        problems.append(
            "MAIL DOWN: no usable MX record for " + HOST + ". Inbound email to Eric is "
            "bouncing. Re-add: MX @ -> smtp.google.com priority 1.")
    else:
        notes.append(f"mail DNS: MX ok ({', '.join(mx)})")

    txt = dig("TXT", HOST) or []
    if not any("v=spf1" in t for t in txt):
        problems.append(
            "no SPF record for " + HOST + ". Mail Eric sends will be penalised as "
            "spam. Re-add TXT @ -> v=spf1 include:_spf.google.com ~all")
    else:
        notes.append("mail DNS: SPF ok")


# --- pages ------------------------------------------------------------------
def sitemap_urls():
    status, body = fetch(SITEMAP)
    if status != 200:
        problems.append(f"sitemap.xml returned {status}")
        return []
    try:
        root = ET.fromstring(body)
    except ET.ParseError as e:
        problems.append(f"sitemap.xml is not valid XML: {e}")
        return []
    ns = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
    return [e.text.strip() for e in root.iter(ns + "loc") if e.text]


def check_pages(urls):
    bad = []
    for u in urls:
        status, _ = fetch(u, method="HEAD")
        if status != 200:
            bad.append(f"{u} -> {status}")
    if bad:
        problems.append("pages not returning 200:\n    " + "\n    ".join(bad))
    else:
        notes.append(f"pages: all {len(urls)} sitemap URLs return 200")


def check_internal_links(urls):
    """Follow internal links found on each page. Catches the classic case of a
    renamed file leaving dead links behind in the nav or footer."""
    seen, bad = set(), []
    for u in urls:
        status, body = fetch(u)
        if status != 200:
            continue
        html = body.decode("utf-8", "replace")
        for href in re.findall(r'href="([^"#?]+)', html):
            if href.startswith(("mailto:", "tel:", "sms:", "javascript:")):
                continue
            target = urljoin(u, href)
            if urlparse(target).netloc != HOST or target in seen:
                continue
            seen.add(target)
            st, _ = fetch(target, method="HEAD")
            if st != 200:
                bad.append(f"{target} -> {st}  (linked from {u})")
    if bad:
        problems.append("broken internal links:\n    " + "\n    ".join(bad))
    else:
        notes.append(f"links: {len(seen)} internal links all resolve")


# --- API + certificate ------------------------------------------------------
def check_api():
    status, body = fetch(f"{BASE}/api/health")
    if status != 200:
        problems.append(f"booking API /api/health returned {status} -- customers cannot book")
        return
    try:
        if not json.loads(body).get("ok"):
            problems.append("booking API responded but reported not ok")
            return
    except ValueError:
        problems.append("booking API returned non-JSON")
        return
    notes.append("booking API: ok")


def check_cert():
    try:
        ctx = ssl.create_default_context()
        with socket.create_connection((HOST, 443), timeout=TIMEOUT) as sock:
            with ctx.wrap_socket(sock, server_hostname=HOST) as ss:
                not_after = ss.getpeercert()["notAfter"]
        # utcnow() is deprecated and slated for removal; use an aware UTC
        # datetime so this doesn't quietly stop working on a future Python.
        exp = datetime.datetime.strptime(not_after, "%b %d %H:%M:%S %Y %Z").replace(
            tzinfo=datetime.timezone.utc)
        days = (exp - datetime.datetime.now(datetime.timezone.utc)).days
        if days < 0:
            problems.append(f"TLS certificate EXPIRED {abs(days)} days ago")
        elif days < CERT_WARN_DAYS:
            problems.append(
                f"TLS certificate expires in {days} days and certbot has not "
                f"renewed it (renewal normally happens at 30 days)")
        else:
            notes.append(f"certificate: {days} days remaining")
    except Exception as e:
        problems.append(f"could not check TLS certificate: {e}")


# --- alerting ---------------------------------------------------------------
def send_alert(body):
    host = os.environ.get("SMTP_HOST")
    user = os.environ.get("SMTP_USER")
    pw = os.environ.get("SMTP_PASS")
    to = os.environ.get("OWNER_EMAIL")
    frm = os.environ.get("FROM_EMAIL") or user
    if not (host and user and pw and to):
        print("[health] SMTP not configured yet -- alert not emailed. "
              "Configure it via setup.html and alerts start automatically.")
        return
    msg = EmailMessage()
    msg["Subject"] = f"[NEMO site] {len(problems)} problem(s) found"
    msg["From"] = f"NEMO Site Monitor <{frm}>"
    msg["To"] = to
    msg.set_content(body)
    try:
        with smtplib.SMTP(host, int(os.environ.get("SMTP_PORT", 587)), timeout=30) as s:
            s.starttls()
            s.login(user, pw)
            s.send_message(msg)
        print(f"[health] alert emailed to {to}")
    except Exception as e:
        print(f"[health] FAILED to send alert email: {e}")


def main():
    load_env()
    stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    print(f"[health] {stamp} checking {BASE}")

    check_mail_dns()
    urls = sitemap_urls()
    if urls:
        check_pages(urls)
        check_internal_links(urls)
    check_api()
    check_cert()

    for n in notes:
        print(f"[health]   ok   {n}")

    if not problems:
        print("[health] all clear")
        return 0

    report = (f"NEMO Seamless Gutter site check — {stamp}\n\n"
              f"{len(problems)} problem(s):\n\n"
              + "\n\n".join(f"* {p}" for p in problems)
              + "\n\nPassing checks:\n" + "\n".join(f"  - {n}" for n in notes) + "\n")
    print("[health] PROBLEMS FOUND")
    print(report)
    send_alert(report)
    return 1


if __name__ == "__main__":
    sys.exit(main())
