// NEMO Seamless Gutter — interactions
(function () {
  var header = document.getElementById('header');
  var toggle = document.getElementById('navToggle');
  var mobileNav = document.getElementById('mobileNav');

  // Header background on scroll
  function onScroll() {
    if (window.scrollY > 24) header.classList.add('scrolled');
    else header.classList.remove('scrolled');
  }
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  // Mobile nav toggle
  if (toggle && mobileNav) {
    toggle.addEventListener('click', function () {
      var open = mobileNav.classList.toggle('open');
      toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
      // force header solid bg while menu open for readability
      if (open) header.classList.add('scrolled');
    });
    mobileNav.querySelectorAll('a').forEach(function (a) {
      a.addEventListener('click', function () {
        mobileNav.classList.remove('open');
        toggle.setAttribute('aria-expanded', 'false');
        onScroll();
      });
    });
  }

  // Footer year
  var y = document.getElementById('year');
  if (y) y.textContent = new Date().getFullYear();
})();

/* Owner opt-out — keep our own visits out of the traffic numbers.
 *
 * Visit /?owner=1 once on a device and it stops being counted, forever, on
 * every network that device uses. That last part is why this exists rather
 * than a list of addresses: the developer's phone reaches the site through
 * iCloud Private Relay, which hands out a different address per session, so
 * an IP list can never keep up. /?owner=0 undoes it.
 *
 * The cookie is read server-side out of the nginx access log (growth/metrics.py
 * drops any request carrying it). Nothing is sent anywhere and no visitor who
 * hasn't opted in is affected.
 */
(function () {
  'use strict';
  var m = /[?&]owner=([01])/.exec(location.search);
  if (!m) return;
  var on = m[1] === '1';
  document.cookie = 'nemo_owner=' + (on ? '1' : '') +
    ';path=/;max-age=' + (on ? 63072000 : 0) +
    ';samesite=lax' + (location.protocol === 'https:' ? ';secure' : '');

  // Say so on screen. A silent toggle is one you can't tell failed.
  var n = document.createElement('div');
  n.textContent = on
    ? 'Owner mode ON — visits from this device are excluded from analytics.'
    : 'Owner mode OFF — this device is counted like any visitor.';
  n.setAttribute('style', 'position:fixed;left:50%;bottom:24px;transform:translateX(-50%);' +
    'z-index:9999;background:#243C94;color:#fff;padding:12px 18px;border-radius:999px;' +
    'font:600 14px/1.3 system-ui,-apple-system,sans-serif;box-shadow:0 6px 24px rgba(0,0,0,.25);' +
    'max-width:92vw;text-align:center');
  document.addEventListener('DOMContentLoaded', function () {
    document.body.appendChild(n);
    setTimeout(function () { n.remove(); }, 6000);
  });
})();
