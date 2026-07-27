#!/usr/bin/env python3
"""Google Search Console — the only honest source of rank for this site.

The goal ("more than 50% of York County gutter searches") is a claim about
where the site RANKS, and nothing else can answer that. Scraping the SERP
violates Google's terms, gets blocked, and returns personalised results that
are not what anyone else sees. Until this module has a key, `keywords.summary()`
reports `share_pct = None` and every report says UNMEASURED rather than
dressing coverage up as rank.

Auth is a service-account JWT signed with `openssl` — the same dependency-free
approach seo/weekly_digest.py already uses, so the droplet needs no Python
packages installed. The key is read from seo/gsc-service-account.json.

Setup is in the module docstring of that file and in growth/README.md; the
short version is: create a service account, grant its email read access to the
Search Console DOMAIN property (sc-domain:nemoseamlessgutter.com), and drop the
JSON key on the droplet at seo/gsc-service-account.json with mode 600.
"""
import base64
import datetime
import json
import os
import subprocess
import tempfile
import urllib.error
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
SA_KEY = os.environ.get(
    "NEMO_GSC_KEY", os.path.join(HERE, "..", "seo", "gsc-service-account.json"))

# A Domain property covers http/https and every subdomain, so it is the one
# that matches what this site actually serves. A URL-prefix property would
# silently miss the www variant.
PROPERTY = os.environ.get("NEMO_GSC_PROPERTY", "sc-domain:nemoseamlessgutter.com")

SCOPE = "https://www.googleapis.com/auth/webmasters.readonly"
TIMEOUT = 60

# Search Console finalises data about 3 days back; querying up to today
# returns a partial tail that reads as a sudden decline.
LAG_DAYS = 3
WINDOW_DAYS = 28        # enough volume for a stable average position


def available():
    return os.path.exists(os.path.abspath(SA_KEY))


def list_properties(token):
    """Every property this service account can read."""
    req = urllib.request.Request(
        "https://www.googleapis.com/webmasters/v3/sites",
        headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return json.loads(r.read()).get("siteEntry", [])


def resolve_property(token):
    """Pick the property to query instead of assuming its form.

    A Domain property is `sc-domain:example.com`; a URL-prefix one is
    `https://example.com/`. They are different strings for the same site, and
    guessing wrong returns a 403 that reads like a permissions problem — which
    sends you back to re-check the thing that was never broken. Ask Google
    which properties the key can actually see, and prefer the Domain form
    because it covers www and http as well.
    """
    entries = list_properties(token)
    urls = [e.get("siteUrl", "") for e in entries]
    if PROPERTY in urls:
        return PROPERTY, urls
    host = PROPERTY.split(":", 1)[-1].rstrip("/")
    host = host.replace("https://", "").replace("http://", "").rstrip("/")
    domain_form = f"sc-domain:{host}"
    if domain_form in urls:
        return domain_form, urls
    for candidate in (f"https://{host}/", f"https://www.{host}/",
                      f"http://{host}/"):
        if candidate in urls:
            return candidate, urls
    return None, urls


def _b64url(b):
    return base64.urlsafe_b64encode(b).rstrip(b"=")


def _token(sa):
    """Mint an access token, signing the JWT with openssl so no crypto
    library is needed on the droplet."""
    now = int(datetime.datetime.now(datetime.timezone.utc).timestamp())
    header = _b64url(json.dumps({"alg": "RS256", "typ": "JWT"}).encode())
    claim = _b64url(json.dumps({
        "iss": sa["client_email"], "scope": SCOPE,
        "aud": "https://oauth2.googleapis.com/token",
        "iat": now, "exp": now + 3600,
    }).encode())
    signing_input = header + b"." + claim

    fd, path = tempfile.mkstemp(suffix=".pem")
    try:
        os.write(fd, sa["private_key"].encode())
        os.close(fd)
        os.chmod(path, 0o600)
        p = subprocess.run(["openssl", "dgst", "-sha256", "-sign", path],
                           input=signing_input, capture_output=True, timeout=20)
        if p.returncode != 0:
            raise RuntimeError("openssl signing failed: "
                               + p.stderr.decode()[:160])
        sig = _b64url(p.stdout)
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass

    body = urllib.parse.urlencode({
        "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
        "assertion": (signing_input + b"." + sig).decode()}).encode()
    req = urllib.request.Request(
        "https://oauth2.googleapis.com/token", data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return json.loads(r.read())["access_token"]


def _query(token, start, end, dimensions, limit=5000, start_row=0, prop=None):
    url = ("https://www.googleapis.com/webmasters/v3/sites/"
           f"{urllib.parse.quote(prop or PROPERTY, safe='')}/searchAnalytics/query")
    payload = json.dumps({
        "startDate": start, "endDate": end, "dimensions": dimensions,
        "rowLimit": limit, "startRow": start_row,
        # Web only: image and video rows would drag the average position
        # around for a site that has neither as a real channel.
        "type": "web",
    }).encode()
    req = urllib.request.Request(url, data=payload, headers={
        "Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return json.loads(r.read()).get("rows", [])


def fetch_queries(days=WINDOW_DAYS):
    """Every query the site appeared for in the window.

    Returns [{query, position, impressions, clicks}, …]. Raises on a real
    error — a silent empty list would look identical to "we rank for nothing",
    which is exactly the wrong conclusion to draw from a broken credential.
    """
    path = os.path.abspath(SA_KEY)
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"no Search Console key at {path} — the goal stays unmeasured "
            f"until one is installed")
    with open(path) as f:
        sa = json.load(f)
    token = _token(sa)

    prop, seen = resolve_property(token)
    if not prop:
        raise RuntimeError(
            "the service account can read no property matching "
            f"{PROPERTY!r}. Properties it CAN see: {seen or '(none)'}. "
            "If that list is empty, it has not been added under Search "
            "Console > Settings > Users and permissions.")

    end = datetime.date.today() - datetime.timedelta(days=LAG_DAYS)
    start = end - datetime.timedelta(days=days - 1)

    rows, start_row = [], 0
    while True:
        batch = _query(token, start.isoformat(), end.isoformat(),
                       ["query"], limit=5000, start_row=start_row, prop=prop)
        rows.extend(batch)
        if len(batch) < 5000:
            break
        start_row += len(batch)

    return [{"query": r["keys"][0],
             "position": r.get("position"),
             "impressions": r.get("impressions"),
             "clicks": r.get("clicks")} for r in rows if r.get("keys")]


def totals(days=WINDOW_DAYS):
    """Site-wide clicks/impressions for the window, for the report."""
    with open(os.path.abspath(SA_KEY)) as f:
        sa = json.load(f)
    token = _token(sa)
    prop, _ = resolve_property(token)
    end = datetime.date.today() - datetime.timedelta(days=LAG_DAYS)
    start = end - datetime.timedelta(days=days - 1)
    rows = _query(token, start.isoformat(), end.isoformat(), [], limit=1, prop=prop)
    if not rows:
        return {"clicks": 0, "impressions": 0, "position": None, "ctr": 0}
    r = rows[0]
    return {"clicks": r.get("clicks", 0), "impressions": r.get("impressions", 0),
            "position": r.get("position"), "ctr": r.get("ctr", 0)}


def sync(quiet=False):
    """Pull rank data and fold it into the tracked keyword universe.

    This is the call that turns the goal from a proxy into a measurement.
    Returns a dict describing what happened; never raises, because a Search
    Console outage must not take down the whole 6am run.
    """
    from . import keywords, ledger

    if not available():
        return {"ok": False, "connected": False,
                "detail": f"no key at {os.path.abspath(SA_KEY)}"}
    try:
        rows = fetch_queries()
        matched = keywords.apply_gsc(rows)
        t = totals()
    except urllib.error.HTTPError as e:
        body = e.read()[:400].decode(errors="replace")
        detail = f"HTTP {e.code}: {body[:200]}"
        if e.code == 403:
            # Both failures return 403 and they need opposite fixes. Naming the
            # wrong one sends you to re-check something that was never broken.
            low = body.lower()
            if "has not been used in project" in low or "accessnotconfigured" in low:
                detail += (" — FIX: the Search Console API is not enabled in the "
                           "Google Cloud project. Enable it at APIs & Services > "
                           "Library > Google Search Console API.")
            elif "billing" in low:
                detail += (" — FIX: the Google Cloud project needs billing enabled.")
            else:
                detail += (" — FIX: the service account is probably not added under "
                           "Search Console > Settings > Users and permissions.")
        ledger.set_state("gsc_last", {"date": ledger.today(), "ok": False,
                                      "detail": detail})
        return {"ok": False, "connected": True, "detail": detail}
    except Exception as e:
        detail = f"{type(e).__name__}: {e}"
        ledger.set_state("gsc_last", {"date": ledger.today(), "ok": False,
                                      "detail": detail})
        return {"ok": False, "connected": True, "detail": detail}

    for k, v in (("gsc_clicks", t["clicks"]), ("gsc_impressions", t["impressions"])):
        ledger.record_result(ledger.today(), "__site__", k, v)

    out = {"ok": True, "connected": True, "rows": len(rows), "matched": matched,
           "clicks": t["clicks"], "impressions": t["impressions"],
           "avg_position": round(t["position"], 1) if t.get("position") else None}
    ledger.set_state("gsc_last", {"date": ledger.today(), **out})
    if not quiet:
        print(f"  gsc: {len(rows)} queries in the last {WINDOW_DAYS}d, "
              f"{matched} matched the tracked universe · "
              f"{t['clicks']} clicks / {t['impressions']} impressions")
    return out
