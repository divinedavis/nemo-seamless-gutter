'use strict';
const { DateTime } = require('luxon');
const config = require('./config');

// luxon weekday: 1=Mon..7=Sun  ->  config.hours key: 0=Sun..6=Sat
function hoursForWeekday(luxonWeekday) {
  const key = luxonWeekday % 7; // 7(Sun)->0, 1(Mon)->1 ... 6(Sat)->6
  return config.business.hours[key] || null;
}

function hmToMinutes(hm) {
  const [h, m] = hm.split(':').map(Number);
  return h * 60 + m;
}

// busyIntervals: array of { start, end } in ms epoch, ALREADY padded by each
// booking's own buffer (see dbBusyInRange). Candidate is checked raw.
function collides(startMs, endMs, busyIntervals) {
  for (const b of busyIntervals) {
    if (startMs < b.end && endMs > b.start) return true;
  }
  return false;
}

function serviceOrThrow(serviceId) {
  const svc = config.servicesById[serviceId];
  if (!svc) {
    const err = new Error('Unknown service');
    err.status = 400;
    throw err;
  }
  return svc;
}

// How much of the day a booking actually reserves. For on-site work the ARRIVAL
// WINDOW is the reservation, not the job length: telling someone "8 to 10" and
// then booking the next customer at 9 would guarantee a broken promise. The
// window is always at least as long as the job.
function blockMinutes(svc) {
  return Math.max(svc.arrivalWindowMin || 0, svc.durationMin);
}

// What the customer is told. A phone consult really does start at 2:00; a crew
// with a ladder and a truck arrives "between 8 and 10", and saying so up front
// is the difference between running late and being late.
function slotLabel(svc, startDt) {
  if (!svc.arrivalWindowMin) return startDt.toFormat('h:mm a');
  const end = startDt.plus({ minutes: svc.arrivalWindowMin });
  const sameMeridiem = startDt.toFormat('a') === end.toFormat('a');
  return `${startDt.toFormat(sameMeridiem ? 'h:mm' : 'h:mm a')}–${end.toFormat('h:mm a')}`;
}

// The exact sentence the phone assistant is allowed to say out loud. Generated
// here, next to the arithmetic, because the one thing an LLM must never do is
// work out a date itself — it will produce a confident, plausible, wrong one.
function slotSpoken(svc, startDt) {
  const day = startDt.toFormat('cccc, LLLL d');
  if (!svc.arrivalWindowMin) return `${day} at ${startDt.toFormat('h:mm a')}`;
  const end = startDt.plus({ minutes: svc.arrivalWindowMin });
  return `${day}, arriving between ${startDt.toFormat('h:mm a')} and ${end.toFormat('h:mm a')}`;
}

/**
 * Generate bookable start times for a given service and local calendar date.
 * @param {string} serviceId
 * @param {string} dateISO  "YYYY-MM-DD" in the business timezone
 * @param {Array}  busyIntervals  [{start,end} ms epoch] from DB bookings + calendar feeds
 * @param {number} nowMs
 * @param {object} [opts]   { weather } — a verdict from weather.verdictFor(); a
 *                          blocked day yields no slots at all.
 * @returns {Array<{start,end,label,spoken,date,weekday}>}  ISO UTC + spoken local text
 */
function generateSlots(serviceId, dateISO, busyIntervals, nowMs, opts = {}) {
  const svc = serviceOrThrow(serviceId);
  const tz = config.timezone;

  // Weather closes the whole day for this service — no point walking the grid.
  if (opts.weather && opts.weather.blocked) return [];

  const blockMs = blockMinutes(svc) * 60000;
  // Step by the arrival window for on-site work: offering 8:00, 8:30 and 9:00 as
  // three separate "8–10 windows" would be three overlapping promises.
  const stepMs = (svc.arrivalWindowMin || config.business.slotStepMin) * 60000;
  const earliestMs = nowMs + config.business.leadTimeHours * 3600000;

  const dayStart = DateTime.fromISO(dateISO, { zone: tz }).startOf('day');
  if (!dayStart.isValid) return [];

  // Bounds: not in the past, not beyond maxDaysAhead.
  const maxDay = DateTime.fromMillis(nowMs, { zone: tz }).plus({ days: config.business.maxDaysAhead }).endOf('day');
  if (dayStart.endOf('day') < DateTime.fromMillis(nowMs, { zone: tz }).startOf('day')) return [];
  if (dayStart > maxDay) return [];

  const hours = hoursForWeekday(dayStart.weekday);
  if (!hours) return [];

  const open = dayStart.plus({ minutes: hmToMinutes(hours.open) });
  const close = dayStart.plus({ minutes: hmToMinutes(hours.close) });

  const slots = [];
  let cursor = open;
  while (cursor.plus({ milliseconds: blockMs }) <= close) {
    const startMs = cursor.toMillis();
    const endMs = startMs + blockMs;
    if (startMs >= earliestMs && !collides(startMs, endMs, busyIntervals)) {
      slots.push({
        start: DateTime.fromMillis(startMs, { zone: 'utc' }).toISO(),
        end: DateTime.fromMillis(endMs, { zone: 'utc' }).toISO(),
        label: slotLabel(svc, cursor),
        spoken: slotSpoken(svc, cursor),
        date: dateISO,
        weekday: cursor.toFormat('cccc'),
      });
    }
    cursor = cursor.plus({ milliseconds: stepMs });
  }
  return slots;
}

/**
 * Validate a requested start time at booking time. Returns {ok, end, reason}.
 */
function validateBooking(serviceId, startISO, busyIntervals, nowMs, opts = {}) {
  const svc = serviceOrThrow(serviceId);
  const tz = config.timezone;
  const blockMs = blockMinutes(svc) * 60000;

  const start = DateTime.fromISO(startISO, { zone: 'utc' });
  if (!start.isValid) return { ok: false, reason: 'Invalid start time' };
  const startMs = start.toMillis();
  const endMs = startMs + blockMs;

  if (opts.weather && opts.weather.blocked) {
    return { ok: false, reason: `That day is closed for outdoor work — ${opts.weather.reason}` };
  }

  // Must be a valid slot on that day (alignment + business hours).
  const dateISO = start.setZone(tz).toFormat('yyyy-LL-dd');
  const validStarts = new Set(generateSlots(serviceId, dateISO, busyIntervals, nowMs, opts).map((s) => s.start));
  if (!validStarts.has(start.toISO())) {
    return { ok: false, reason: 'That time is no longer available' };
  }
  if (collides(startMs, endMs, busyIntervals)) {
    return { ok: false, reason: 'That time was just booked' };
  }
  return {
    ok: true,
    end: DateTime.fromMillis(endMs, { zone: 'utc' }).toISO(),
    durationMin: svc.durationMin,
    blockMin: blockMinutes(svc),
    spoken: slotSpoken(svc, start.setZone(tz)),
    label: slotLabel(svc, start.setZone(tz)),
  };
}

module.exports = { generateSlots, validateBooking, serviceOrThrow, blockMinutes, slotLabel, slotSpoken };
