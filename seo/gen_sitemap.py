#!/usr/bin/env python3
"""Auto-regenerate sitemap.xml from the live site files.

Scans the web root for .html pages, writes accurate <lastmod> from each file's
modification time, and auto-includes any NEW pages (e.g. service-area pages)
without anyone editing the sitemap by hand. Run daily by cron + after deploys.
"""
import os
import html
import datetime

WEB_ROOT = os.environ.get("WEB_ROOT", "/var/www/nemo-seamless-gutter")
BASE = "https://nemoseamlessgutter.com"
SKIP_DIRS = {"server", "node_modules", ".git", "assets", "seo"}
SKIP_FILES = {"setup.html", "404.html"}          # owner-only / error page: keep out of index
TOP_PRIORITY = {"index.html": "1.0"}


def main():
    urls = []
    for dirpath, dirs, files in os.walk(WEB_ROOT):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in files:
            if not f.endswith(".html") or f in SKIP_FILES:
                continue
            full = os.path.join(dirpath, f)
            rel = os.path.relpath(full, WEB_ROOT)
            loc = BASE + "/" if rel == "index.html" else BASE + "/" + rel.replace(os.sep, "/")
            lastmod = datetime.date.fromtimestamp(os.path.getmtime(full)).isoformat()
            priority = TOP_PRIORITY.get(rel, "0.8" if os.sep not in rel else "0.7")
            urls.append((loc, lastmod, priority))

    urls.sort(key=lambda u: (u[2] == "0.7", u[0]))  # homepage + top-level first
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for loc, lastmod, priority in urls:
        lines.append(
            f"  <url><loc>{html.escape(loc)}</loc>"
            f"<lastmod>{lastmod}</lastmod>"
            f"<changefreq>weekly</changefreq>"
            f"<priority>{priority}</priority></url>"
        )
    lines.append("</urlset>")
    with open(os.path.join(WEB_ROOT, "sitemap.xml"), "w") as fh:
        fh.write("\n".join(lines) + "\n")
    print(f"[gen_sitemap] wrote {len(urls)} URLs to sitemap.xml")


if __name__ == "__main__":
    main()
