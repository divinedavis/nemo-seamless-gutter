#!/usr/bin/env python3
"""Monthly fresh-content engine — drafts a unique local gutter guide with Claude.

Fresh, genuinely useful content is one of the strongest organic-traction levers.
This drafts ONE new long-tail guide per run, reusing the live site's header/
footer/head chrome so branding stays consistent.

SAFETY: by default it writes a DRAFT to seo/drafts/ and does NOT publish — a
human approves first, which keeps us clear of Google's "scaled content abuse"
policy. Pass --publish to move the newest draft into /guides/ live, then run
gen_sitemap.py + indexnow_submit.py to get it indexed.

Requires ANTHROPIC_API_KEY in the environment (or seo/.env). Dependency-free.
"""
import os
import re
import sys
import json
import glob
import urllib.request
import urllib.error

WEB_ROOT = os.environ.get("WEB_ROOT", "/var/www/nemo-seamless-gutter")
BASE = "https://nemoseamlessgutter.com"
MODEL = os.environ.get("NEMO_CONTENT_MODEL", "claude-sonnet-4-6")
DRAFTS = os.path.join(WEB_ROOT, "seo", "drafts")
CHROME_PAGE = os.path.join(WEB_ROOT, "guides", "seamless-vs-sectional-gutters.html")

# Rotating long-tail topics aimed at York-County gutter searches.
TOPICS = [
    "How to tell if your gutters need replacing (signs for York, PA homeowners)",
    "5 vs 6 inch gutters: which size is right for your York County home",
    "Ice dams and gutters in Pennsylvania winters: what homeowners should know",
    "Gutter maintenance checklist for fall in York County, PA",
    "Do gutter guards really work? An honest look for PA homes",
    "Copper vs aluminum gutters: cost, look and lifespan",
    "How gutters protect your foundation and basement from water damage",
    "Spring gutter cleaning: why it matters after a PA winter",
    "Downspout placement and extensions: keeping water away from your home",
    "Fascia and soffit damage from failing gutters: what to watch for",
    "How long do seamless aluminum gutters last?",
    "Gutter colors: how to match gutters to your roof and siding",
]


def load_env():
    p = os.path.join(WEB_ROOT, "seo", ".env")
    if os.path.exists(p):
        for line in open(p):
            m = re.match(r"\s*([A-Z0-9_]+)\s*=\s*(.*)\s*$", line)
            if m and not os.environ.get(m.group(1)):
                os.environ[m.group(1)] = m.group(2).strip().strip("'\"")


def read_chrome():
    """Pull the <head> boilerplate (icons/fonts/stylesheet), <header> and
    <footer>+float+script from a live page so drafts match the site exactly."""
    html = open(CHROME_PAGE).read()
    header = re.search(r"(<header class=\"site-header\".*?</header>)", html, re.S).group(1)
    footer_float = re.search(r"(<footer class=\"site-footer\".*?</body>)", html, re.S).group(1)
    head_links = re.search(r"(<link rel=\"icon\".*?</head>)", html, re.S).group(1)
    return head_links, header, footer_float


def pick_topic():
    done = {os.path.basename(p) for p in glob.glob(os.path.join(DRAFTS, "*.html"))}
    done |= {os.path.basename(p) for p in glob.glob(os.path.join(WEB_ROOT, "guides", "*.html"))}
    for t in TOPICS:
        slug = slugify(t)
        if f"{slug}.html" not in done:
            return t
    return TOPICS[0]


def slugify(t):
    s = re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")
    return s[:70]


def claude(topic):
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        print("[gen_article] ANTHROPIC_API_KEY not set — add it to seo/.env to enable. Skipping.")
        sys.exit(0)
    prompt = (
        f"Write a genuinely useful, original guide for NEMO Seamless Gutter, a seamless "
        f"gutter contractor serving York County, Pennsylvania. Topic: \"{topic}\".\n\n"
        "Audience: local homeowners. Be specific, practical and honest. Do NOT invent "
        "reviews, ratings, prices, years in business, licenses or warranties; frame any "
        "cost as 'varies — get a free written quote'. Phone is (717) 578-0073.\n\n"
        "Return ONLY valid JSON with keys: title (<=60 chars, include 'York, PA' or "
        "'York County'), meta (<=155 chars), body_html. body_html must use ONLY these "
        "tags/classes: a leading <p class=\"lead\">, then <h2>, <h3>, <p>, "
        "<ul><li><strong>..</strong> ..</li></ul>. 600-900 words. Where natural, link to "
        "/services/seamless-gutter-installation.html, /services/gutter-guards.html, "
        "/services/gutter-cleaning-repair.html. No <html>/<head>/<body>, no images."
    )
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=json.dumps({
            "model": MODEL,
            "max_tokens": 2500,
            "messages": [{"role": "user", "content": prompt}],
        }).encode(),
        headers={
            "x-api-key": key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        data = json.loads(r.read())
    text = data["content"][0]["text"]
    text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.M).strip()
    return json.loads(text)


def build_page(art, slug):
    head_links, header, footer_float = read_chrome()
    url = f"{BASE}/guides/{slug}.html"
    title = art["title"]
    meta = art["meta"]
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{title} | NEMO Seamless Gutter</title>
  <meta name="description" content="{meta}" />
  <meta name="theme-color" content="#243C94" />
  <link rel="canonical" href="{url}" />
  <meta property="og:site_name" content="NEMO Seamless Gutter" />
  <meta property="og:title" content="{title}" />
  <meta property="og:description" content="{meta}" />
  <meta property="og:type" content="article" />
  <meta property="og:url" content="{url}" />
  <meta property="og:image" content="{BASE}/assets/og.png" />
  <meta name="twitter:card" content="summary_large_image" />
  <script type="application/ld+json">
  {{"@context":"https://schema.org","@type":"Article","headline":{json.dumps(title)},
    "description":{json.dumps(meta)},
    "author":{{"@type":"Organization","name":"NEMO Seamless Gutter"}},
    "publisher":{{"@type":"Organization","name":"NEMO Seamless Gutter","logo":{{"@type":"ImageObject","url":"{BASE}/assets/logo-4k.png"}}}},
    "image":"{BASE}/assets/og.png","mainEntityOfPage":"{url}"}}
  </script>
  {head_links}
<body>
  {header}
  <section class="subhero"><div class="container">
    <p class="crumbs"><a href="/">Home</a><span>/</span><span>Guides</span><span>/</span><span class="here">{title}</span></p>
    <p class="eyebrow">Guide · York County, PA</p>
    <h1>{title}</h1>
  </div></section>
  <article class="article"><div class="container prose">
    {art["body_html"]}
    <div class="cta-band">
      <h2>Need gutters done right?</h2>
      <p>Book a free estimate in about 30 seconds — or call or text anytime.</p>
      <div class="hero-actions">
        <a href="/#book" class="btn btn-primary btn-lg">Book Online</a>
        <a href="tel:+17175780073" class="btn btn-ghost btn-lg" style="border-color:rgba(255,255,255,.55)">Call (717) 578-0073</a>
      </div>
    </div>
  </div></article>
  {footer_float}
</html>
"""


def main():
    load_env()
    os.makedirs(DRAFTS, exist_ok=True)
    publish = "--publish" in sys.argv
    if publish:
        drafts = sorted(glob.glob(os.path.join(DRAFTS, "*.html")), key=os.path.getmtime)
        if not drafts:
            print("[gen_article] no drafts to publish")
            return
        src = drafts[-1]
        dest = os.path.join(WEB_ROOT, "guides", os.path.basename(src))
        os.replace(src, dest)
        print(f"[gen_article] PUBLISHED {os.path.basename(dest)} -> /guides/. Run gen_sitemap.py + indexnow_submit.py.")
        return
    topic = pick_topic()
    art = claude(topic)
    slug = slugify(art["title"])
    out = os.path.join(DRAFTS, f"{slug}.html")
    open(out, "w").write(build_page(art, slug))
    print(f"[gen_article] DRAFT written: {out}\n  topic: {topic}\n  review it, then: gen_article.py --publish")


if __name__ == "__main__":
    main()
