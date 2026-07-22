'use strict';
// Load .env if present (no hard dependency on dotenv).
try {
  const fs = require('fs');
  const path = require('path');
  const envPath = path.join(__dirname, '.env');
  if (fs.existsSync(envPath)) {
    for (const line of fs.readFileSync(envPath, 'utf8').split('\n')) {
      const m = line.match(/^\s*([A-Z0-9_]+)\s*=\s*(.*)\s*$/);
      if (m && !process.env[m[1]]) {
        let v = m[2];
        if ((v.startsWith('"') && v.endsWith('"')) || (v.startsWith("'") && v.endsWith("'"))) v = v.slice(1, -1);
        process.env[m[1]] = v;
      }
    }
  }
} catch (_) {}

const crypto = require('crypto');
const express = require('express');
const { DateTime } = require('luxon');
const config = require('./config');
const { stmts } = require('./db');
const { generateSlots, validateBooking, serviceOrThrow } = require('./availability');
const calendar = require('./calendar');
const weather = require('./weather');
const scheduler = require('./scheduler');
const { runSetup, validateSetupToken } = require('./setup');

const app = express();
app.disable('x-powered-by');

// Escape user-controlled values before interpolating them into any HTML output,
// to prevent stored XSS (booking fields are accepted verbatim and rendered later).
function escapeHtml(s) {
  return String(s == null ? '' : s)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

// Baseline security response headers (no helmet dependency present; a small
// middleware keeps the footprint minimal).
app.use((_req, res, next) => {
  res.setHeader('Content-Security-Policy', "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'");
  res.setHeader('X-Frame-Options', 'DENY');
  res.setHeader('X-Content-Type-Options', 'nosniff');
  res.setHeader('Referrer-Policy', 'no-referrer');
  res.setHeader('Strict-Transport-Security', 'max-age=63072000; includeSubDomains');
  next();
});

app.use(express.json({ limit: '32kb' }));
app.use(express.urlencoded({ extended: false, limit: '32kb' }));

// --- tiny in-memory rate limiter for the booking endpoint ---
const hits = new Map();
function rateLimit(ip, max, windowMs) {
  const now = Date.now();
  const rec = hits.get(ip) || { count: 0, reset: now + windowMs };
  if (now > rec.reset) {
    rec.count = 0;
    rec.reset = now + windowMs;
  }
  rec.count += 1;
  hits.set(ip, rec);
  return rec.count <= max;
}

const { busyForDay } = scheduler;

// Keep the forecast warm without blocking a request on api.weather.gov. The
// cron refreshes it properly; this is just so a cold process isn't answering
// availability questions with no weather data at all.
function warmWeather() {
  weather.refresh().catch((err) => console.error('[weather] refresh failed:', err.message));
}

// --- routes ---
app.get('/api/health', (_req, res) => res.json({ ok: true, service: 'nemo-seamless-gutter-booking' }));

app.get('/api/services', (_req, res) => {
  // The phone assistant calls this first. Hand it the calendar already worked
  // out — "Thursday" -> 2026-07-24 is exactly the arithmetic an LLM gets subtly
  // wrong, and a booking on the wrong day is worse than no booking at all.
  const now = DateTime.now().setZone(config.timezone);
  const upcomingDays = [];
  for (let i = 0; i < 14; i += 1) {
    const d = now.plus({ days: i });
    const hours = config.business.hours[d.weekday % 7];
    upcomingDays.push({
      date: d.toFormat('yyyy-LL-dd'),
      weekday: d.toFormat('cccc'),
      open: Boolean(hours),
      hours: hours ? `${hours.open}–${hours.close}` : 'closed',
    });
  }

  res.json({
    timezone: config.timezone,
    today: now.toFormat('yyyy-LL-dd'),
    todayWeekday: now.toFormat('cccc'),
    localTime: now.toFormat('h:mm a'),
    leadTimeHours: config.business.leadTimeHours,
    maxDaysAhead: config.business.maxDaysAhead,
    services: Object.values(config.services).map((s) => ({
      id: s.id,
      label: s.label,
      durationMin: s.durationMin,
      requiresAddress: s.id !== 'consult',
      weatherSensitive: (s.weather || 'none') !== 'none',
      arrivalWindowMin: s.arrivalWindowMin || 0,
    })),
    upcomingDays,
  });
});

app.get('/api/availability', async (req, res) => {
  try {
    const { service, date } = req.query;
    serviceOrThrow(service);
    if (!/^\d{4}-\d{2}-\d{2}$/.test(date || '')) return res.status(400).json({ error: 'date must be YYYY-MM-DD' });
    const verdict = weather.verdictFor(service, date);
    const busy = await busyForDay(date);
    const slots = generateSlots(service, date, busy, Date.now(), { weather: verdict });
    res.json({
      date,
      service,
      timezone: config.timezone,
      slots,
      weather: { status: verdict.status, blocked: verdict.blocked, reason: verdict.reason, pop: verdict.pop == null ? null : verdict.pop, summary: verdict.summary || null },
    });
  } catch (err) {
    res.status(err.status || 500).json({ error: err.message });
  }
});

// The phone assistant's main question: "what can I offer this caller?"
//
// It returns a short list of ready-made sentences rather than a calendar, because
// the assistant must never do date arithmetic or read a grid — it reads back
// `spoken` verbatim and passes `start` to /api/book untouched.
app.get('/api/next-openings', async (req, res) => {
  // Each call can walk three weeks of days, and every day can touch the cached
  // calendar feeds — far heavier than /api/availability's single day. Public and
  // unmetered it would be a cheap way to pin the process, so it gets its own
  // bucket, with the phone assistant separated out (one storm-week shift really
  // can be dozens of legitimate calls).
  const fromAgent = Boolean(config.agentToken) && req.headers['x-agent-token'] === config.agentToken;
  const ip = (req.headers['x-forwarded-for'] || req.ip || '').split(',')[0].trim();
  if (!rateLimit(fromAgent ? 'openings-ai' : `openings-${ip}`, fromAgent ? 120 : 30, 10 * 60000)) {
    return res.status(429).json({ error: 'Too many requests, please try again later.' });
  }
  try {
    const service = String(req.query.service || '').trim();
    serviceOrThrow(service);
    const limit = Math.min(Math.max(parseInt(req.query.limit, 10) || 3, 1), 6);
    const { openings, skipped } = await scheduler.findOpenings(service, { limit });
    const svc = config.servicesById[service];

    res.json({
      service,
      serviceLabel: svc.label,
      timezone: config.timezone,
      openings,
      // Days the forecast ruled out. Worth saying out loud — "Wednesday's out,
      // they're calling for rain" is a reason a customer accepts, where a bare
      // "Wednesday is unavailable" invites an argument.
      weatherClosed: skipped,
      message: openings.length
        ? `Offer these ${openings.length} option(s), reading the "spoken" text exactly as written.`
        : `No openings in the next ${config.holds.rebookSearchDays} days. Take a message for Eric instead.`,
    });
  } catch (err) {
    res.status(err.status || 500).json({ error: err.message });
  }
});

app.post('/api/book', async (req, res) => {
  // Every call from the phone assistant arrives from ElevenLabs' egress IP, so it
  // would otherwise share one bucket with itself and lock out later callers.
  // Give it its own, roomier bucket — a busy storm week is a lot of calls.
  const fromAgent = Boolean(config.agentToken) && req.headers['x-agent-token'] === config.agentToken;
  const ip = (req.headers['x-forwarded-for'] || req.ip || '').split(',')[0].trim();
  const limitKey = fromAgent ? 'phone-ai' : ip;
  const limitMax = fromAgent ? 30 : 8;
  if (!rateLimit(limitKey, limitMax, 10 * 60000)) return res.status(429).json({ error: 'Too many requests, please try again later.' });

  try {
    const b = req.body || {};
    const name = String(b.name || '').trim();
    const phone = String(b.phone || '').trim();
    const email = String(b.email || '').trim();
    const address = String(b.address || '').trim();
    const notes = String(b.notes || '').trim().slice(0, 1000);
    const service = String(b.service || '').trim();
    const start = String(b.start || '').trim();

    const svc = serviceOrThrow(service);
    if (name.length < 2) return res.status(400).json({ error: 'Please enter your name.' });
    if (phone.replace(/\D/g, '').length < 10) return res.status(400).json({ error: 'Please enter a valid phone number.' });
    if (email && !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) return res.status(400).json({ error: 'Please enter a valid email.' });
    if (svc.id !== 'consult' && address.length < 5) return res.status(400).json({ error: 'Please enter the job address for your visit.' });

    const dateISO = DateTime.fromISO(start, { zone: 'utc' }).setZone(config.timezone).toFormat('yyyy-LL-dd');

    // Re-validate against freshest busy data and insert atomically.
    const booking = {
      uid: `${crypto.randomUUID()}@nemoseamlessgutter.com`,
      service,
      name,
      email: email || null,
      phone,
      address: address || null,
      notes: notes || null,
      start_utc: null,
      end_utc: null,
      // Trusted, not caller-supplied: the token is what makes the label mean
      // something, so a spoofed body field can't claim the assistant took it.
      source: fromAgent ? 'phone-ai' : 'web',
      // Set below, once we know how far out this is.
      hold_state: 'confirmed',
      confirmed_at: DateTime.utc().toISO(),
      created_at: DateTime.utc().toISO(),
    };

    const verdict = weather.verdictFor(service, dateISO);
    const busy = await busyForDay(dateISO);
    const v = validateBooking(service, start, busy, Date.now(), { weather: verdict });
    if (!v.ok) return res.status(409).json({ error: v.reason });
    booking.start_utc = DateTime.fromISO(start, { zone: 'utc' }).toISO();
    booking.end_utc = v.end;

    // Outdoor work booked beyond the forecast horizon is a HOLD, not a promise.
    // The slot is really reserved, but confirm_run.js re-checks the sky about a
    // day out and either confirms it or moves the customer automatically.
    if (scheduler.shouldHold(service, booking.start_utc)) {
      booking.hold_state = 'tentative';
      booking.confirmed_at = null;
    }

    // Final guard inside a transaction against a concurrent identical insert.
    const insertTxn = require('./db').db.transaction(() => {
      const conflict = stmts.overlapping.get({ start: booking.start_utc, end: booking.end_utc });
      if (conflict) {
        const e = new Error('That time was just booked');
        e.status = 409;
        throw e;
      }
      stmts.insert.run(booking);
    });
    insertTxn();
    scheduler.logEvent(booking.uid, 'booked', `${booking.hold_state} · ${booking.source} · ${v.spoken}`);

    // Side-effects (email invite + optional iCloud write). Don't fail the booking on these.
    let emailResult = { sent: false };
    try {
      emailResult = await calendar.sendBookingEmails(booking);
    } catch (err) {
      console.error('[book] email failed:', err.message);
    }
    calendar.icloudWriteback(booking).catch(() => {});

    const when = DateTime.fromISO(booking.start_utc, { zone: 'utc' }).setZone(config.timezone).toFormat("cccc, LLL d 'at' h:mm a");
    const tentative = booking.hold_state === 'tentative';
    res.json({
      ok: true,
      uid: booking.uid,
      when,
      service: svc.label,
      emailed: emailResult.sent,
      holdState: booking.hold_state,
      // The exact words to say. A tentative hold must be described honestly —
      // promising a fixed date for outdoor work three weeks out is how you get a
      // customer standing in the driveway in the rain.
      spoken: tentative
        ? `You're down for ${v.spoken}. Because that's outdoor work, we'll check the forecast the day before and call or email you if the weather makes us move it.`
        : `You're all set for ${v.spoken}.`,
    });
  } catch (err) {
    res.status(err.status || 500).json({ error: err.message || 'Booking failed' });
  }
});

// --- phone assistant leads ---
// Unlike /api/book (public, used by the site widget) this is agent-only: it exists
// solely to put mail in Eric's inbox, so leaving it open would be a spam cannon.
app.post('/api/lead', async (req, res) => {
  if (!config.agentToken || req.headers['x-agent-token'] !== config.agentToken) {
    return res.status(401).json({ error: 'unauthorized' });
  }
  if (!rateLimit('lead', 40, 10 * 60000)) {
    return res.status(429).json({ error: 'Too many requests, please try again later.' });
  }

  const b = req.body || {};
  const clip = (v, n) => String(v == null ? '' : v).trim().slice(0, n);
  const lead = {
    uid: crypto.randomUUID(),
    name: clip(b.name, 120),
    phone: clip(b.phone, 40),
    address: clip(b.address, 300) || null,
    service: clip(b.service, 120) || null,
    availability: clip(b.availability, 500) || null,
    notes: clip(b.notes, 1500) || null,
    caller_id: clip(b.caller_id, 40) || null,
    emailed: 0,
    created_at: DateTime.utc().toISO(),
  };

  // A callback number is the one thing a lead cannot exist without. Everything
  // else — including the name — is optional on purpose: rejecting a nameless lead
  // would only teach the assistant to invent a name to get past the check, and Eric
  // can ask for it in the first five seconds of the call he's about to make.
  if (lead.phone.replace(/\D/g, '').length < 10) {
    return res.status(400).json({ error: 'A valid 10-digit callback number is required.' });
  }
  // Leave a missing name empty rather than substituting a placeholder — the email
  // renders its own "not given" under the Name label, and a stored placeholder ends
  // up read aloud or printed as though it were the person's name.
  if (lead.name.length < 2) lead.name = '';

  // Store first: if the mail server is having a bad day the lead is still not lost,
  // and `emailed` shows which ones need chasing.
  stmts.insertLead.run(lead);

  let sent = false;
  try {
    sent = (await calendar.sendLeadEmail(lead)).sent;
    if (sent) stmts.markLeadEmailed.run(lead.uid);
  } catch (err) {
    console.error('[lead] email failed:', err.message);
  }

  // Tell the agent plainly whether Eric was actually notified, so it can only
  // promise a callback when the message really went out. The wording is read
  // aloud, so address the caller directly rather than by a name we may not have —
  // "tell Name not given that Eric will call" is exactly the sort of thing an
  // assistant will happily say down the phone.
  res.json({
    ok: true,
    emailed: sent,
    message: sent
      ? `Message delivered to Eric. Tell the caller Eric will ring them back on ${lead.phone} to sort out a time.`
      : `Saved, but the email did NOT go out — do not promise a callback. Tell the caller to reach Eric directly on ${config.business.phone}.`,
  });
});

// --- admin (token-protected) ---
function requireAdmin(req, res) {
  const token = req.query.token || req.headers['x-admin-token'];
  if (!config.adminToken || token !== config.adminToken) {
    res.status(401).json({ error: 'unauthorized' });
    return false;
  }
  return true;
}

app.get('/api/admin/leads', (req, res) => {
  if (!requireAdmin(req, res)) return;
  const rows = stmts.recentLeads.all();
  res.json({ count: rows.length, leads: rows });
});

app.get('/api/admin/bookings', (req, res) => {
  if (!requireAdmin(req, res)) return;
  const rows = stmts.upcoming.all({ now: DateTime.utc().toISO() });
  res.json({
    count: rows.length,
    bookings: rows.map((r) => ({
      ...r,
      when_local: DateTime.fromISO(r.start_utc, { zone: 'utc' }).setZone(config.timezone).toFormat("ccc LLL d, h:mm a"),
    })),
  });
});

app.post('/api/admin/cancel', (req, res) => {
  if (!requireAdmin(req, res)) return;
  const uid = String((req.body && req.body.uid) || req.query.uid || '');
  const existing = stmts.byUid.get(uid);
  if (!existing) return res.status(404).json({ error: 'not found' });
  stmts.cancel.run(uid);
  res.json({ ok: true, uid });
});

// --- Owner booking management (signed, tokenless link from his alert email) ---
function manageHtml(title, body) {
  return `<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex"><title>${escapeHtml(title)} — ${escapeHtml(config.business.name)}</title>
  <style>body{font-family:-apple-system,Segoe UI,Roboto,sans-serif;background:#f6f8fc;color:#10182a;margin:0;padding:40px 20px}
  .card{max-width:520px;margin:0 auto;background:#fff;border:1px solid #e6ebf3;border-radius:18px;box-shadow:0 18px 50px -20px rgba(36,60,148,.28);padding:32px}
  h1{font-size:1.4rem;margin:0 0 14px;color:#243C94}.row{margin:6px 0;color:#5a6678}.row b{color:#10182a}
  .btn{display:inline-block;margin-top:18px;padding:13px 24px;border-radius:999px;border:0;font-weight:700;font-size:1rem;cursor:pointer}
  .danger{background:#e0463a;color:#fff}.muted{color:#5a6678;font-size:.9rem;margin-top:16px}a{color:#243C94}
  .pick{background:#F16C27;color:#fff;width:100%;margin-top:0;text-align:left}</style></head>
  <body><div class="card">${body}</div></body></html>`;
}

app.get('/booking/manage', (req, res) => {
  const uid = String(req.query.uid || '');
  const sig = String(req.query.sig || '');
  if (!calendar.verifyManageSig(uid, sig)) return res.status(403).send(manageHtml('Invalid link', '<h1>This link is invalid.</h1><p class="muted">Please use the link from your booking email.</p>'));
  const b = stmts.byUid.get(uid);
  if (!b) return res.status(404).send(manageHtml('Not found', '<h1>Booking not found.</h1>'));
  const svc = config.servicesById[b.service];
  const when = DateTime.fromISO(b.start_utc, { zone: 'utc' }).setZone(config.timezone).toFormat("cccc, LLL d 'at' h:mm a");
  if (b.status !== 'confirmed') {
    return res.send(manageHtml('Already cancelled', `<h1>This booking is already cancelled.</h1><div class="row"><b>${escapeHtml(b.name)}</b> — ${svc ? escapeHtml(svc.label) : ''} on ${escapeHtml(when)}</div>`));
  }
  res.send(
    manageHtml(
      'Manage booking',
      `<h1>Cancel this appointment?</h1>
       <div class="row"><b>${svc ? escapeHtml(svc.label) : 'Appointment'}</b></div>
       <div class="row">${escapeHtml(when)} (ET)</div>
       <div class="row">${escapeHtml(b.name)} · ${escapeHtml(b.phone)}${b.email ? ' · ' + escapeHtml(b.email) : ''}</div>
       ${b.address ? `<div class="row">${escapeHtml(b.address)}</div>` : ''}
       <form method="POST" action="/booking/cancel">
         <input type="hidden" name="uid" value="${escapeHtml(uid)}"><input type="hidden" name="sig" value="${escapeHtml(sig)}">
         <button class="btn danger" type="submit">Cancel &amp; notify the customer</button>
       </form>
       <p class="muted">The customer${b.email ? ' will be emailed' : ' has no email on file — please call them at ' + escapeHtml(b.phone)}, and this time will reopen on the site.</p>`
    )
  );
});

app.post('/booking/cancel', async (req, res) => {
  const uid = String((req.body && req.body.uid) || '');
  const sig = String((req.body && req.body.sig) || '');
  if (!calendar.verifyManageSig(uid, sig)) return res.status(403).send(manageHtml('Invalid link', '<h1>This link is invalid.</h1>'));
  const b = stmts.byUid.get(uid);
  if (!b) return res.status(404).send(manageHtml('Not found', '<h1>Booking not found.</h1>'));
  if (b.status === 'confirmed') {
    stmts.cancel.run(uid);
    calendar.invalidateBusyCache();
    calendar.sendCancellationEmail(b).catch((e) => console.error('[cancel] customer email failed:', e.message));
  }
  res.send(
    manageHtml(
      'Cancelled',
      `<h1>Done — booking cancelled.</h1>
       <p class="row">${b.email ? 'The customer has been emailed and asked to rebook.' : 'No email was on file — please call ' + escapeHtml(b.phone) + ' to let them know.'}</p>
       <p class="muted">That time is now open again on the site.</p>`
    )
  );
});

/* ---------------------------------------------------------------------------
 * Customer self-reschedule. Reached from the "we had to move you" email, so it
 * must work in one tap on a phone: the alternatives are already listed, tapping
 * one is the whole interaction. No login, no app, no phone tag.
 * ------------------------------------------------------------------------- */
app.get('/booking/reschedule', async (req, res) => {
  const uid = String(req.query.uid || '');
  const sig = String(req.query.sig || '');
  if (!calendar.verifyManageSig(uid, sig)) {
    return res.status(403).send(manageHtml('Invalid link', '<h1>This link is invalid.</h1><p class="muted">Please use the link from your email.</p>'));
  }
  const b = stmts.byUid.get(uid);
  if (!b) return res.status(404).send(manageHtml('Not found', '<h1>Booking not found.</h1>'));
  const svc = config.servicesById[b.service];
  const current = DateTime.fromISO(b.start_utc, { zone: 'utc' }).setZone(config.timezone);

  const { openings, skipped } = await scheduler.findOpenings(b.service, { limit: 6, perDay: 2, excludeUid: uid, excludeStart: b.start_utc });
  const buttons = openings
    .map(
      (o) => `<form method="POST" action="/booking/reschedule" style="margin:8px 0">
        <input type="hidden" name="uid" value="${escapeHtml(uid)}"><input type="hidden" name="sig" value="${escapeHtml(sig)}">
        <input type="hidden" name="start" value="${escapeHtml(o.start)}">
        <button class="btn pick" type="submit">${escapeHtml(o.weekday)}, ${escapeHtml(o.date)} · ${escapeHtml(o.label)}</button>
      </form>`
    )
    .join('');

  res.send(
    manageHtml(
      'Reschedule',
      `<h1>Pick a new time</h1>
       <div class="row"><b>${svc ? escapeHtml(svc.label) : 'Appointment'}</b></div>
       <div class="row">Currently: ${escapeHtml(current.toFormat("cccc, LLL d 'at' h:mm a"))} (ET)</div>
       ${b.status !== 'confirmed' ? '<p class="muted">This booking was cancelled — picking a time below will rebook it.</p>' : ''}
       ${openings.length ? buttons : '<p class="row">No open times in the next few weeks. Please call (717) 578-0073.</p>'}
       ${skipped.length ? `<p class="muted">Skipped for weather: ${escapeHtml(skipped.map((s) => `${s.weekday} (${s.reason})`).join(', '))}</p>` : ''}
       <p class="muted">Prefer to talk it through? Call or text (717) 578-0073.</p>`
    )
  );
});

app.post('/booking/reschedule', async (req, res) => {
  const uid = String((req.body && req.body.uid) || '');
  const sig = String((req.body && req.body.sig) || '');
  const start = String((req.body && req.body.start) || '');
  if (!calendar.verifyManageSig(uid, sig)) return res.status(403).send(manageHtml('Invalid link', '<h1>This link is invalid.</h1>'));
  const b = stmts.byUid.get(uid);
  if (!b) return res.status(404).send(manageHtml('Not found', '<h1>Booking not found.</h1>'));

  try {
    const dateISO = DateTime.fromISO(start, { zone: 'utc' }).setZone(config.timezone).toFormat('yyyy-LL-dd');
    const verdict = weather.verdictFor(b.service, dateISO);
    const busy = await busyForDay(dateISO, uid);
    const v = validateBooking(b.service, start, busy, Date.now(), { weather: verdict });
    if (!v.ok) {
      return res.status(409).send(manageHtml('Just taken', `<h1>Sorry — that time just went.</h1><p class="row">${escapeHtml(v.reason)}</p><p class="muted"><a href="/booking/reschedule?uid=${encodeURIComponent(uid)}&sig=${encodeURIComponent(sig)}">Pick another time</a></p>`));
    }
    const moved = await scheduler.applyMove(b, start, v, 'customer-reschedule');
    return res.send(
      manageHtml(
        'Rescheduled',
        `<h1>Done — you're rebooked.</h1>
         <div class="row"><b>${escapeHtml(moved.spoken)}</b></div>
         <p class="muted">A confirmation is on its way${b.email ? '' : ' — we have no email on file, so we will call you'}. Need to change it again? Call (717) 578-0073.</p>`
      )
    );
  } catch (err) {
    console.error('[reschedule] failed:', err.message);
    return res.status(500).send(manageHtml('Something went wrong', '<h1>Something went wrong.</h1><p class="muted">Please call (717) 578-0073.</p>'));
  }
});

/* ---------------------------------------------------------------------------
 * Owner day control. Eric gets one link in his morning email; the forecast is a
 * good default, but the man standing in the yard gets the last word — the
 * ground can still be soaked under a clear sky, and a front can track south.
 * ------------------------------------------------------------------------- */
const OWNER_SCHEDULE_KEY = calendar.OWNER_SCHEDULE_KEY;

app.get('/owner/schedule', (req, res) => {
  if (!calendar.verifyManageSig(OWNER_SCHEDULE_KEY, String(req.query.sig || ''))) {
    return res.status(403).send(manageHtml('Invalid link', '<h1>This link is invalid.</h1>'));
  }
  const tz = config.timezone;
  const today = DateTime.now().setZone(tz).startOf('day');
  const rows = [];
  for (let i = 0; i < 10; i += 1) {
    const d = today.plus({ days: i });
    const dateISO = d.toFormat('yyyy-LL-dd');
    if (!config.business.hours[d.weekday % 7]) continue;
    const jobs = stmts.inRange.all({
      start: d.toUTC().toISO(),
      end: d.plus({ days: 1 }).toUTC().toISO(),
    });
    const ov = stmts.getWeatherOverride.get(dateISO);
    const verdict = weather.verdictFor('cleaning', dateISO);
    const state = ov ? ov.decision : verdict.blocked ? 'auto-closed' : 'open';
    const badge = state === 'closed' || state === 'auto-closed' ? '#e0463a' : '#1a8a4a';
    rows.push(`
      <div class="day">
        <div class="dayhead"><b>${escapeHtml(d.toFormat('cccc, LLL d'))}</b>
          <span class="pill" style="background:${badge}">${escapeHtml(state)}</span></div>
        <div class="row">${escapeHtml(weather.describeDay(dateISO))}</div>
        <div class="row">${jobs.length} job${jobs.length === 1 ? '' : 's'}${jobs.length ? ': ' + escapeHtml(jobs.map((j) => j.name).join(', ')) : ''}</div>
        <form method="POST" action="/owner/schedule" class="acts">
          <input type="hidden" name="sig" value="${escapeHtml(String(req.query.sig || ''))}">
          <input type="hidden" name="date" value="${escapeHtml(dateISO)}">
          <button class="mini danger" name="decision" value="closed">Call it off</button>
          <button class="mini go" name="decision" value="open">We're working</button>
          <button class="mini plain" name="decision" value="auto">Use forecast</button>
        </form>
      </div>`);
  }
  res.send(
    manageHtml(
      'Your schedule',
      `<h1>Next 10 working days</h1>
       <p class="muted">The forecast decides by default. Override any day here — closing a day moves its jobs and emails those customers automatically tonight.</p>
       <style>.day{border-top:1px solid #e6ebf3;padding:14px 0}.dayhead{display:flex;justify-content:space-between;align-items:center}
       .pill{color:#fff;border-radius:999px;padding:3px 10px;font-size:.72rem;font-weight:700;text-transform:uppercase}
       .acts{display:flex;gap:8px;margin-top:10px;flex-wrap:wrap}
       .mini{border:0;border-radius:999px;padding:8px 14px;font-weight:700;font-size:.82rem;cursor:pointer}
       .go{background:#1a8a4a;color:#fff}.plain{background:#eef1f7;color:#10182a}</style>
       ${rows.join('')}`
    )
  );
});

app.post('/owner/schedule', (req, res) => {
  const sig = String((req.body && req.body.sig) || '');
  if (!calendar.verifyManageSig(OWNER_SCHEDULE_KEY, sig)) {
    return res.status(403).send(manageHtml('Invalid link', '<h1>This link is invalid.</h1>'));
  }
  const date = String((req.body && req.body.date) || '');
  const decision = String((req.body && req.body.decision) || '');
  if (!/^\d{4}-\d{2}-\d{2}$/.test(date)) return res.status(400).send(manageHtml('Bad request', '<h1>Bad date.</h1>'));

  if (decision === 'auto') weather.clearOverride(date);
  else if (decision === 'open' || decision === 'closed') weather.setOverride(date, decision, 'Set by Eric');
  else return res.status(400).send(manageHtml('Bad request', '<h1>Unknown action.</h1>'));

  res.redirect(303, `/owner/schedule?sig=${encodeURIComponent(sig)}`);
});

// --- one-time setup link (owner connects their calendars/email) ---
app.post('/api/setup', async (req, res) => {
  // The setup token gates credential overwrite, so it is required ON the
  // credential-write request itself and is accepted ONLY from a header or the
  // POST body — never from req.query, so it can't leak via access logs, the
  // Referer header, or browser history. It is short-TTL + single-use (see
  // setup.js): it expires and is burned from .env after the first successful
  // connect, so the link can't be replayed.
  const p = req.body || {};
  const t = req.headers['x-setup-token'] || p.setupToken || p.t;
  const gate = validateSetupToken(t);
  if (!gate.ok) {
    return res.status(401).json({ error: 'This setup link is invalid, expired, or has already been used. Ask for a fresh one.' });
  }
  const hasEmail = p.gmailUser && p.gmailAppPassword;
  const hasGoogle = p.googleIcsUrl;
  const hasApple = p.appleId && p.appleAppPassword;
  if (!hasEmail && !hasGoogle && !hasApple) {
    return res.status(400).json({ error: 'Please fill in at least one section before submitting.' });
  }
  // Re-validate immediately before the credential-changing action so a token
  // that expired between the gate check and the write can't slip through.
  if (!validateSetupToken(t).ok) {
    return res.status(401).json({ error: 'This setup link is invalid, expired, or has already been used. Ask for a fresh one.' });
  }
  try {
    const result = await runSetup(p);
    res.json({ ok: true, checks: result.checks, connected: result.changed });
    // Only restart if something actually connected — then the new .env (SMTP +
    // feeds + iCloud) is picked up and the single-use SETUP_TOKEN is cleared.
    // A fully-failed attempt changes nothing and keeps the link alive for retry.
    if (result.changed) {
      calendar.invalidateBusyCache();
      setTimeout(() => process.exit(0), 800);
    }
  } catch (err) {
    res.status(500).json({ error: err.message || 'Setup failed' });
  }
});

app.listen(config.port, '127.0.0.1', () => {
  console.log(`[nemo-seamless-gutter-booking] listening on 127.0.0.1:${config.port} (tz ${config.timezone})`);
  console.log(`  feeds: ${config.icsFeeds.length} | smtp: ${config.smtp.host ? 'on' : 'off'} | icloud: ${config.icloud.username ? 'on' : 'off'}`);
  console.log(`  weather: ${config.weather.enabled ? `on (${config.weather.lat},${config.weather.lon})` : 'off'} | holds confirm at T-${config.holds.confirmLeadHours}h`);
  if (config.weather.enabled) warmWeather();
});
