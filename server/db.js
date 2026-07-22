'use strict';
const path = require('path');
const Database = require('better-sqlite3');

const dbPath = process.env.DB_PATH || path.join(__dirname, 'bookings.sqlite');
const db = new Database(dbPath);
db.pragma('journal_mode = WAL');

db.exec(`
  CREATE TABLE IF NOT EXISTS bookings (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    uid         TEXT NOT NULL UNIQUE,
    service     TEXT NOT NULL,
    name        TEXT NOT NULL,
    email       TEXT,
    phone       TEXT NOT NULL,
    address     TEXT,
    notes       TEXT,
    start_utc   TEXT NOT NULL,
    end_utc     TEXT NOT NULL,
    status      TEXT NOT NULL DEFAULT 'confirmed',
    created_at  TEXT NOT NULL
  );
  CREATE INDEX IF NOT EXISTS idx_bookings_start ON bookings(start_utc);
`);

// Where the booking came from: 'web' (the site widget) or 'phone-ai' (the
// ElevenLabs phone assistant, proven by the agent token). Added after the table
// existed in production, so migrate in place rather than in the CREATE above.
// Columns added after the table existed in production, so migrate in place
// rather than in the CREATE above.
//
//  source     — 'web' (site widget) or 'phone-ai' (the ElevenLabs assistant).
//  hold_state — the weather story for this booking, orthogonal to `status`:
//               `status` says whether the slot is still OCCUPIED (confirmed /
//               cancelled), `hold_state` says how sure we are it will happen.
//                 'tentative'  — held, forecast not yet trustworthy
//                 'confirmed'  — re-checked close in and locked
//                 'rescheduled'— weather moved it at least once
//               A tentative booking still blocks its slot: the customer owns
//               that time, we just haven't promised the sky yet.
const cols = new Set(db.prepare(`PRAGMA table_info(bookings)`).all().map((c) => c.name));
const addColumn = (name, ddl) => {
  if (!cols.has(name)) db.exec(`ALTER TABLE bookings ADD COLUMN ${ddl}`);
};
addColumn('source', `source TEXT NOT NULL DEFAULT 'web'`);
addColumn('hold_state', `hold_state TEXT NOT NULL DEFAULT 'confirmed'`);
addColumn('confirmed_at', `confirmed_at TEXT`);
addColumn('reschedule_count', `reschedule_count INTEGER NOT NULL DEFAULT 0`);
addColumn('original_start_utc', `original_start_utc TEXT`);

// Cached NWS forecast, one row per local calendar date. A cache rather than a
// record: every refresh overwrites it.
db.exec(`
  CREATE TABLE IF NOT EXISTS weather_days (
    date       TEXT PRIMARY KEY,
    pop        INTEGER NOT NULL DEFAULT 0,
    wind       INTEGER NOT NULL DEFAULT 0,
    min_temp   INTEGER,
    summary    TEXT,
    fetched_at TEXT NOT NULL
  );
`);

// Eric's manual call on a given day, which beats the forecast in both
// directions — he can close a dry-looking day (ground still soaked from
// yesterday) or open a wet-looking one (the front is tracking south).
db.exec(`
  CREATE TABLE IF NOT EXISTS weather_overrides (
    date     TEXT PRIMARY KEY,
    decision TEXT NOT NULL,
    note     TEXT,
    set_at   TEXT NOT NULL
  );
`);

// What the automation did and why. When a customer says "nobody told me it
// moved", this is the answer — and it is the only way to debug a rule that
// fired at 4 AM.
db.exec(`
  CREATE TABLE IF NOT EXISTS booking_events (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    uid        TEXT NOT NULL,
    event      TEXT NOT NULL,
    detail     TEXT,
    created_at TEXT NOT NULL
  );
  CREATE INDEX IF NOT EXISTS idx_events_uid ON booking_events(uid);
`);

// Leads taken by the phone assistant. Eric has no fixed schedule, so the assistant
// does not touch a calendar — it takes a good message, emails him, and he calls the
// customer back to agree a time. This table is the record in case an email is lost.
db.exec(`
  CREATE TABLE IF NOT EXISTS leads (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    uid          TEXT NOT NULL UNIQUE,
    name         TEXT NOT NULL,
    phone        TEXT NOT NULL,
    address      TEXT,
    service      TEXT,
    availability TEXT,
    notes        TEXT,
    caller_id    TEXT,
    emailed      INTEGER NOT NULL DEFAULT 0,
    created_at   TEXT NOT NULL
  );
  CREATE INDEX IF NOT EXISTS idx_leads_created ON leads(created_at);
`);

const stmts = {
  insert: db.prepare(`
    INSERT INTO bookings (uid, service, name, email, phone, address, notes, start_utc, end_utc, status, source, hold_state, confirmed_at, created_at)
    VALUES (@uid, @service, @name, @email, @phone, @address, @notes, @start_utc, @end_utc, 'confirmed', @source, @hold_state, @confirmed_at, @created_at)
  `),
  // Active bookings that overlap a [start,end) window.
  overlapping: db.prepare(`
    SELECT * FROM bookings
    WHERE status = 'confirmed' AND start_utc < @end AND end_utc > @start
  `),
  inRange: db.prepare(`
    SELECT * FROM bookings
    WHERE status = 'confirmed' AND start_utc < @end AND end_utc > @start
    ORDER BY start_utc ASC
  `),
  upcoming: db.prepare(`
    SELECT * FROM bookings
    WHERE status = 'confirmed' AND end_utc >= @now
    ORDER BY start_utc ASC
  `),
  byUid: db.prepare(`SELECT * FROM bookings WHERE uid = ?`),
  cancel: db.prepare(`UPDATE bookings SET status = 'cancelled' WHERE uid = ?`),

  // --- weather-aware holds -------------------------------------------------
  // Bookings due inside the confirm horizon that we have not yet committed to.
  pendingHolds: db.prepare(`
    SELECT * FROM bookings
    WHERE status = 'confirmed' AND hold_state = 'tentative'
      AND start_utc > @now AND start_utc <= @until
    ORDER BY start_utc ASC
  `),
  markConfirmed: db.prepare(`
    UPDATE bookings SET hold_state = 'confirmed', confirmed_at = @at WHERE uid = @uid
  `),
  moveBooking: db.prepare(`
    UPDATE bookings
       SET start_utc = @start_utc,
           end_utc = @end_utc,
           reschedule_count = reschedule_count + 1,
           original_start_utc = COALESCE(original_start_utc, @previous_start)
     WHERE uid = @uid
  `),
  setHoldState: db.prepare(`UPDATE bookings SET hold_state = @state WHERE uid = @uid`),
  // Holds the automation gave up on — kept out of pendingHolds so a booking it
  // cannot solve is raised to Eric once, not re-raised every hour.
  escalatedHolds: db.prepare(`
    SELECT * FROM bookings
    WHERE status = 'confirmed' AND hold_state = 'escalated' AND start_utc > @now
    ORDER BY start_utc ASC
  `),
  logEvent: db.prepare(`
    INSERT INTO booking_events (uid, event, detail, created_at)
    VALUES (@uid, @event, @detail, @created_at)
  `),
  eventsForUid: db.prepare(`SELECT * FROM booking_events WHERE uid = ? ORDER BY id ASC`),

  upsertWeatherDay: db.prepare(`
    INSERT INTO weather_days (date, pop, wind, min_temp, summary, fetched_at)
    VALUES (@date, @pop, @wind, @min_temp, @summary, @fetched_at)
    ON CONFLICT(date) DO UPDATE SET
      pop = excluded.pop, wind = excluded.wind, min_temp = excluded.min_temp,
      summary = excluded.summary, fetched_at = excluded.fetched_at
  `),
  getWeatherDay: db.prepare(`SELECT * FROM weather_days WHERE date = ?`),
  upsertWeatherOverride: db.prepare(`
    INSERT INTO weather_overrides (date, decision, note, set_at)
    VALUES (@date, @decision, @note, @set_at)
    ON CONFLICT(date) DO UPDATE SET
      decision = excluded.decision, note = excluded.note, set_at = excluded.set_at
  `),
  getWeatherOverride: db.prepare(`SELECT * FROM weather_overrides WHERE date = ?`),
  deleteWeatherOverride: db.prepare(`DELETE FROM weather_overrides WHERE date = ?`),

  insertLead: db.prepare(`
    INSERT INTO leads (uid, name, phone, address, service, availability, notes, caller_id, emailed, created_at)
    VALUES (@uid, @name, @phone, @address, @service, @availability, @notes, @caller_id, @emailed, @created_at)
  `),
  markLeadEmailed: db.prepare(`UPDATE leads SET emailed = 1 WHERE uid = ?`),
  recentLeads: db.prepare(`SELECT * FROM leads ORDER BY id DESC LIMIT 50`),
};

module.exports = { db, stmts };
