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

  // --- phone + text taps -----------------------------------------------
  document.addEventListener('click', function (e) {
    var a = e.target && e.target.closest ? e.target.closest('a[href^="tel:"], a[href^="sms:"]') : null;
    if (!a) return;
    var href = a.getAttribute('href') || '';
    var isSms = href.indexOf('sms:') === 0;
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
