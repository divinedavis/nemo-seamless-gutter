#!/usr/bin/env python3
"""Generate /privacy.html using the live site's own header/footer chrome.

Google Analytics' terms and Google Ads' landing-page policy both require a
privacy policy that discloses cookies and data collection before you may run
either on a site. This generates one that matches the rest of the site so it
doesn't look bolted on.

Run once, and re-run after changing the site chrome or the disclosures below.
Dependency-free; same chrome-extraction approach as gen_article.py.
"""
import os
import re

WEB_ROOT = os.environ.get("WEB_ROOT", "/var/www/nemo-seamless-gutter")
CHROME_PAGE = os.path.join(WEB_ROOT, "guides", "seamless-vs-sectional-gutters.html")
OUT = os.path.join(WEB_ROOT, "privacy.html")

BASE = "https://nemoseamlessgutter.com"
BUSINESS = "NEMO Seamless Gutter"
CONTACT_EMAIL = "eric@nemoseamlessgutter.com"
PHONE = "(717) 578-0073"
# Bump when the disclosures below change so the page shows an honest date.
EFFECTIVE = "July 20, 2026"


def read_chrome():
    html = open(CHROME_PAGE).read()
    header = re.search(r"(<header class=\"site-header\".*?</header>)", html, re.S).group(1)
    footer_float = re.search(r"(<footer class=\"site-footer\".*?</body>)", html, re.S).group(1)
    head_links = re.search(r"(<link rel=\"icon\".*?</head>)", html, re.S).group(1)
    return head_links, header, footer_float


SECTIONS = [
    ("Who we are", f"""
      <p>{BUSINESS} installs and services seamless gutters in York County, Pennsylvania.
      This policy explains what we collect through <a href="{BASE}">{BASE.replace('https://','')}</a>,
      why, and what you can do about it. Questions go to
      <a href="mailto:{CONTACT_EMAIL}">{CONTACT_EMAIL}</a> or {PHONE}.</p>"""),

    ("Information you give us", """
      <p>When you book an appointment or submit the contact form, we collect your
      <strong>name, phone number, email address, and the job address</strong> for the property
      you want serviced, plus any notes you add. We ask for the job address because we
      cannot quote or schedule gutter work without knowing where the house is.</p>
      <p>We use this only to schedule and perform the work you asked for, and to contact you
      about that job. We do not sell it, rent it, or share it for anyone else's marketing.</p>"""),

    ("Information collected automatically", """
      <p>Like most websites, our server records standard request logs (IP address, browser
      type, pages requested, timestamps) for security and troubleshooting.</p>
      <p>We also use <strong>Google Analytics</strong> to understand which pages people find
      useful and which searches bring them here. Google Analytics sets cookies and collects
      usage data, including a truncated version of your IP address. We have IP anonymization
      enabled. We use this to improve the site, not to identify individual visitors.</p>
      <p>If you arrived from a Google ad, <strong>Google Ads</strong> may set a cookie so we
      can tell which ads lead to real enquiries. We see totals, not who you are.</p>"""),

    ("Cookies and how to refuse them", """
      <p>Cookies are small files a site stores in your browser. Ours fall into two groups:</p>
      <ul>
        <li><strong>Necessary</strong> &mdash; needed for the booking form to work correctly.</li>
        <li><strong>Analytics and advertising</strong> &mdash; set by Google as described above.</li>
      </ul>
      <p>Every major browser lets you block or delete cookies in its settings. Blocking the
      analytics and advertising cookies will not stop you from booking an appointment. You can
      also install Google's
      <a href="https://tools.google.com/dlpage/gaoptout" rel="nofollow noopener" target="_blank">opt-out
      browser add-on</a> to prevent Google Analytics from measuring your visits to any site.</p>"""),

    ("Who else can see your information", f"""
      <p>We share information only with services that make the site and our scheduling work:</p>
      <ul>
        <li><strong>Google</strong> &mdash; analytics, advertising measurement, and the email
            and calendar we use to run the business.</li>
        <li><strong>Our web host</strong> &mdash; stores the site and its logs.</li>
      </ul>
      <p>We may also disclose information if the law requires it. Otherwise, your details stay
      with us and the crew doing your job.</p>"""),

    ("How long we keep it", """
      <p>We keep booking and customer records as long as needed to service the job, honor any
      warranty, and meet tax and accounting obligations. Server logs are kept for a short
      period for security purposes. Analytics data is retained under Google's own schedule.</p>"""),

    ("Your choices", f"""
      <p>Ask us to see, correct, or delete the information we hold about you by emailing
      <a href="mailto:{CONTACT_EMAIL}">{CONTACT_EMAIL}</a>. We will respond within a reasonable
      time. If you booked an appointment and want the record removed, say so and we will delete
      it once the job and any warranty period are complete.</p>
      <p>Depending on where you live, you may have additional rights over your personal
      information. Contact us and we will honor them.</p>"""),

    ("Children", """
      <p>This site is meant for homeowners and is not directed at children under 13. We do not
      knowingly collect information from children.</p>"""),

    ("Changes", f"""
      <p>If we change how we handle your information we will update this page and move the
      effective date below. Material changes will be noted clearly.</p>
      <p class="muted">Effective {EFFECTIVE}.</p>"""),
]


def build_page(head_links, header, footer_float):
    body = "\n".join(
        f'      <h2>{title}</h2>{html}' for title, html in SECTIONS
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Privacy Policy | {BUSINESS}</title>
  <meta name="description" content="How {BUSINESS} collects, uses and protects the information you share when you book gutter work or browse our site." />
  <meta name="robots" content="index, follow" />
  <link rel="canonical" href="{BASE}/privacy.html" />
  {head_links}
<body>
  {header}
  <article class="page">
    <div class="wrap wrap-narrow">
      <h1>Privacy Policy</h1>
      <p class="lede">Plain English: we collect what we need to quote and schedule your gutter
      work, we measure how people find the site, and we don't sell your information.</p>
{body}
    </div>
  </article>
  {footer_float}
</html>
"""


def main():
    head_links, header, footer_float = read_chrome()
    open(OUT, "w").write(build_page(head_links, header, footer_float))
    print(f"[gen_privacy] wrote {OUT}\n  re-run gen_sitemap.py so it appears in sitemap.xml")


if __name__ == "__main__":
    main()
