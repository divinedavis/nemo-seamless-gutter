#!/usr/bin/env python3
"""Page shells, copied structurally from the hand-built pages already ranking.

This matters more than it looks. The site's CSS is written against specific
class names (`subhero`, `container prose`, `cta-band`, `related-grid`); a
generated page that invents its own markup renders unstyled and reads as a
throwaway doorway page to both visitors and Google. Everything here mirrors
areas/seamless-gutters-dover-pa.html so a generated page is structurally
indistinguishable from a hand-written one.

Placeholders are `{name}` — callers use .format(), so any literal brace in the
markup has to be doubled.
"""

HEAD = """<!DOCTYPE html>
<html lang="en">
<head>
  <!-- Google tag (gtag.js) -->
  <script async src="https://www.googletagmanager.com/gtag/js?id={ga}"></script>
  <script>
    window.dataLayer = window.dataLayer || [];
    function gtag(){{dataLayer.push(arguments);}}
    gtag('js', new Date());
    gtag('config', '{ga}');
  </script>
  <script src="/analytics.js?v=1" defer></script>

  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{title}</title>
  <meta name="description" content="{meta_desc}" />
  <meta name="theme-color" content="#243C94" />
  <link rel="canonical" href="{canonical}" />
{geo}
  <meta property="og:site_name" content="NEMO Seamless Gutter" />
  <meta property="og:title" content="{og_title}" />
  <meta property="og:description" content="{meta_desc}" />
  <meta property="og:type" content="{og_type}" />
  <meta property="og:url" content="{canonical}" />
  <meta property="og:image" content="https://nemoseamlessgutter.com/assets/og.png" />
  <meta property="og:locale" content="en_US" />
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="{og_title}" />
  <meta name="twitter:description" content="{meta_desc}" />
  <meta name="twitter:image" content="https://nemoseamlessgutter.com/assets/og.png" />

  <script type="application/ld+json">
{primary_ld}
  </script>
  <script type="application/ld+json">
{faq_ld}
  </script>

  <link rel="icon" href="/favicon.ico" sizes="16x16 32x32 48x48" />
  <link rel="icon" href="/assets/favicon-96.png" type="image/png" sizes="96x96" />
  <link rel="icon" href="/assets/favicon.svg" type="image/svg+xml" />
  <link rel="apple-touch-icon" href="/assets/apple-touch-icon.png" />
  <link rel="manifest" href="/site.webmanifest" />
  <link rel="stylesheet" href="/styles.css?v=1" />
</head>
<body>

  <header class="site-header" id="header">
    <div class="container header-inner">
      <a href="/" class="brand" aria-label="NEMO Seamless Gutter home">
        <img class="brand-logo brand-logo-light" src="/assets/logo-white.png" alt="NEMO Seamless Gutter" width="170" height="68" />
        <img class="brand-logo brand-logo-dark" src="/assets/logo.png" alt="NEMO Seamless Gutter" width="170" height="68" />
      </a>
      <nav class="nav" aria-label="Primary">
        <a href="/#services">Services</a>
        <a href="/#why">Why Us</a>
        <a href="/#about">About</a>
        <a href="/#faq">FAQ</a>
        <a href="/#book">Book</a>
        <a href="/#contact">Contact</a>
      </nav>
      <a href="/#book" class="btn btn-sm btn-primary header-cta">Free Estimate</a>
      <button class="nav-toggle" id="navToggle" aria-label="Open menu" aria-expanded="false">
        <span></span><span></span><span></span>
      </button>
    </div>
    <div class="mobile-nav" id="mobileNav">
      <a href="/#services">Services</a>
      <a href="/#why">Why Us</a>
      <a href="/#about">About</a>
      <a href="/#faq">FAQ</a>
      <a href="/#book">Book</a>
      <a href="/#contact">Contact</a>
      <a href="/#book" class="btn btn-primary">Book Online</a>
      <a href="tel:+17175780073" class="btn btn-ghost" style="border-color:var(--line);color:var(--navy)">Call (717) 578-0073</a>
    </div>
  </header>

  <section class="subhero">
    <div class="container">
      <p class="crumbs"><a href="/">Home</a><span>/</span><a href="{crumb_href}">{crumb_label}</a><span>/</span><span class="here">{crumb_here}</span></p>
      <p class="eyebrow">{eyebrow}</p>
      <h1>{h1}</h1>
      <p>{lede}</p>
      <div class="hero-actions">
        <a href="/#book" class="btn btn-primary btn-lg">Book a Free Estimate</a>
        <a href="tel:+17175780073" class="btn btn-ghost btn-lg">Call or Text (717) 578-0073</a>
      </div>
    </div>
  </section>

  <article class="article">
    <div class="container prose">
{body}

      <div class="cta-band">
        <h2>{cta_heading}</h2>
        <p>Book a free seamless gutter estimate in about 30 seconds — or call or text anytime.</p>
        <div class="hero-actions">
          <a href="/#book" class="btn btn-primary btn-lg">Book Online</a>
          <a href="tel:+17175780073" class="btn btn-ghost btn-lg" style="border-color:rgba(255,255,255,.55)">Call (717) 578-0073</a>
        </div>
      </div>

      <div class="related">
        <h3>Related</h3>
        <div class="related-grid">
          <a href="/services/seamless-gutter-installation.html">Seamless Gutter Installation →</a>
          <a href="/services/half-round-gutters.html">Half-Round Gutters →</a>
          <a href="/services/gutter-guards.html">Gutter Guards / Leaf Protection →</a>
          <a href="/services/gutter-cleaning-repair.html">Gutter Cleaning &amp; Repair →</a>
        </div>
      </div>
{nearby}
    </div>
  </article>

  <footer class="site-footer">
    <div class="container footer-inner">
      <div class="footer-brand">
        <img src="/assets/logo-white.png" alt="NEMO Seamless Gutter" width="210" height="84" style="margin-bottom:6px" />
        <p>Seamless gutters done right.<br/>Installation, guards, cleaning &amp; repair.<br/>Serving York, PA &amp; surrounding areas.</p>
      </div>
      <div class="footer-col">
        <h4>Services</h4>
        <a href="/services/seamless-gutter-installation.html">Seamless Gutter Installation</a>
        <a href="/services/half-round-gutters.html">Half-Round Gutters</a>
        <a href="/services/gutter-guards.html">Gutter Guards / Leaf Protection</a>
        <a href="/services/gutter-cleaning-repair.html">Gutter Cleaning &amp; Repair</a>
        <a href="/#services">All Services</a>
      </div>
      <div class="footer-col">
        <h4>Get in touch</h4>
        <a href="tel:+17175780073">Call (717) 578-0073</a>
        <a href="sms:+17175780073">Text (717) 578-0073</a>
        <a href="/#contact">Free Estimate</a>
      </div>
    </div>
    <div class="container footer-bottom">
      <p>© <span id="year"></span> NEMO Seamless Gutter. All rights reserved.</p>
      <p>Seamless · Local · Reliable · <a href="/privacy.html">Privacy Policy</a></p>
    </div>
  </footer>

  <a href="tel:+17175780073" class="call-bar"
     aria-label="Call NEMO Seamless Gutter at (717) 578-0073">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72c.13.96.36 1.9.7 2.81a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45c.91.34 1.85.57 2.81.7A2 2 0 0 1 22 16.92Z"/></svg>
    <span>Call (717) 578-0073</span>
    <span class="call-bar-sub">Free estimate</span>
  </a>

  <script src="/script.js?v=1"></script>
</body>
</html>
"""

GEO_META = """
  <meta name="geo.region" content="US-PA" />
  <meta name="geo.placename" content="{town}, Pennsylvania" />
  <meta name="geo.position" content="{lat};{lon}" />
  <meta name="ICBM" content="{lat}, {lon}" />
"""

# The nearby-areas block. `data-growth="nearby"` is the anchor internal_links
# looks for, so refreshing it is a replace rather than an ever-growing pile of
# duplicated blocks.
NEARBY_BLOCK = """
      <div class="related" data-growth="nearby">
        <h3>Nearby service areas</h3>
        <div class="related-grid">
{links}
        </div>
      </div>"""
