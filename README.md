# NEMO Seamless Gutter

Marketing website + online booking for **NEMO Seamless Gutter**, a seamless gutter
contractor serving York County, PA. *Seamless gutters done right.*

- **Live:** https://nemoseamlessgutter.com (droplet `104.236.120.144`)
- **Contact:** call/text **(717) 578-0073** · enemo@nemoseamlessgutter.com
- **Design:** brand blue (`#243C94`) + orange (`#F16C27`) from the NEMO logo.

## Structure

```
index.html        # single-page marketing site (hero, services, why-us, FAQ, areas, book, contact)
                  #   + SEO: canonical, OG/Twitter, geo tags, JSON-LD (RoofingContractor + FAQPage)
services/         # seamless-gutter-installation, gutter-guards, gutter-cleaning-repair
guides/           # seamless-vs-sectional-gutters, gutter-cleaning-cost-york-pa
robots.txt        # allows search + AI crawlers (GPTBot, PerplexityBot, ClaudeBot, …); points to sitemap
sitemap.xml       # sitemap (home + service + guide pages)
styles.css        # site styles + design tokens (blue/orange)
script.js         # header scroll state, mobile nav, footer year
booking.css       # booking widget styles
booking.js        # booking widget (service → date → slot → details → confirm)
setup.html        # one-time owner setup page (connect email + calendars)
assets/           # logo (svg + 4k png), white logo, square icon/favicon, og image
server/           # booking + two-way calendar-sync API (Node/Express/SQLite)
```

## Booking + two-way calendar sync

The booking system avoids Google's lengthy OAuth verification by using the
universal, no-OAuth path that works for **both Google and Apple** calendars:

- **Read the owner's blocks → hide site slots.** The API pulls the owner's
  read-only **ICS feed URLs** (Google "secret iCal address", iCloud published
  calendar) on a short cache interval. Any event there blocks matching slots.
- **Write site bookings → the owner's calendar.** Each booking emails an
  **ICS invite (`METHOD:REQUEST`)** to the owner and the customer; Google and Apple
  both add `REQUEST` invites natively. Optional iCloud CalDAV write-back inserts
  the event instantly into Apple Calendar.
- **No double-booking.** Site availability = local SQLite bookings ∪ calendar
  busy times, re-validated inside a transaction at booking time.

Three booking types: **Free On-Site Estimate** (60 min), **Gutter Cleaning /
Repair** (90 min), and **Phone Consultation** (20 min). On-site services require a
job address; the phone consult does not. Business hours, slot step, buffer, and
lead time are configurable in `server/config.js` / env.

## Weather-aware scheduling

Gutter work is decided by the sky, so the diary is **computed on every request**
rather than read out of a fixed calendar:

```
available(day) = business hours − booked jobs (+ travel buffer)
               − days the forecast rules out for that kind of work
               − Eric's manual open/close
```

- **Forecast** comes from the National Weather Service (`api.weather.gov`) — free,
  keyless, unmetered. Cached hourly in `weather_days`. Only hours the crew would
  actually be working count: an 11 PM storm doesn't close an 8 AM job.
- **Each service declares how much weather matters.** A phone consult never moves;
  an estimate only stops for a downpour; ladder work stops well before it rains.
  Tuned with `WEATHER_HARD_POP` / `WEATHER_LIGHT_POP` / `WEATHER_*_WIND`.
- **Eric always wins.** `/owner/schedule` (signed link, in his 6 AM email) opens or
  closes any day by hand, and that beats the forecast in both directions.
- **Arrival windows, not exact times.** On-site work is quoted as "arriving between
  8 and 10". A crew that hits rotted fascia runs ninety minutes late and every
  later "9:15" becomes a broken promise. The window *is* the reservation.

### Holds → confirmation

The forecast only reaches about 6½ days, but customers book weeks out. So
weather-sensitive bookings made beyond `CONFIRM_LEAD_HOURS` (30h) are stored as
**tentative holds** — the slot is genuinely reserved, we just haven't promised the
sky yet — and `server/jobs/confirm_run.js` resolves them as the day approaches:

| Forecast at T-30h | What happens |
| --- | --- |
| fine | booking confirmed, customer emailed "you're confirmed" |
| wet | moved to the next clear slot, both parties emailed, one-tap link to pick another |
| wet, already moved twice | handed to Eric **once** (`hold_state = 'escalated'`), listed in his digest |
| no slot to move to | same escalation |

Runs hourly from `/etc/cron.d/nemo-booking` (repo copy: `deploy/cron-nemo-booking`);
the 6 AM run also emails Eric today + tomorrow, the forecast, what moved overnight,
and his open/close links. Every decision is written to `booking_events`, which is
the answer when a customer says "nobody told me it moved".

Customers reschedule themselves from a signed `/booking/reschedule` link — no
login, no phone tag, and it never offers them the slot they're already in.

### API

| Method | Path | Purpose |
| --- | --- | --- |
| GET  | `/api/health` | health check |
| GET  | `/api/services` | service list + booking rules + today's date and the next 14 days |
| GET  | `/api/availability?service=&date=` | open slots for a day, + why the weather closed it |
| GET  | `/api/next-openings?service=&limit=` | next bookable windows, with ready-to-speak text |
| POST | `/api/book` | create a booking |
| GET  | `/api/admin/bookings?token=` | upcoming bookings (admin) |
| POST | `/api/admin/cancel?token=` | cancel a booking (admin) |
| GET  | `/booking/reschedule?uid=&sig=` | customer picks a new time (signed link) |
| GET  | `/owner/schedule?sig=` | Eric opens/closes days for weather (signed link) |

`/api/services` returns the resolved calendar (`today`, `upcomingDays` with weekday
names and open/closed) because the phone assistant reads it — working out that
"Thursday" means the 23rd is exactly the arithmetic a language model gets subtly
wrong, and a visit booked on the wrong morning is worse than no booking.

Bookings carry a `source` of `web` or `phone-ai`. A request is only labelled
`phone-ai` if it presents the `x-agent-token` header matching `AGENT_TOKEN`, so
the label can be trusted; a spoofed body field can't claim it.

| Method | Path | Purpose |
| --- | --- | --- |
| POST | `/api/lead` | phone assistant hands a caller's details to Eric (agent token required) |
| GET  | `/api/admin/leads?token=` | recent leads, including any whose email failed |

## Phone assistant

An ElevenLabs voice agent answers the phone, answers questions about the business,
and takes the caller's details so Eric can ring them back.

**It books real appointments** — it was reduced to message-taking only because
there was no schedule to book against, and now there is one.

It never reasons about dates. `check_openings` returns openings with a `spoken`
sentence written out for it to read verbatim plus an opaque `start` to hand back to
`book_appointment`, and the server refuses any time it did not offer (a 3 AM slot
and a beyond-horizon date are both rejected). It also has to be honest about holds,
because the confirmation wording it reads back is generated server-side.

When it can't book — no openings, the caller won't commit, a tool failed, or
they're outside York County — it falls back to `send_message_to_eric` as before.
Never both, never neither.

It lives in [`agent/`](agent/) — see [`agent/README.md`](agent/README.md) for how to
edit what it says, how to test it without a phone number, and how to attach one.

### Configuration

Copy `server/.env.example` → `server/.env` and fill in. The site and booking
work without these, but **calendar sync and email need them**:

- `OWNER_EMAIL` — address(es) that receive invites/alerts. Defaults to
  `enemo@nemoseamlessgutter.com`.
- `ICS_FEEDS` — comma-separated read-only calendar feed URLs (Google secret iCal
  + iCloud published calendar) so the owner's manual blocks hide site slots.
- `SMTP_*` / `FROM_EMAIL` — outbound email for invites + confirmations.
- `ICLOUD_*` — optional iCloud CalDAV write-back.
- `ADMIN_TOKEN` — **required**; protects admin endpoints and signs the cancel,
  reschedule and owner-schedule links.
- `WEATHER_*` — forecast location and the thresholds that close a day. Set
  `WEATHER_ENABLED=false` to fall back to plain availability.
- `CONFIRM_LEAD_HOURS` / `REBOOK_SEARCH_DAYS` / `MAX_AUTO_RESCHEDULES` — the hold
  loop: how close in to commit, how far ahead to hunt for a replacement, and how
  many automatic moves before a human is asked.

The owner can connect everything from a single-use link at
`/setup.html#t=<SETUP_TOKEN>` without touching the server.

## Deployment

Static files live at `/var/www/nemo-seamless-gutter` on the droplet, served by the
nginx site `nemo-seamless-gutter`. The booking API runs under **pm2** on
`127.0.0.1:3009`, reverse-proxied by nginx at `/api/`.

```bash
# static
rsync -avz index.html styles.css script.js booking.css booking.js setup.html \
  robots.txt sitemap.xml site.webmanifest assets/ \
  root@104.236.120.144:/var/www/nemo-seamless-gutter/
rsync -avz services/ root@104.236.120.144:/var/www/nemo-seamless-gutter/services/
rsync -avz guides/   root@104.236.120.144:/var/www/nemo-seamless-gutter/guides/
# api
rsync -avz --exclude node_modules --exclude .env --exclude '*.sqlite*' --exclude data \
  server/ root@104.236.120.144:/var/www/nemo-seamless-gutter/server/
ssh root@104.236.120.144 'cd /var/www/nemo-seamless-gutter/server && npm install --omit=dev && pm2 restart nemo-seamless-gutter'
```

nginx proxies `/api/`, `/booking/` and `/owner/` to the Node app; the config is
mirrored at `deploy/nginx-nemo-seamless-gutter.conf`. Scp it and reload — never
edit it over an ssh heredoc.

The scheduling cron lives at `/etc/cron.d/nemo-booking` (this droplet keeps
per-project crons in `/etc/cron.d/`; `crontab -` would clobber the others). Check
it with:

```bash
ssh root@104.236.120.144 'cd /var/www/nemo-seamless-gutter/server && node jobs/confirm_run.js --dry-run'
tail -f /var/log/nemo-confirm.log
```
