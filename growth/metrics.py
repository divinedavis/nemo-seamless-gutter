#!/usr/bin/env python3
"""Daily measurement: traffic, leads, calls — and attribution to techniques.

Everything the review loop judges comes from here. There is no analytics
database on this site, so the numbers come from two places that cannot lie:

  nginx access log   /var/log/nginx/nemo-access.log — one line per request, with
                     the referrer, so channel attribution is possible. Requires
                     the dedicated access_log directive in the nginx site config;
                     without it NEMO's requests land in the shared catch-all log
                     mixed with the other sites on this droplet and are
                     unattributable (the combined format has no Host field).

  bookings.sqlite    the booking server's database. `bookings` are jobs booked
                     through the site; `leads` are callers captured by the phone
                     agent. Those two tables ARE the revenue signal — a growth
                     technique that moves visitors but not these has not worked.

Three rules keep the year-end "what worked" list honest:

  1. Bots are excluded. Half the raw traffic to a small site is SemrushBot and
     friends; counting them turns a flat month into a hockey stick.
  2. The owner's own IPs are excluded, so a day Eric spends clicking around his
     own site does not read as growth.
  3. A technique is credited only for traffic landing on the URL prefixes it
     declares. Site-wide techniques are judged on a global series instead, and
     the ledger says which.

Deliberately NOT measured here: tel: link taps. Those fire as GA4 `contact_call`
events and GA4 has no server-side export without a service-account key. The
report names that gap rather than pretending `leads` is the whole call volume —
most callers dial the number off the page or the Business Profile and never
touch the booking form.
"""
import datetime
import gzip
import ipaddress
import os
import re
import sqlite3
import urllib.parse

from . import ledger

ACCESS_LOG = os.environ.get("NEMO_ACCESS_LOG", "/var/log/nginx/nemo-access.log")
BOOKINGS_DB = os.environ.get("NEMO_BOOKINGS_DB",
                             "/var/www/nemo-seamless-gutter/server/bookings.sqlite")

SEARCH_HOSTS = ("google.", "bing.com", "duckduckgo.com", "yahoo.", "ecosia.org",
                "search.brave.com", "yandex.", "baidu.com", "startpage.com")
AI_HOSTS = ("chatgpt.com", "chat.openai.com", "openai.com", "perplexity.ai",
            "claude.ai", "anthropic.com", "copilot.microsoft.com",
            "gemini.google.com", "bard.google.com", "you.com", "phind.com")
# Where a local contractor's referral traffic actually comes from — worth
# separating from generic referral so the citation work can be judged.
LOCAL_HOSTS = ("google.com/maps", "maps.google", "yelp.com", "angi.com",
               "homeadvisor.com", "bbb.org", "nextdoor.com", "thumbtack.com",
               "facebook.com", "houzz.com", "porch.com", "manta.com")

BOT_RE = re.compile(
    r"bot|crawl|spider|slurp|bingpreview|semrush|ahrefs|mj12|dotbot|petalbot|"
    r"yandex|baidu|facebookexternalhit|headlesschrome|python-requests|curl/|"
    r"wget|scrapy|go-http-client|okhttp|uptime|pingdom|monitor|lighthouse|"
    # Crawlers with no "bot"/"crawl"/"spider"/"slurp" substring, so the
    # pattern above misses them outright — seen hitting pages within hours
    # of a same-morning IndexNow submission, which is exactly when a
    # fresh page's owned_visitors should be zero.
    r"googleother|google-extended|google-inspectiontool|"
    r"meta-externalagent|anthropic-ai|"
    # Internet-wide scanners and HTTP libraries found in the 2026-07-28 audit,
    # all of which were being counted as visitors. NemoHealthCheck is ours —
    # the site monitoring its own uptime is not an audience.
    r"zgrab|libredtail|masscan|nuclei|censys|expanse|internet-measurement|"
    r"python-httpx|httpx/|aiohttp|java/|libwww|perl|ruby|axios|node-fetch|"
    r"nemohealthcheck",
    re.I)

# Chrome shipped v70 in 2018 and Firefox v60 the same year. A UA claiming
# something older is not a York County homeowner on an old laptop — those still
# auto-update. In the audit these were single IPs making hundreds of requests
# behind Firefox/13.0 and Firefox/47.0 strings: scrapers picking a stale UA.
ANCIENT_UA_RE = re.compile(r"Chrome/([1-9]|[1-6]\d)\.|Firefox/([1-9]|[1-5]\d)\.")

# A real visitor to a gutter contractor's site reads a few pages. Anything past
# this in one day from one address is automation, whatever its UA claims.
MAX_HUMAN_PAGES_PER_DAY = 30

# Assets are requests, not visits. Counting them makes every page view look
# like fifteen.
ASSET_RE = re.compile(
    r"\.(css|js|png|jpe?g|gif|svg|webp|ico|woff2?|ttf|eot|map|txt|xml|webmanifest)$", re.I)

LOG_RE = re.compile(
    r'^(?P<ip>\S+) \S+ \S+ \[(?P<ts>[^\]]+)\] '
    r'"(?P<method>\S+) (?P<path>\S+) [^"]*" '
    r'(?P<status>\d{3}) (?P<bytes>\S+) '
    r'"(?P<ref>[^"]*)" "(?P<ua>[^"]*)"'
    # Trailing owner-opt-out cookie, added to the log format on 2026-07-28.
    # Optional: every line written before that date ends after the user agent,
    # and those days must keep parsing or the history disappears.
    r'(?: "(?P<owner>[^"]*)")?')

MONTHS = {m: i + 1 for i, m in enumerate(
    ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
     "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"])}


def owner_ips():
    """IPs to exclude. Learned over time and stored in the ledger, seeded from
    NEMO_OWNER_IPS so the first run is not polluted either.

    Entries may be a plain address or a CIDR block. A block matters here because
    the developer's traffic has come from a corporate proxy whose egress address
    moves around a /16 — pinning single addresses would exclude yesterday's
    testing and count today's.
    """
    ips = set(ledger.get_state("owner_ips", []))
    env = os.environ.get("NEMO_OWNER_IPS", "")
    ips |= {i.strip() for i in env.split(",") if i.strip()}
    return ips


def ip_skipper(entries=None):
    """Build `skip(ip) -> bool` from owner_ips(), understanding CIDR blocks.

    Anything unparseable is kept as an exact string match, so a typo excludes
    nothing rather than silently excluding a whole range.
    """
    exact, nets = set(), []
    for e in (owner_ips() if entries is None else entries):
        if "/" in e:
            try:
                nets.append(ipaddress.ip_network(e, strict=False))
                continue
            except ValueError:
                pass
        exact.add(e)

    def skip(ip):
        if ip in exact:
            return True
        if not nets:
            return False
        try:
            addr = ipaddress.ip_address(ip)
        except ValueError:
            return False
        return any(addr in net for net in nets)

    return skip


def _parse_ts(ts):
    """'26/Jul/2026:23:50:17 +0000' → date string in the log's own offset.

    The offset is kept as-is rather than converted: nginx here logs UTC, the
    business runs on Eastern, and a day boundary shifted by four hours would
    put every evening's traffic on the wrong day. Both ends of the comparison
    use the same convention, so trends stay consistent.
    """
    try:
        d, _ = ts.split(":", 1)
        day, mon, year = d.split("/")
        return f"{year}-{MONTHS[mon]:02d}-{int(day):02d}"
    except Exception:
        return None


def _host(ref):
    if not ref or ref == "-":
        return None
    try:
        return (urllib.parse.urlparse(ref).hostname or "").lower()
    except Exception:
        return None


def classify(referrer, path):
    """Which channel did this visit come from?"""
    # An explicit utm_source wins — AI engines increasingly send no referrer
    # header and tag the URL instead, and our own campaigns are tagged.
    if path and "utm_source=" in path:
        try:
            src = urllib.parse.parse_qs(
                urllib.parse.urlparse("http://x" + path).query).get("utm_source", [""])[0].lower()
        except Exception:
            src = ""
        if any(a.split(".")[0] in src for a in AI_HOSTS):
            return "ai"
        if src in ("gbp", "google-business", "gmb"):
            return "local"
        if src:
            return "campaign"
    ref = (referrer or "").lower()
    h = _host(referrer)
    if not h:
        return "direct"
    if any(a in h for a in AI_HOSTS):
        return "ai"
    if any(a in ref for a in LOCAL_HOSTS):
        return "local"
    if any(a in h for a in SEARCH_HOSTS):
        return "organic"
    if "nemoseamlessgutter.com" in h:
        return "internal"
    return "referral"


def _open_log(path):
    if path.endswith(".gz"):
        return gzip.open(path, "rt", errors="replace")
    return open(path, errors="replace")


def read_log(dates, path=None):
    """Parse the access log(s) for the given set of date strings.

    Also reads the .1 rotation, because a 6am run needs yesterday and logrotate
    will usually have moved yesterday's tail into nemo-access.log.1 overnight.
    """
    path = path or ACCESS_LOG
    want = set(dates)
    hits = []
    for p in (path, path + ".1", path + ".2.gz"):
        if not os.path.exists(p):
            continue
        try:
            with _open_log(p) as f:
                for line in f:
                    m = LOG_RE.match(line)
                    if not m:
                        continue
                    d = _parse_ts(m.group("ts"))
                    if d not in want:
                        continue
                    hits.append(m)
        except Exception:
            continue
    return hits


def collect(days=1, end=None, log_path=None):
    """Measure the last `days` complete days. Returns {date: {metric: value}}.

    Default is yesterday only — today is still in progress, and a partial day
    recorded as a data point would poison every trend the review loop reads.
    """
    end = end or (datetime.date.today() - datetime.timedelta(days=1))
    start = end - datetime.timedelta(days=days - 1)
    dates = [(start + datetime.timedelta(days=i)).isoformat() for i in range(days)]

    matches = read_log(dates, log_path)
    skip_owner = ip_skipper()

    techs = ledger.load_techniques()
    prefixed = [(t["slug"], t.get("prefixes") or []) for t in techs if t.get("prefixes")]

    # Pass 1: shape of each address's day. A browser loading a page also loads
    # its stylesheet and script; a scraper takes the HTML and leaves. That
    # difference identifies automation that lies about its user agent, which a
    # UA blocklist can never catch up with — in the 2026-07-28 audit 232 of 272
    # addresses fetched pages and never once fetched an asset, and they were
    # 63% of all "visits". Volume is the second tell.
    wanted = set(dates)
    # Addresses seen carrying the owner-opt-out cookie. The cookie is the
    # reliable signal — it follows the device — but the first request of a
    # session can arrive before it is set, and a page load fans out into asset
    # requests that carry it. Learning the address for that day catches the
    # stragglers, and it is scoped per day so a rotating consumer IP never
    # excludes a stranger tomorrow.
    owner_seen = set()
    for m in matches:
        if (m.group("owner") or "-").strip() not in ("", "-"):
            owner_seen.add((_parse_ts(m.group("ts")), m.group("ip")))

    shape = {}
    for m in matches:
        d = _parse_ts(m.group("ts"))
        if d not in wanted:
            continue
        if (d, m.group("ip")) in owner_seen:
            continue
        s = shape.setdefault((d, m.group("ip")), {"assets": 0, "pages": 0})
        if ASSET_RE.search(m.group("path").split("?")[0]):
            s["assets"] += 1
        else:
            s["pages"] += 1

    per_day = {d: {"visitors": {}, "pages": 0, "bots": 0} for d in dates}
    for m in matches:
        d = _parse_ts(m.group("ts"))
        if d not in per_day:
            continue
        ua, ip = m.group("ua"), m.group("ip")
        path = m.group("path")
        # Ours: this browser opted out at /?owner=1. Not counted as a visit and
        # not counted as a bot either — it simply never happened, which is the
        # point of the opt-out.
        if (d, ip) in owner_seen:
            continue
        # An empty user agent is not a browser. Every browser sends one.
        if not (ua or "").strip() or ua.strip() == "-":
            per_day[d]["bots"] += 1
            continue
        if BOT_RE.search(ua) or ANCIENT_UA_RE.search(ua):
            per_day[d]["bots"] += 1
            continue
        s = shape.get((d, ip), {"assets": 0, "pages": 0})
        if s["assets"] == 0 or s["pages"] > MAX_HUMAN_PAGES_PER_DAY:
            per_day[d]["bots"] += 1
            continue
        if skip_owner(ip):
            continue
        if m.group("method") != "GET" or ASSET_RE.search(path.split("?")[0]):
            continue
        if not m.group("status").startswith("2"):
            continue
        per_day[d]["pages"] += 1
        # No cookie on this static site, so IP+UA is the visitor proxy. It
        # slightly undercounts (shared NAT) and slightly overcounts (mobile
        # roaming); both are stable, so the trend is what matters.
        vid = f"{ip}|{ua[:60]}"
        v = per_day[d]["visitors"].setdefault(
            vid, {"paths": [], "channel": None})
        v["paths"].append(path)
        if v["channel"] is None:
            v["channel"] = classify(m.group("ref"), path)

    out = {}
    for d in dates:
        vis = per_day[d]["visitors"]
        chan = {}
        for vid, v in vis.items():
            chan.setdefault(v["channel"] or "direct", set()).add(vid)
        mm = {
            "visitors": len(vis),
            "pageviews": per_day[d]["pages"],
            "bot_hits": per_day[d]["bots"],
            "organic_visitors": len(chan.get("organic", ())),
            "local_visitors": len(chan.get("local", ())),
            "ai_visitors": len(chan.get("ai", ())),
            "direct_visitors": len(chan.get("direct", ())),
            "referral_visitors": len(chan.get("referral", ())),
            "campaign_visitors": len(chan.get("campaign", ())),
        }
        for slug, prefixes in prefixed:
            n = sum(1 for v in vis.values()
                    if any(p.startswith(pre) for p in v["paths"] for pre in prefixes))
            mm[f"owned::{slug}"] = n
        out[d] = mm

    # ---- leads and bookings: the numbers that actually mean money -----------
    lead_rows = read_leads(dates)
    for d in dates:
        out[d].update(lead_rows.get(d, {"bookings": 0, "phone_leads": 0, "total_leads": 0}))
    return out


# Rows the developer created while wiring up the booking form and the phone
# assistant. Every one of them landed in the same tables a paying customer
# would, so "10 phone leads" read as demand when it was one person testing.
# Three tells, checked in order of how sure they are:
TEST_RE = re.compile(r"\btest\b|please ignore|do not book|no real customer", re.I)


def _digits(s):
    return re.sub(r"\D", "", s or "")


def owner_phones():
    """Phone numbers whose bookings and leads are ours, not customers'.

    Kept in the ledger's state file (or NEMO_OWNER_PHONES), which is never
    published to the repo or served by nginx — the number itself is personal
    data and does not belong in a public tree.
    """
    raw = set(ledger.get_state("owner_phones", []))
    raw |= {p.strip() for p in os.environ.get("NEMO_OWNER_PHONES", "").split(",") if p.strip()}
    return {_digits(p)[-10:] for p in raw if _digits(p)}


def is_own_row(row, phones=None):
    """True if this booking/lead is the developer's testing, not a customer."""
    phones = owner_phones() if phones is None else phones
    text = " ".join(str(row.get(k) or "") for k in ("name", "notes", "service", "address"))
    if TEST_RE.search(text):
        return True
    d = _digits(row.get("phone"))[-10:]
    if not d:
        return False
    if d in phones:
        return True
    # 555 is the reserved fictional exchange — nothing real ever dials it, so a
    # future test that forgets to say "test" in the name is still caught.
    return len(d) == 10 and d[3:6] == "555"


def read_leads(dates, db=None):
    """Bookings and phone-agent leads created on each date.

    created_at is written by the booking server in its configured TZ (Eastern),
    which is the business's day — so a booking taken at 8pm counts today, which
    is what Eric would say if you asked him.

    Our own test rows are not counted. A growth engine that judges techniques on
    lead volume must not be able to score itself by the developer submitting the
    form again.
    """
    db = db or BOOKINGS_DB
    out = {d: {"bookings": 0, "phone_leads": 0, "total_leads": 0} for d in dates}
    if not os.path.exists(db):
        return out
    try:
        con = sqlite3.connect(f"file:{db}?mode=ro", uri=True, timeout=10)
    except Exception:
        return out
    phones = owner_phones()
    try:
        con.row_factory = sqlite3.Row
        for table, key in (("bookings", "bookings"), ("leads", "phone_leads")):
            try:
                rows = con.execute(
                    f"select * from {table} "
                    f"where substr(created_at,1,10) in ({','.join('?' * len(dates))})",
                    dates).fetchall()
            except sqlite3.Error:
                continue
            for r in rows:
                row = dict(r)
                d = str(row.get("created_at") or "")[:10]
                if d in out and not is_own_row(row, phones):
                    out[d][key] += 1
    finally:
        con.close()
    for d in out:
        out[d]["total_leads"] = out[d]["bookings"] + out[d]["phone_leads"]
    return out


def lead_totals(db=None):
    """All-time counts, for the goal panel in the report.

    Our own test rows are excluded and counted separately, so a zero here reads
    as "no customer has called yet" instead of being hidden behind a dozen rows
    the developer created.
    """
    db = db or BOOKINGS_DB
    totals = {"bookings_all_time": 0, "phone_leads_all_time": 0, "own_rows_excluded": 0}
    if not os.path.exists(db):
        return totals
    try:
        con = sqlite3.connect(f"file:{db}?mode=ro", uri=True, timeout=10)
    except Exception:
        return totals
    phones = owner_phones()
    try:
        con.row_factory = sqlite3.Row
        for table, key in (("bookings", "bookings_all_time"),
                           ("leads", "phone_leads_all_time")):
            try:
                rows = con.execute(f"select * from {table}").fetchall()
            except sqlite3.Error:
                continue
            for r in rows:
                if is_own_row(dict(r), phones):
                    totals["own_rows_excluded"] += 1
                else:
                    totals[key] += 1
    finally:
        con.close()
    return totals


def record_day(date, m):
    """Write one day's measurements into the ledger, attributing where we can."""
    for k, v in m.items():
        if k.startswith("owned::"):
            ledger.record_result(date, k.split("::", 1)[1], "owned_visitors", v)
        else:
            ledger.record_result(date, "__site__", k, v)


def collect_and_record(days=1, log_path=None):
    data = collect(days=days, log_path=log_path)
    for d, m in sorted(data.items()):
        record_day(d, m)
    totals = lead_totals()
    today = ledger.today()
    for k, v in totals.items():
        ledger.record_result(today, "__site__", k, v)
    return data, totals
