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
const hasSource = db.prepare(`PRAGMA table_info(bookings)`).all().some((c) => c.name === 'source');
if (!hasSource) {
  db.exec(`ALTER TABLE bookings ADD COLUMN source TEXT NOT NULL DEFAULT 'web'`);
}

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
    INSERT INTO bookings (uid, service, name, email, phone, address, notes, start_utc, end_utc, status, source, created_at)
    VALUES (@uid, @service, @name, @email, @phone, @address, @notes, @start_utc, @end_utc, 'confirmed', @source, @created_at)
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

  insertLead: db.prepare(`
    INSERT INTO leads (uid, name, phone, address, service, availability, notes, caller_id, emailed, created_at)
    VALUES (@uid, @name, @phone, @address, @service, @availability, @notes, @caller_id, @emailed, @created_at)
  `),
  markLeadEmailed: db.prepare(`UPDATE leads SET emailed = 1 WHERE uid = ?`),
  recentLeads: db.prepare(`SELECT * FROM leads ORDER BY id DESC LIMIT 50`),
};

module.exports = { db, stmts };
