#!/usr/bin/env python3
"""Submit every site URL to IndexNow for near-instant indexing.

IndexNow pushes URL changes straight to Bing, Yandex, Seznam, Naver (and their
partners) instead of waiting weeks for a crawl. It's free and keyless to sign up
for — you just host a <key>.txt ownership file at the web root.

SELF-ACTIVATING: it first checks that the live domain actually serves our key
file. While the domain is still parked elsewhere (pre-transfer) this is a no-op,
so the cron is harmless now and switches on automatically once DNS points here.
"""
import os
import re
import sys
import json
import urllib.request
import urllib.error

WEB_ROOT = os.environ.get("WEB_ROOT", "/var/www/nemo-seamless-gutter")
HOST = "nemoseamlessgutter.com"


def read_key():
    with open(os.path.join(WEB_ROOT, "seo", "indexnow_key.txt")) as fh:
        return fh.read().strip()


def domain_serves_key(key):
    """True only when https://HOST/<key>.txt returns our key (i.e. DNS + our
    server are live). Guards against submitting before the domain points here."""
    url = f"https://{HOST}/{key}.txt"
    try:
        with urllib.request.urlopen(url, timeout=10) as r:
            return r.read().decode().strip() == key
    except Exception as e:
        print(f"[indexnow] key file not live yet at {url} ({e}); skipping")
        return False


def sitemap_urls():
    with open(os.path.join(WEB_ROOT, "sitemap.xml")) as fh:
        return re.findall(r"<loc>([^<]+)</loc>", fh.read())


def main():
    key = read_key()
    if not domain_serves_key(key):
        sys.exit(0)
    urls = sitemap_urls()
    payload = {
        "host": HOST,
        "key": key,
        "keyLocation": f"https://{HOST}/{key}.txt",
        "urlList": urls,
    }
    req = urllib.request.Request(
        "https://api.indexnow.org/indexnow",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            print(f"[indexnow] submitted {len(urls)} URLs -> HTTP {r.status}")
    except urllib.error.HTTPError as e:
        # 200/202 = accepted; 422 = some URLs rejected; anything else logged
        print(f"[indexnow] HTTP {e.code}: {e.read().decode()[:200]}")


if __name__ == "__main__":
    main()
