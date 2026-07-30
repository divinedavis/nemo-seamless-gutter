/* Conversion tracking for GA4.
 *
 * The three things worth counting on a contractor site are: someone tapped to
 * call, someone tapped to text, someone completed a booking. Page views alone
 * can't tell Eric which pages actually produce work.
 *
 * Phone/text use a delegated listener so we don't have to touch 86 anchor tags
 * across the site. Booking listens for the 'nemo:booked' event that booking.js
 * dispatches only after the server confirms -- not on form submit, so failed
 * and double-booked attempts aren't counted as leads.
 */
(function () {
  'use strict';

  function track(name, params) {
    if (typeof window.gtag !== 'function') return; // blocked or not yet loaded
    window.gtag('event', name, params || {});
  }

  // --- first-party call beacon ------------------------------------------
  // GA4 is the wrong and only home for the most important number on the site.
  // gtag is blocked for a large share of visitors and, worse, GA4 has no
  // server-side export without a service-account key, so "did anyone actually
  // ring us?" was invisible to the growth engine and to Eric's dashboard.
  //
  // This pings our own server instead. nginx answers 204 and the line lands in
  // the same access log every other metric is already read from, so it inherits
  // the existing bot and owner filtering and needs no cookie, no third party
  // and no consent banner. It runs whether or not gtag ever loaded.
  function beacon() {
    try {
      var u = '/e/call-tap?p=' + encodeURIComponent(location.pathname);
      // sendBeacon survives the page being backgrounded when the dialer opens,
      // which is exactly when this fires on a phone.
      if (navigator.sendBeacon && navigator.sendBeacon(u)) return;
      new Image().src = u + '&t=' + Date.now(); // cache-buster for the GET path
    } catch (e) { /* never let measurement break the tap */ }
  }

  // --- phone + text taps -----------------------------------------------
  document.addEventListener('click', function (e) {
    var a = e.target && e.target.closest ? e.target.closest('a[href^="tel:"], a[href^="sms:"]') : null;
    if (!a) return;
    var href = a.getAttribute('href') || '';
    var isSms = href.indexOf('sms:') === 0;
    // Calls only. A text is a lead too, but mixing them would make the
    // dashboard's call-conversion rate mean two different things at once.
    if (!isSms) beacon();
    track(isSms ? 'contact_text' : 'contact_call', {
      // where on the site the tap happened, so we can see which pages drive calls
      page_path: location.pathname,
      link_url: href
    });
  }, true);

  // --- confirmed booking ------------------------------------------------
  document.addEventListener('nemo:booked', function (e) {
    var d = (e && e.detail) || {};
    track('generate_lead', {
      page_path: location.pathname,
      service: d.service || '',
      value: 0,
      currency: 'USD'
    });
  });
})();
