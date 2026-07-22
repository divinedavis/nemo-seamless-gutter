'use strict';
// The loop that makes a weather-driven schedule bookable.
//
// Runs hourly from cron. Everything a customer books more than a day out is a
// HOLD; this job walks up to each hold as its day approaches and turns it into
// either "you're confirmed" or "we moved you to Thursday" — automatically, with
// the customer emailed either way. That is the whole trick: the appointment is
// real, and the churn is absorbed by software instead of by Eric making nine
// phone calls every time it rains.
//
//   node jobs/confirm_run.js            hourly pass (confirm / move)
//   node jobs/confirm_run.js --digest   also send Eric his morning summary
//   node jobs/confirm_run.js --dry-run  decide and print, change nothing
//
// Deliberately a cron script rather than a setInterval inside server.js: a pm2
// restart mid-sweep must not skip a day's confirmations, and a crash here must
// not take the booking API down with it.
const path = require('path');

// Load .env the same way server.js does, so the job sees SMTP + tokens.
try {
  const fs = require('fs');
  const envPath = path.join(__dirname, '..', '.env');
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

const { DateTime } = require('luxon');
const config = require('../config');
const { stmts } = require('../db');
const { validateBooking } = require('../availability');
const calendar = require('../calendar');
const weather = require('../weather');
const scheduler = require('../scheduler');

const DRY = process.argv.includes('--dry-run');
const WANT_DIGEST = process.argv.includes('--digest');
const tz = config.timezone;

function log(...a) {
  console.log(`[confirm ${DateTime.now().setZone(tz).toFormat('LL-dd HH:mm')}]`, ...a);
}

function localDate(iso) {
  return DateTime.fromISO(iso, { zone: 'utc' }).setZone(tz).toFormat('yyyy-LL-dd');
}

function localWhen(iso) {
  return DateTime.fromISO(iso, { zone: 'utc' }).setZone(tz).toFormat("cccc, LLL d 'at' h:mm a");
}

// Hand a booking back to a human. Flipping it out of 'tentative' is the point:
// a hold the automation cannot solve must be raised to Eric ONCE, not shouted
// about every hour until someone notices.
function escalate(b, detail, humanLine, actions) {
  stmts.setHoldState.run({ uid: b.uid, state: 'escalated' });
  scheduler.logEvent(b.uid, 'escalated', detail);
  actions.push(`NEEDS YOUR CALL: ${b.name} (${b.phone}) — ${humanLine}`);
}

/* --- 1. confirm or move every hold inside the horizon --------------------- */
async function processHolds(actions) {
  const now = DateTime.utc();
  const holds = stmts.pendingHolds.all({
    now: now.toISO(),
    until: now.plus({ hours: config.holds.confirmLeadHours }).toISO(),
  });
  log(`${holds.length} hold(s) inside the ${config.holds.confirmLeadHours}h horizon`);

  for (const b of holds) {
    const dateISO = localDate(b.start_utc);
    const verdict = weather.verdictFor(b.service, dateISO);

    // The forecast says go — commit, and tell them so.
    if (!verdict.blocked) {
      log(`CONFIRM ${b.name} ${localWhen(b.start_utc)} (${verdict.status})`);
      if (DRY) continue;
      stmts.markConfirmed.run({ uid: b.uid, at: DateTime.utc().toISO() });
      scheduler.logEvent(b.uid, 'confirmed', `weather ${verdict.status}${verdict.pop != null ? ` pop=${verdict.pop}` : ''}`);
      try {
        await calendar.sendConfirmationEmail(b);
      } catch (err) {
        log(`  ! confirmation email failed: ${err.message}`);
        scheduler.logEvent(b.uid, 'email-failed', `confirmation: ${err.message}`);
      }
      actions.push(`confirmed ${b.name} for ${localWhen(b.start_utc)}`);
      continue;
    }

    // Rained off. Shuffling someone indefinitely is worse than a phone call, so
    // after a couple of automatic moves we stop and hand it to Eric.
    if (b.reschedule_count >= config.holds.maxAutoReschedules) {
      log(`ESCALATE ${b.name} — already moved ${b.reschedule_count}x`);
      if (DRY) continue;
      escalate(b, `moved ${b.reschedule_count}x, weather ${verdict.status}`,
        `rained off ${b.reschedule_count + 1} times — still down for ${localWhen(b.start_utc)}`, actions);
      continue;
    }

    const { openings } = await scheduler.findOpenings(b.service, {
      // Never offer a replacement earlier than the job it is replacing.
      fromMs: Math.max(Date.now(), DateTime.fromISO(b.start_utc, { zone: 'utc' }).toMillis()),
      limit: 1,
      perDay: 1,
      excludeUid: b.uid,
      excludeStart: b.start_utc,
    });

    if (!openings.length) {
      log(`NO SLOT for ${b.name} — escalating`);
      if (DRY) continue;
      escalate(b, `no replacement slot within ${config.holds.rebookSearchDays}d`,
        'rained off and nothing free to move them to', actions);
      continue;
    }

    const target = openings[0];
    log(`MOVE ${b.name}: ${localWhen(b.start_utc)} → ${localWhen(target.start)} (${verdict.reason})`);
    if (DRY) continue;

    const busy = await scheduler.busyForDay(target.date, b.uid);
    const v = validateBooking(b.service, target.start, busy, Date.now(), {
      weather: weather.verdictFor(b.service, target.date),
    });
    if (!v.ok) {
      log(`  ! target slot went stale: ${v.reason}`);
      escalate(b, `move-failed: ${v.reason}`, `could not be moved automatically (${v.reason})`, actions);
      continue;
    }
    await scheduler.applyMove(b, target.start, v, 'weather-auto');
    actions.push(`moved ${b.name} to ${localWhen(target.start)} — ${verdict.reason}`);
  }
}

/* --- 2. Eric's morning summary -------------------------------------------- */
function jobsOn(dayStart) {
  return stmts.inRange.all({
    start: dayStart.toUTC().toISO(),
    end: dayStart.plus({ days: 1 }).toUTC().toISO(),
  });
}

async function sendDigest(actions) {
  const today = DateTime.now().setZone(tz).startOf('day');
  const tomorrow = today.plus({ days: 1 });

  // Escalations raised by an earlier run are in the database, not in this
  // process's `actions`. Re-list every outstanding one: the 3 AM sweep that gave
  // up on a booking is exactly the thing that must reach Eric at 6 AM.
  const stuck = stmts.escalatedHolds.all({ now: DateTime.utc().toISO() });
  for (const b of stuck) {
    const line = `NEEDS YOUR CALL: ${b.name} (${b.phone}) — weather-stuck, currently ${localWhen(b.start_utc)}`;
    if (!actions.includes(line)) actions.push(line);
  }

  const payload = {
    today: { label: today.toFormat('cccc, LLL d'), weather: weather.describeDay(today.toFormat('yyyy-LL-dd')), jobs: jobsOn(today) },
    tomorrow: { label: tomorrow.toFormat('cccc, LLL d'), weather: weather.describeDay(tomorrow.toFormat('yyyy-LL-dd')), jobs: jobsOn(tomorrow) },
    actions,
  };
  if (DRY) {
    log('digest (dry run):', JSON.stringify(payload, null, 2));
    return;
  }
  const r = await calendar.sendOwnerDigest(payload);
  log(`digest ${r.sent ? 'sent' : `NOT sent (${r.reason})`}`);
}

/* --- main ----------------------------------------------------------------- */
(async () => {
  const actions = [];
  try {
    // Force a refresh: everything below is decided by this data, and an hour-old
    // cached forecast is not a good enough reason to move someone's morning.
    const w = await weather.refresh(true);
    log(`forecast refreshed (${(w.days || []).length} days)`);
  } catch (err) {
    // Fail loudly but keep going. With no fresh forecast, verdictFor() falls back
    // to the last cached day and then to 'unknown' — which leaves holds alone
    // rather than cancelling anyone's appointment over a network blip.
    log(`! weather refresh failed: ${err.message} — using cached forecast`);
  }

  try {
    await processHolds(actions);
  } catch (err) {
    log(`! hold processing failed: ${err.message}`);
    console.error(err);
    process.exitCode = 1;
  }

  if (WANT_DIGEST) {
    try {
      await sendDigest(actions);
    } catch (err) {
      log(`! digest failed: ${err.message}`);
      process.exitCode = 1;
    }
  }
  log(`done — ${actions.length} action(s)`);
})();
