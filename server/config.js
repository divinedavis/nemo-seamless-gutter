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
  // Shared secret the ElevenLabs phone assistant sends as `x-agent-token`. It does
  // not gate access — /api/book is public because the site widget uses it — it
  // proves provenance, so a booking labelled "taken by the phone assistant" in
  // Eric's inbox actually was. Unset = the phone assistant is simply not wired up.
  agentToken: str('AGENT_TOKEN', ''),
  siteUrl: str('SITE_URL', 'https://nemoseamlessgutter.com'),

  business: {
    name: 'NEMO Seamless Gutter',
    phone: str('BUSINESS_PHONE', '(717) 578-0073'),
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
  //
  // weather: how much a wet/windy day matters to this service (see weather.js).
  //   'none'  — happens regardless (phone call)
  //   'light' — outdoor but brief; only a real downpour stops it
  //   'hard'  — ladder work; called off well before it actually rains
  // arrivalWindowMin: customers are given an ARRIVAL WINDOW, not a to-the-minute
  //   time. A gutter crew that hits a hidden rotted fascia runs 90 minutes late
  //   and every later "9:15" becomes a broken promise; a 2-hour window absorbs
  //   that. 0 = quote the exact time (a phone call really does start on time).
  services: {
    estimate: {
      id: 'estimate',
      label: 'Free On-Site Estimate',
      durationMin: int('DUR_ESTIMATE_MIN', 60),
      bufferMin: int('BUFFER_ESTIMATE_MIN', 20),
      weather: str('WEATHER_ESTIMATE', 'light'),
      arrivalWindowMin: int('WINDOW_ESTIMATE_MIN', 120),
    },
    cleaning: {
      id: 'cleaning',
      label: 'Gutter Cleaning / Repair',
      durationMin: int('DUR_CLEANING_MIN', 90),
      bufferMin: int('BUFFER_CLEANING_MIN', 20),
      weather: str('WEATHER_CLEANING', 'hard'),
      arrivalWindowMin: int('WINDOW_CLEANING_MIN', 180),
    },
    consult: {
      id: 'consult',
      label: 'Phone Consultation',
      durationMin: int('DUR_CONSULT_MIN', 20),
      bufferMin: int('BUFFER_CONSULT_MIN', 0),
      weather: str('WEATHER_CONSULT', 'none'),
      arrivalWindowMin: int('WINDOW_CONSULT_MIN', 0),
    },
  },

  // --- weather-aware scheduling ---------------------------------------------
  // Eric's day is decided by the sky, so availability is COMPUTED at request time
  // (capacity − bookings − forecast) instead of read out of a fixed calendar.
  // Source is the US National Weather Service: free, no key, no quota.
  weather: {
    enabled: str('WEATHER_ENABLED', 'true') === 'true',
    lat: str('WEATHER_LAT', '39.9626'), // York, PA
    lon: str('WEATHER_LON', '-76.7277'),
    // NWS asks that every caller identify itself with a contact address.
    userAgent: str('WEATHER_UA', 'nemo-seamless-gutter/1.0 (enemo@nemoseamlessgutter.com)'),
    cacheTtlSec: int('WEATHER_CACHE_TTL_SEC', 1800),
    // Precipitation probability (%) at or above which the day is called off.
    // 'hard' work stops well below certainty — nobody puts a ladder up on a
    // coin-flip morning — while 'light' work only stops for a real soaking.
    hardPop: int('WEATHER_HARD_POP', 50),
    lightPop: int('WEATHER_LIGHT_POP', 75),
    hardWindMph: int('WEATHER_HARD_WIND', 25),
    lightWindMph: int('WEATHER_LIGHT_WIND', 32),
    minTempF: int('WEATHER_MIN_TEMP_F', 20),
  },

  // The hold → confirm loop. A slot booked for next Thursday is a forecast, not a
  // fact, so weather-sensitive bookings are held TENTATIVE and re-checked as the
  // day approaches; only then does the customer get "you're confirmed".
  holds: {
    // Inside this horizon the forecast is trustworthy enough to commit.
    confirmLeadHours: int('CONFIRM_LEAD_HOURS', 30),
    // How far ahead to look for a replacement slot when weather kills one.
    rebookSearchDays: int('REBOOK_SEARCH_DAYS', 21),
    // How many auto-moves before we stop shuffling and have Eric phone them.
    maxAutoReschedules: int('MAX_AUTO_RESCHEDULES', 2),
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
    : ['eric@nemoseamlessgutter.com'],
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
