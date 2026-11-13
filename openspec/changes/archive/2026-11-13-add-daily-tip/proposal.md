## Why

The user wants a small, warm touch on every page — a short plant-care-themed motivational message near the top, with a different one each day — making the app feel more alive and more pleasant to show off (including to their teacher during the course presentation).

## What Changes

- Add a short, plant-themed motivational message shown on every page, inside the existing shared header, directly below the persistent nav.
- A fixed set of 10 messages rotates by calendar day (same message for everyone on a given day, deterministic, no randomness), so it reads as "today's tip" rather than reshuffling on every page load.

## Capabilities

### New Capabilities
- `daily-tip`: a deterministic, date-based rotation through 10 plant-themed messages, shown on every page.

### Modified Capabilities
(none)

## Impact

- `app/main.py`: a new Jinja global function (registered once in `create_app`, following the existing `asset_version` global's pattern) that uses the app's `clock()` callable to pick today's message.
- `app/templates/_header.html`: one new line of markup, shared across every page.
- `app/static/style.css`: one new, deliberately minimal style rule — a thin line of text, not a boxed notice.
- `tests/`: a new test file exercising the day-based selection via the existing `clock`/`TODAY` fixture pattern.
