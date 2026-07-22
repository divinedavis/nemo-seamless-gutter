'use strict';
// Weather-aware availability.
//
// Eric installs and cleans gutters, so rain does not "affect" his schedule — it
// IS his schedule. Rather than ask him to keep a calendar up to date day by day,
// availability is computed at request time: business hours, minus bookings,
// minus any day the forecast rules out for that kind of work.
//
// Source: the US National Weather Service (api.weather.gov) — free, keyless,
// unmetered, and authoritative for York County. Two hops: /points/{lat},{lon}
// resolves to a forecast grid (stable forever, so it is cached hard), then
// /gridpoints/.../forecast/hourly returns ~156 hourly periods (≈6.5 days).
//
// Beyond that horizon there is no forecast, which is precisely why bookings are
// taken as tentative HOLDS and confirmed later (see jobs/confirm_run.js) rather
// than refused. A customer calling in October about next month must still be
// able to book something.
const { DateTime } = require('luxon');
const config = require('./config');
const { stmts } = require('./db');
const { safeFetchText } = require('./safeFetch');

const POINTS_URL = `https://api.weather.gov/points/${config.weather.lat},${config.weather.lon}`;

let gridUrl = null; // resolved once per process
let cache = { at: 0, days: null };

function ua() {
  return { 'User-Agent': config.weather.userAgent, Accept: 'application/geo+json' };
}

// "7 mph" and "5 to 10 mph" both appear; take the top of the range, since it is
// the gust-adjacent number that decides whether a ladder is safe.
function parseWindMph(s) {
  const nums = String(s || '').match(/\d+/g);
  if (!nums) return 0;
  return Math.max(...nums.map(Number));
}

async function resolveGridUrl() {
  if (gridUrl) return gridUrl;
  const body = await safeFetchText(POINTS_URL, { headers: ua(), timeoutMs: 10000 });
  const url = JSON.parse(body).properties.forecastHourly;
  if (!url) throw new Error('no forecastHourly in /points response');
  gridUrl = url;
  return gridUrl;
}

/**
 * Reduce the hourly forecast to one verdict per local calendar date, considering
 * only hours the crew would actually be working — an 11 PM thunderstorm is
 * irrelevant to an 8 AM job, and treating it as a washout would close a
 * perfectly good day.
 */
function summarizeByDay(periods) {
  const tz = config.timezone;
  const days = new Map();
  for (const p of periods) {
    const local = DateTime.fromISO(p.startTime).setZone(tz);
    const date = local.toFormat('yyyy-LL-dd');
    const hours = config.business.hours[local.weekday % 7];
    if (!hours) continue; // closed that weekday
    const h = local.hour + local.minute / 60;
    const [oh, om] = hours.open.split(':').map(Number);
    const [ch, cm] = hours.close.split(':').map(Number);
    if (h < oh + om / 60 || h >= ch + cm / 60) continue;

    const pop = (p.probabilityOfPrecipitation && p.probabilityOfPrecipitation.value) || 0;
    const wind = parseWindMph(p.windSpeed);
    const temp = typeof p.temperature === 'number' ? p.temperature : 60;

    const d = days.get(date) || { date, pop: 0, wind: 0, minTemp: 999, summary: '' };
    if (pop >= d.pop) {
      d.pop = pop;
      // Name the worst hour, not the first — "Chance Rain Showers" is what Eric
      // needs to see, not the "Sunny" that preceded it.
      if (p.shortForecast) d.summary = p.shortForecast;
    }
    d.wind = Math.max(d.wind, wind);
    d.minTemp = Math.min(d.minTemp, temp);
    days.set(date, d);
  }
  return [...days.values()].map((d) => ({ ...d, minTemp: d.minTemp === 999 ? null : d.minTemp }));
}

// Refresh the forecast into the DB cache. Safe to call often; obeys the TTL.
async function refresh(force = false) {
  if (!config.weather.enabled) return { skipped: 'disabled' };
  if (!force && Date.now() - cache.at < config.weather.cacheTtlSec * 1000) {
    return { cached: true, days: cache.days };
  }
  const url = await resolveGridUrl();
  const body = await safeFetchText(url, { headers: ua(), timeoutMs: 12000 });
  const periods = JSON.parse(body).properties.periods || [];
  const days = summarizeByDay(periods);
  const now = DateTime.utc().toISO();
  const write = require('./db').db.transaction(() => {
    for (const d of days) {
      stmts.upsertWeatherDay.run({
        date: d.date,
        pop: d.pop,
        wind: d.wind,
        min_temp: d.minTemp,
        summary: d.summary || '',
        fetched_at: now,
      });
    }
  });
  write();
  cache = { at: Date.now(), days };
  return { days, fetchedAt: now };
}

// Verdict for one service on one date. Never throws: if the forecast is missing
// (outside the horizon, or api.weather.gov is down) the answer is 'unknown',
// which stays bookable — refusing to book on a network error would cost Eric far
// more than a hold that gets moved later.
function verdictFor(serviceId, dateISO) {
  const svc = config.servicesById[serviceId];
  const sensitivity = (svc && svc.weather) || 'none';
  const base = { date: dateISO, service: serviceId, sensitivity, blocked: false, status: 'ok', reason: null };

  if (sensitivity === 'none' || !config.weather.enabled) return base;

  // Eric's own call always wins. The forecast is a good default, not a boss —
  // he can see the sky and we cannot.
  const ov = stmts.getWeatherOverride.get(dateISO);
  if (ov) {
    if (ov.decision === 'closed') {
      return { ...base, blocked: true, status: 'owner-closed', reason: ov.note || 'Eric has closed this day for outdoor work.' };
    }
    return { ...base, status: 'owner-open', reason: ov.note || 'Eric has confirmed this day is a go.' };
  }

  const row = stmts.getWeatherDay.get(dateISO);
  if (!row) return { ...base, status: 'unknown', reason: 'No forecast this far out yet.' };

  const w = config.weather;
  const popLimit = sensitivity === 'hard' ? w.hardPop : w.lightPop;
  const windLimit = sensitivity === 'hard' ? w.hardWindMph : w.lightWindMph;

  const detail = { pop: row.pop, wind: row.wind, minTemp: row.min_temp, summary: row.summary };
  if (row.pop >= popLimit) {
    return { ...base, ...detail, blocked: true, status: 'wet', reason: `${row.pop}% chance of rain${row.summary ? ` (${row.summary.toLowerCase()})` : ''}` };
  }
  if (row.wind >= windLimit) {
    return { ...base, ...detail, blocked: true, status: 'windy', reason: `winds up to ${row.wind} mph — not safe on a ladder` };
  }
  if (row.min_temp != null && row.min_temp <= w.minTempF) {
    return { ...base, ...detail, blocked: true, status: 'cold', reason: `${row.min_temp}°F — too cold to work safely` };
  }
  return { ...base, ...detail, status: 'ok' };
}

// Plain-language line for the owner digest / admin views.
function describeDay(dateISO) {
  const row = stmts.getWeatherDay.get(dateISO);
  const ov = stmts.getWeatherOverride.get(dateISO);
  const parts = [];
  if (row) {
    parts.push(`${row.pop}% rain`);
    if (row.wind) parts.push(`${row.wind} mph wind`);
    if (row.summary) parts.push(row.summary);
  } else {
    parts.push('no forecast yet');
  }
  if (ov) parts.push(`OVERRIDE: ${ov.decision}`);
  return parts.join(' · ');
}

function setOverride(dateISO, decision, note) {
  stmts.upsertWeatherOverride.run({
    date: dateISO,
    decision,
    note: note || null,
    set_at: DateTime.utc().toISO(),
  });
}

function clearOverride(dateISO) {
  stmts.deleteWeatherOverride.run(dateISO);
}

module.exports = { refresh, verdictFor, describeDay, setOverride, clearOverride, parseWindMph, summarizeByDay };
