#!/usr/bin/env python3
"""Generate /privacy.html using the live site's own header/footer chrome.

Google Analytics' terms require a privacy policy that discloses cookies and
data collection. Every statement below must match what the site actually does
(FormSubmit, Google Workspace mail, the nemo_vid beacon, Consent Mode). This generates one that matches the rest of the site so it
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
FROM_EMAIL = "enemo@nemoseamlessgutter.com"
# Bump when the disclosures below change so the page shows an honest date.
EFFECTIVE = "September 27, 2026"


def read_chrome():
    html = open(CHROME_PAGE).read()
    header = re.search(r"(<header class=\"site-header\".*?</header>)", html, re.S).group(1)
    footer_float = re.search(r"(<footer class=\"site-footer\".*?</body>)", html, re.S).group(1)
    head_links = chrome_head(html)
    return head_links, header, footer_float


def chrome_head(html):
    """The consent + Google tag + analytics.js block, then the icon/font/stylesheet
    links. Only those two slices: the chrome page's own <title>, canonical, OG tags and
    JSON-LD sit between them, and copying the whole span gave privacy.html two titles
    and two canonicals (the chrome guide's second)."""
    tag = re.search(r"(<!-- Google tag.*?analytics\.js[^>]*></script>)", html, re.S).group(1)
    links = re.search(r"(<link rel=\"icon\".*?</head>)", html, re.S).group(1)
    return tag + "\n\n  " + links


SECTIONS = [
    ("Who we are", f"""
      <p>{BUSINESS} installs and services seamless gutters in York County, Pennsylvania.
      This policy explains what we collect through <a href="{BASE}">{BASE.replace('https://','')}</a>,
      why, who else handles it, and what you can do about it. Questions go to
      <a href="mailto:{CONTACT_EMAIL}">{CONTACT_EMAIL}</a> or {PHONE}.</p>"""),

    ("Information you give us", f"""
      <p><strong>Online booking.</strong> When you book a time, we collect your <strong>name,
      phone number, email address, the job address</strong> (not needed for a phone
      consultation) and any notes you add, plus the service and time you picked. This is
      stored in our booking database on our own server.</p>
      <p><strong>Estimate request form.</strong> The &ldquo;Request Free Estimate&rdquo; form
      (name, phone, email, message) is delivered by
      <a href="https://formsubmit.co/" rel="nofollow noopener" target="_blank">FormSubmit</a>
      (formsubmit.co), a third-party form-to-email service: your entries go to FormSubmit, which
      emails them to us. That form is not stored on our server.</p>
      <p>We use this information only to quote, schedule and do the work you asked for and to
      contact you about that job. We do not sell it, rent it, or share it for anyone else's
      marketing.</p>"""),

    ("Email and calendar", f"""
      <p>Booking confirmations, reminders, weather reschedules and alerts to our crew are sent
      from our Google Workspace email ({FROM_EMAIL}) through Google's mail servers. Each booking
      is emailed to you and to us as a calendar invitation (.ics) containing your name, phone,
      email, job address and notes, and we add it to our own calendar, which may be Google
      Calendar or Apple iCloud Calendar.</p>
      <p>Our booking system can also write appointments straight into Apple iCloud Calendar
      and read busy times from our calendars to avoid double-booking. Those direct calendar
      connections are currently switched off; if we turn them on, the same booking details
      will be stored in Apple iCloud.</p>"""),

    ("Information collected automatically", """
      <p><strong>Server logs.</strong> Our web server records standard request logs (IP
      address, browser type, pages requested, referring page, timestamps). They are used for
      security, troubleshooting and counting visits, and are deleted after 14 days.</p>
      <p><strong>Visit counter.</strong> To count visitors without relying on Google, our
      server sets a first-party cookie called <code>nemo_vid</code> containing a random ID
      (or, if cookies are blocked, stores one in your browser's local storage). Each page view
      and each tap on a &ldquo;call&rdquo; link sends that ID, the page and the referring page
      back to our own server. It is not shared with anyone and cannot identify you by name.</p>
      <p><strong>Google Analytics.</strong> We use Google Analytics 4 (measurement ID
      G-JWSK5E1ZRZ) to see which pages people use and which searches bring them here, including
      when someone taps to call or text us or completes a booking. Google Analytics sets cookies
      and Google receives your IP address and browsing data from our pages. We do not run
      Google Ads or any advertising or remarketing tags.</p>
      <p><strong>Fonts.</strong> Our pages load fonts from Google Fonts, so your browser
      contacts Google's servers and shares your IP address when a page loads.</p>"""),

    ("Cookies and how to refuse them", """
      <ul>
        <li><strong>Necessary / first-party</strong> &mdash; <code>nemo_vid</code> (visit
            counting, described above) and a <code>consent.v1</code> entry in local storage that
            remembers your cookie choice.</li>
        <li><strong>Analytics</strong> &mdash; Google Analytics cookies (names starting with
            <code>_ga</code>).</li>
      </ul>
      <p>If you are in the European Economic Area, the UK or Switzerland, Google Analytics
      cookies are off by default (Google Consent Mode) and we ask before turning them on.
      Anyone can block or delete cookies in their browser settings, or install Google's
      <a href="https://tools.google.com/dlpage/gaoptout" rel="nofollow noopener" target="_blank">opt-out
      browser add-on</a>. Blocking cookies will not stop you from booking.</p>"""),

    ("Who else handles your information", """
      <ul>
        <li><strong>Google</strong> &mdash; Google Analytics, Google Fonts, and the Google
            Workspace email we send and receive booking messages with.</li>
        <li><strong>FormSubmit</strong> &mdash; delivers the estimate request form to our
            inbox.</li>
        <li><strong>Apple</strong> &mdash; iCloud Calendar, if we keep your appointment there
            (see &ldquo;Email and calendar&rdquo;).</li>
        <li><strong>DigitalOcean</strong> &mdash; hosts our website, booking database and
            server logs.</li>
        <li><strong>U.S. National Weather Service</strong> &mdash; we check the public forecast
            for York County to schedule outdoor work; no personal information is sent.</li>
      </ul>
      <p>We may also disclose information if the law requires it. We do not sell personal
      information and do not share it for cross-context behavioral advertising.</p>"""),

    ("How long we keep it", """
      <p>We keep booking and customer records as long as needed to service the job, honor any
      warranty, and meet tax and accounting obligations. Server logs are deleted after 14 days.
      Google Analytics data is kept under the retention setting in our Google Analytics account
      and Google's own schedule. Estimate-form emails stay in our mailbox until we delete
      them.</p>"""),

    ("Your rights", f"""
      <p><strong>Everyone:</strong> email <a href="mailto:{CONTACT_EMAIL}">{CONTACT_EMAIL}</a>
      to see, correct or delete the information we hold about you. We will respond within 30
      days. If you booked an appointment and want the record removed, we will delete it, except
      what we must keep for an open job, a warranty, or tax records.</p>
      <p><strong>California residents (CCPA/CPRA):</strong> you have the right to know what
      personal information we collect and how we use it, to access it, to have it corrected or
      deleted, and to opt out of its sale or sharing &mdash; we do neither. We will not treat you
      differently for using these rights. We verify requests by confirming the email or phone
      number on the booking; an authorized agent may ask on your behalf.</p>
      <p><strong>EEA, UK and Swiss residents (GDPR / UK GDPR):</strong> you have the right to
      access, correct, delete, restrict or object to our use of your information, to receive
      it in a portable format, and to withdraw consent at any time (for analytics cookies, clear
      this site's storage and choose again when asked). We rely on your request for a quote or
      booking (contract), your consent (analytics cookies), and our legitimate interest in
      securing and improving the site. You may complain to your local data protection
      authority.</p>"""),

    ("Children", """
      <p>This site is meant for homeowners and is not directed at children under 13. We do not
      knowingly collect information from children.</p>"""),

    ("Changes", f"""
      <p>If we change how we handle your information we will update this page and the date
      below. Material changes will be noted clearly.</p>
      <p class="muted">Last updated: {EFFECTIVE}.</p>"""),
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
      <p class="muted">Last updated: {EFFECTIVE}</p>
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
