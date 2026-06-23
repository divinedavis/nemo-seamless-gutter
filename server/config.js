'use strict';
// Central config, all overridable via environment variables (.env loaded in server.js).

function int(name, def) {
  const v = parseInt(process.env[name], 10);
  return Number.isFinite(v) ? v : def;
}
function str(name, def) {
  const v = process.env[name];
  return v && v.trim() ? v.trim() : def;
}
function list(name) {
  return str(name, '')
    .split(',')
    .map((s) => s.trim())
    .filter(Boolean);
}

const config = {
  port: int('PORT', 3009),
  timezone: str('TZ', 'America/New_York'),
  adminToken: str('ADMIN_TOKEN', ''),
  siteUrl: str('SITE_URL', 'https://nemoseamlessgutter.com'),

  business: {
    name: 'NEMO Seamless Gutter',
    phone: str('BUSINESS_PHONE', '(717) 891-6844'),
    // 0 = Sunday ... 6 = Saturday. Each day: open/close in 24h local time, or null = closed.
    // Gutter crew hours: Mon–Fri 7:30 AM–6 PM, Sat 8 AM–2 PM ET, closed Sunday.
    hours: {
      0: null,                              // Sun (closed)
      1: { open: '07:30', close: '18:00' }, // Mon
      2: { open: '07:30', close: '18:00' }, // Tue
      3: { open: '07:30', close: '18:00' }, // Wed
      4: { open: '07:30', close: '18:00' }, // Thu
      5: { open: '07:30', close: '18:00' }, // Fri
      6: { open: '08:00', close: '14:00' }, // Sat
    },
    leadTimeHours: int('LEAD_TIME_HOURS', 2), // earliest a customer can book from now (allows same-day)
    maxDaysAhead: int('MAX_DAYS_AHEAD', 45),
    slotStepMin: int('SLOT_STEP_MIN', 30), // grid the day is divided into
    bufferMin: int('BUFFER_MIN', 0), // default gap for external/unknown busy blocks
  },

  // bufferMin is per-service: on-site visits reserve travel time on each side;
  // phone consults need none (back-to-back calls are fine).
  // NOTE: 'consult' is the only phone service — every other service is on-site
  // and requires a job address (see server.js + booking.js).
  services: {
    estimate: { id: 'estimate', label: 'Free On-Site Estimate', durationMin: int('DUR_ESTIMATE_MIN', 60), bufferMin: int('BUFFER_ESTIMATE_MIN', 20) },
    cleaning: { id: 'cleaning', label: 'Gutter Cleaning / Repair', durationMin: int('DUR_CLEANING_MIN', 90), bufferMin: int('BUFFER_CLEANING_MIN', 20) },
    consult: { id: 'consult', label: 'Phone Consultation', durationMin: int('DUR_CONSULT_MIN', 20), bufferMin: int('BUFFER_CONSULT_MIN', 0) },
  },

  // Read-only ICS feed URLs for the owner's calendars (Google "secret iCal address",
  // iCloud published-calendar URL, etc.). Any event on these blocks site availability.
  icsFeeds: list('ICS_FEEDS'),
  busyCacheTtlSec: int('BUSY_CACHE_TTL_SEC', 300),

  // Email (used to send ICS invites + notifications). If unset, booking still works
  // and is stored, but no email is sent.
  smtp: {
    host: str('SMTP_HOST', ''),
    port: int('SMTP_PORT', 587),
    secure: str('SMTP_SECURE', 'false') === 'true',
    user: str('SMTP_USER', ''),
    pass: str('SMTP_PASS', ''),
  },
  fromEmail: str('FROM_EMAIL', ''),
  // Owner email address(es) — receive the calendar invite + new-booking alerts.
  // Comma-separated; first is the primary (calendar organizer/attendee).
  ownerEmails: list('OWNER_EMAIL').length
    ? list('OWNER_EMAIL')
    : ['enemo@nemoseamlessgutter.com'],
  ownerName: str('OWNER_NAME', 'NEMO Seamless Gutter'),

  // Optional iCloud CalDAV write-back (app-specific password) for instant insertion
  // into the owner's Apple Calendar without them accepting the email invite.
  icloud: {
    username: str('ICLOUD_USERNAME', ''),
    appPassword: str('ICLOUD_APP_PASSWORD', ''),
    calendarUrl: str('ICLOUD_CALENDAR_URL', ''), // specific calendar collection URL
  },
};

config.servicesById = config.services;
config.ownerEmail = config.ownerEmails[0]; // primary

module.exports = config;
