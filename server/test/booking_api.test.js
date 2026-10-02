'use strict';
// Booking API smoke test: boots the real server.js against a throwaway SQLite
// file and drives /api/health, /api/services, /api/availability and /api/book.
//
//   node --test server/test/        (or scripts/test.sh for everything)
//
// SAFE BY CONSTRUCTION — this can never email anyone or touch real bookings:
//   - DB_PATH points at a temp file, deleted afterwards;
//   - SMTP_HOST / ICS_FEEDS / ICLOUD_* / AGENT_TOKEN are set to a single
//     space. server.js only lets server/.env fill a variable that is unset or
//     empty, and config.js trims " " to "" — so even on a checkout that has a
//     real server/.env, SMTP stays off and no calendar is read or written;
//   - WEATHER_ENABLED=false, so nothing calls api.weather.gov.
// The one booking it makes lands in the temp DB and returns emailed:false.

const { test, before, after } = require('node:test');
const assert = require('node:assert');
const { spawn } = require('node:child_process');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const net = require('node:net');

const SERVER = path.join(__dirname, '..', 'server.js');
const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'nemo-api-test-'));
const DB = path.join(tmp, 'bookings.sqlite');
let proc;
let base;
let ipSeq = 0;

function freePort() {
  return new Promise((resolve, reject) => {
    const s = net.createServer();
    s.listen(0, '127.0.0.1', () => {
      const { port } = s.address();
      s.close(() => resolve(port));
    });
    s.on('error', reject);
  });
}

// Each request gets its own client address: the API rate-limits /api/book to
// 4 per 10 minutes per IP, and with `trust proxy loopback` it reads the
// address from X-Forwarded-For exactly as it does behind nginx.
function fakeIp() {
  ipSeq += 1;
  return `203.0.113.${ipSeq}`;
}

async function api(method, p, body, ip = fakeIp()) {
  const res = await fetch(base + p, {
    method,
    headers: { 'content-type': 'application/json', 'x-forwarded-for': ip },
    body: body ? JSON.stringify(body) : undefined,
  });
  let json = null;
  try { json = await res.json(); } catch (_) {}
  return { status: res.status, json };
}

// The first weekday at least 3 days out, so lead time and today's hours never
// make the day empty, and it is inside MAX_DAYS_AHEAD.
function openWeekday() {
  const d = new Date();
  d.setDate(d.getDate() + 3);
  while (d.getDay() === 0 || d.getDay() === 6) d.setDate(d.getDate() + 1);
  const pad = (n) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

before(async () => {
  const port = await freePort();
  base = `http://127.0.0.1:${port}`;
  const blank = ' ';
  proc = spawn(process.execPath, [SERVER], {
    env: {
      ...process.env,
      PORT: String(port),
      DB_PATH: DB,
      ADMIN_TOKEN: 'test-admin-token',
      AGENT_TOKEN: blank,
      SMTP_HOST: blank,
      SMTP_USER: blank,
      SMTP_PASS: blank,
      OWNER_EMAIL: 'owner@example.invalid',
      LEAD_EMAIL: 'owner@example.invalid',
      ICS_FEEDS: blank,
      ICLOUD_USERNAME: blank,
      ICLOUD_APP_PASSWORD: blank,
      ICLOUD_CALENDAR_URL: blank,
      SETUP_TOKEN: blank,
      WEATHER_ENABLED: 'false',
      TZ: 'America/New_York',
    },
    stdio: ['ignore', 'pipe', 'pipe'],
  });
  let log = '';
  proc.stdout.on('data', (b) => { log += b; });
  proc.stderr.on('data', (b) => { log += b; });
  const deadline = Date.now() + 10000;
  for (;;) {
    try {
      const r = await fetch(base + '/api/health');
      if (r.ok) break;
    } catch (_) {}
    if (Date.now() > deadline || proc.exitCode !== null) throw new Error('server did not start:\n' + log);
    await new Promise((r) => setTimeout(r, 100));
  }
  assert.match(log, /smtp: off/, 'SMTP must be off in tests:\n' + log);
  assert.match(log, /feeds: 0/, 'no calendar feeds in tests:\n' + log);
});

after(() => {
  if (proc) proc.kill();
  fs.rmSync(tmp, { recursive: true, force: true });
});

test('health responds', async () => {
  const r = await api('GET', '/api/health');
  assert.strictEqual(r.status, 200);
  assert.strictEqual(r.json.ok, true);
});

test('services lists the three bookable services', async () => {
  const r = await api('GET', '/api/services');
  assert.strictEqual(r.status, 200);
  const ids = r.json.services.map((s) => s.id).sort();
  assert.deepStrictEqual(ids, ['cleaning', 'consult', 'estimate']);
});

test('availability offers slots on an open weekday', async () => {
  const r = await api('GET', `/api/availability?service=estimate&date=${openWeekday()}`);
  assert.strictEqual(r.status, 200);
  assert.ok(Array.isArray(r.json.slots) && r.json.slots.length > 0, JSON.stringify(r.json));
});

test('availability rejects an unknown service', async () => {
  const r = await api('GET', `/api/availability?service=nope&date=${openWeekday()}`);
  assert.ok(r.status >= 400 && r.status < 500, String(r.status));
});

test('book validates every required field before storing anything', async () => {
  const good = { service: 'estimate', name: 'Test Person', phone: '717-555-0100', address: '1 Test St, York PA', start: '' };
  const cases = [
    [{ ...good, name: '' }, /name/i],
    [{ ...good, name: 'see https://spam.example' }, /just your name/i],
    [{ ...good, phone: '123' }, /phone/i],
    [{ ...good, email: 'not-an-email' }, /email/i],
    [{ ...good, address: '' }, /address/i],
    [{ ...good, service: 'nope' }, /./],
  ];
  for (const [body, msg] of cases) {
    const r = await api('POST', '/api/book', body);
    assert.ok(r.status >= 400 && r.status < 500, `${JSON.stringify(body)} -> ${r.status}`);
    assert.match(r.json.error, msg);
  }
});

test('book refuses a time that is not an open slot', async () => {
  const r = await api('POST', '/api/book', {
    service: 'consult', name: 'Test Person', phone: '717-555-0100', start: '2020-01-06T15:00:00.000Z',
  });
  assert.ok(r.status >= 400 && r.status < 500, String(r.status));
  assert.match(r.json.error, /available|booked/i);
});

test('a valid booking is stored once, emails nobody, and takes the slot', async () => {
  const day = openWeekday();
  const before = await api('GET', `/api/availability?service=estimate&date=${day}`);
  const slot = before.json.slots[0];
  const r = await api('POST', '/api/book', {
    service: 'estimate', name: 'Test Person', phone: '717-555-0100',
    address: '1 Test St, York PA', start: slot.start,
  });
  assert.strictEqual(r.status, 200, JSON.stringify(r.json));
  assert.strictEqual(r.json.emailed, false);

  const again = await api('POST', '/api/book', {
    service: 'estimate', name: 'Other Person', phone: '717-555-0101',
    address: '2 Test St, York PA', start: slot.start,
  });
  assert.ok(again.status >= 400, 'double booking must be refused');

  const afterAv = await api('GET', `/api/availability?service=estimate&date=${day}`);
  assert.ok(!afterAv.json.slots.some((s) => s.start === slot.start), 'booked slot still offered');

  const Database = require('better-sqlite3');
  const db = new Database(DB, { readonly: true });
  const n = db.prepare('SELECT COUNT(*) AS n FROM bookings').get().n;
  db.close();
  assert.strictEqual(n, 1);
});

test('book is rate-limited per client address', async () => {
  const ip = fakeIp();
  const codes = [];
  for (let i = 0; i < 5; i++) codes.push((await api('POST', '/api/book', { service: 'estimate' }, ip)).status);
  assert.deepStrictEqual(codes.slice(0, 4).every((c) => c === 400), true, codes.join(','));
  assert.strictEqual(codes[4], 429);
});

test('admin endpoints refuse a missing or wrong token', async () => {
  assert.strictEqual((await api('GET', '/api/admin/bookings')).status, 401);
  const r = await fetch(base + '/api/admin/bookings', { headers: { 'x-admin-token': 'wrong' } });
  assert.strictEqual(r.status, 401);
});
