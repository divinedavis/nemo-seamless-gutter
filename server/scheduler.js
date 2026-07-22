'use strict';
// The one place that answers "when can we actually come out?".
//
// Shared deliberately by the HTTP layer and the overnight confirm/reschedule job
// so a slot the phone assistant offers and a slot the automation moves someone
// into are produced by exactly the same rules. Two implementations of "is this
// free?" is how you end up double-booking a crew.
const { DateTime } = require('luxon');
const config = require('./config');
const { stmts } = require('./db');
const { generateSlots, blockMinutes } = require('./availability');
const calendar = require('./calendar');
const weather = require('./weather');

// Active bookings overlapping a window, each padded by its own travel buffer.
// Tentative holds are included: the customer owns that time even though we
// haven't promised them the weather yet.
function dbBusyInRange(startMs, endMs, excludeUid) {
  const rows = stmts.inRange.all({
    start: DateTime.fromMillis(startMs, { zone: 'utc' }).toISO(),
    end: DateTime.fromMillis(endMs, { zone: 'utc' }).toISO(),
  });
  return rows
    .filter((r) => r.uid !== excludeUid)
    .map((r) => {
      const svc = config.servicesById[r.service];
      const bufMs = ((svc && svc.bufferMin) || 0) * 60000;
      return {
        start: DateTime.fromISO(r.start_utc, { zone: 'utc' }).toMillis() - bufMs,
        end: DateTime.fromISO(r.end_utc, { zone: 'utc' }).toMillis() + bufMs,
      };
    });
}

async function busyForDay(dateISO, excludeUid) {
  const tz = config.timezone;
  const dayStart = DateTime.fromISO(dateISO, { zone: tz }).startOf('day');
  const startMs = dayStart.minus({ days: 1 }).toMillis();
  const endMs = dayStart.plus({ days: 2 }).toMillis();
  const external = await calendar.getExternalBusy(startMs, endMs);
  return [...dbBusyInRange(startMs, endMs, excludeUid), ...external];
}

/**
 * Walk forward day by day and collect the next bookable openings for a service,
 * skipping days the weather rules out.
 *
 * @param {string} serviceId
 * @param {object} [opts]
 *   fromMs      start searching from this instant (default: now)
 *   limit       how many openings to return (default 3)
 *   days        how many days to scan (default holds.rebookSearchDays)
 *   perDay      cap openings offered per day (default 2) so three choices aren't
 *               all the same Tuesday
 *   excludeUid  ignore this booking when checking conflicts — used when moving a
 *               booking, which must not collide with the slot it is leaving
 *   excludeStart drop this exact start from the results. Pairs with excludeUid:
 *               ignoring a booking's own busy block makes its current slot look
 *               free again, and offering someone their existing time as a "new
 *               time" on a reschedule page is a dead end.
 * @returns {Promise<{openings:Array, skipped:Array}>}
 */
async function findOpenings(serviceId, opts = {}) {
  const tz = config.timezone;
  const nowMs = opts.fromMs || Date.now();
  const limit = opts.limit || 3;
  const days = opts.days || config.holds.rebookSearchDays;
  const perDay = opts.perDay || 2;

  const openings = [];
  const skipped = [];
  let cursor = DateTime.fromMillis(nowMs, { zone: tz }).startOf('day');

  for (let i = 0; i < days && openings.length < limit; i += 1) {
    const dateISO = cursor.toFormat('yyyy-LL-dd');
    cursor = cursor.plus({ days: 1 });

    if (!config.business.hours[DateTime.fromISO(dateISO, { zone: tz }).weekday % 7]) continue;

    const verdict = weather.verdictFor(serviceId, dateISO);
    if (verdict.blocked) {
      skipped.push({ date: dateISO, weekday: DateTime.fromISO(dateISO, { zone: tz }).toFormat('cccc'), reason: verdict.reason });
      continue;
    }

    const busy = await busyForDay(dateISO, opts.excludeUid);
    let slots = generateSlots(serviceId, dateISO, busy, nowMs, { weather: verdict });
    if (opts.excludeStart) {
      const skip = DateTime.fromISO(opts.excludeStart, { zone: 'utc' }).toMillis();
      slots = slots.filter((s) => DateTime.fromISO(s.start, { zone: 'utc' }).toMillis() !== skip);
    }
    for (const s of slots.slice(0, perDay)) {
      openings.push({ ...s, weather: { status: verdict.status, pop: verdict.pop == null ? null : verdict.pop, summary: verdict.summary || null } });
      if (openings.length >= limit) break;
    }
  }
  return { openings, skipped };
}

// Is this booking far enough out that the forecast can't be trusted yet?
// Weather-insensitive work (a phone call) is never tentative.
function shouldHold(serviceId, startISO) {
  const svc = config.servicesById[serviceId];
  if (!svc || (svc.weather || 'none') === 'none') return false;
  if (!config.weather.enabled) return false;
  const hoursOut = (DateTime.fromISO(startISO, { zone: 'utc' }).toMillis() - Date.now()) / 3600000;
  return hoursOut > config.holds.confirmLeadHours;
}

function logEvent(uid, event, detail) {
  try {
    stmts.logEvent.run({ uid, event, detail: detail || null, created_at: DateTime.utc().toISO() });
  } catch (err) {
    console.error('[scheduler] event log failed:', err.message);
  }
}

/**
 * Move a booking to a new start and tell everyone. The single write path for a
 * reschedule, whether the customer tapped a button or the weather job decided
 * for them — so the audit trail, the cache invalidation and the emails can't
 * drift apart between the two.
 *
 * @param {object} b        the existing booking row
 * @param {string} startISO new UTC start
 * @param {object} v        the result of validateBooking() for that start
 * @param {string} reason   'customer-reschedule' | 'weather-auto' | ...
 */
async function applyMove(b, startISO, v, reason) {
  const previousStart = b.start_utc;
  const newStart = DateTime.fromISO(startISO, { zone: 'utc' }).toISO();

  stmts.moveBooking.run({
    uid: b.uid,
    start_utc: newStart,
    end_utc: v.end,
    previous_start: previousStart,
  });

  // Re-derive the hold state from the NEW date rather than assuming a move means
  // certainty. A customer rescheduling themselves three weeks out lands right
  // back outside the forecast horizon, and marking that "confirmed" would drop
  // them out of the nightly sweep — the one booking most likely to get rained on
  // would be the one nothing was watching.
  const state = shouldHold(b.service, newStart) ? 'tentative' : 'confirmed';
  if (state === 'confirmed') stmts.markConfirmed.run({ uid: b.uid, at: DateTime.utc().toISO() });
  else stmts.setHoldState.run({ uid: b.uid, state: 'tentative' });

  calendar.invalidateBusyCache();
  logEvent(b.uid, 'moved', `${reason}: ${previousStart} → ${newStart} (now ${state}, move #${(b.reschedule_count || 0) + 1})`);

  const updated = { ...b, start_utc: newStart, end_utc: v.end, hold_state: state };
  try {
    await calendar.sendRescheduleEmails(updated, previousStart, reason);
  } catch (err) {
    console.error('[scheduler] reschedule email failed:', err.message);
    logEvent(b.uid, 'email-failed', `reschedule notice: ${err.message}`);
  }
  return { ...updated, spoken: v.spoken, when: v.label };
}

module.exports = { dbBusyInRange, busyForDay, findOpenings, shouldHold, logEvent, applyMove, blockMinutes };
