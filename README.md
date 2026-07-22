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

### API

| Method | Path | Purpose |
| --- | --- | --- |
| GET  | `/api/health` | health check |
| GET  | `/api/services` | service list + booking rules + today's date and the next 14 days |
| GET  | `/api/availability?service=&date=` | open slots for a day |
| POST | `/api/book` | create a booking |
| GET  | `/api/admin/bookings?token=` | upcoming bookings (admin) |
| POST | `/api/admin/cancel?token=` | cancel a booking (admin) |

`/api/services` returns the resolved calendar (`today`, `upcomingDays` with weekday
names and open/closed) because the phone assistant reads it — working out that
"Thursday" means the 23rd is exactly the arithmetic a language model gets subtly
wrong, and a visit booked on the wrong morning is worse than no booking.

Bookings carry a `source` of `web` or `phone-ai`. A request is only labelled
`phone-ai` if it presents the `x-agent-token` header matching `AGENT_TOKEN`, so
the label in Eric's inbox can be trusted; a spoofed body field can't claim it.

## Phone assistant

An ElevenLabs voice agent answers the phone, answers questions, and books
estimates on the call using the API above. It lives in [`agent/`](agent/) — see
[`agent/README.md`](agent/README.md) for how to edit what it says, how to test it
without a phone number, and how to attach a real number.

### Configuration

Copy `server/.env.example` → `server/.env` and fill in. The site and booking
work without these, but **calendar sync and email need them**:

- `OWNER_EMAIL` — address(es) that receive invites/alerts. Defaults to
  `enemo@nemoseamlessgutter.com`.
- `ICS_FEEDS` — comma-separated read-only calendar feed URLs (Google secret iCal
  + iCloud published calendar) so the owner's manual blocks hide site slots.
- `SMTP_*` / `FROM_EMAIL` — outbound email for invites + confirmations.
- `ICLOUD_*` — optional iCloud CalDAV write-back.
- `ADMIN_TOKEN` — **required**; protects admin endpoints and signs cancel links.

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
