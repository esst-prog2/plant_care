## Why

Watering status today only shows up per-plant, on each plant's own card. To know what needs doing soon across several plants, the user has to open every group and read each card, or just check the Google Calendar sync on their phone. A single, date-sorted list of what's coming up — right on the site, filterable by group — removes that mental math without duplicating or replacing the existing Google Calendar reminders.

## What Changes

- Add a new "Upcoming" view: a flat list of every plant with a computed due status, sorted most-urgent first (overdue, then due today, then soonest-due), with no artificial lookahead cutoff.
- The view is filterable by group, reusing the existing `group_id`/"All" scoping already used by the collection views.
- Add an "Upcoming" link to the existing topbar on both the landing page and every collection view, so it's reachable the same way everywhere ("a separate menu item," as asked for), without replacing the existing page-specific buttons.
- No new database schema; the view reads existing `plants`/`groups` data through the care-status logic that already exists.

## Capabilities

### New Capabilities
- `upcoming-view`: a date-sorted, group-filterable list of upcoming/overdue watering across plants, as its own page.

### Modified Capabilities
(none — `watering-tracker`'s per-plant status logic and `plant-groups`' group/filter semantics are reused as-is, not changed)

## Impact

- `app/main.py`: a new route (e.g. `GET /upcoming`) and a persistent top bar used by `index.html` and `collection.html`.
- `app/care.py`: reuses `plant_days_left`/`status_of`; likely a small addition to sort/aggregate across plants rather than per-card.
- A new template for the upcoming list; `base.html` or equivalent gains the shared top bar.
- `app/static/style.css`: new top bar + list styles, using the existing palette.
- Tests: a new `tests/test_upcoming.py` (or additions to `tests/test_groups.py`/`tests/test_web.py`).
