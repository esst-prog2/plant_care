## Context

See proposal.md for motivation. Relevant current state:
- `plants.interval_days` is already a per-plant column, set once when the background fetch completes (`app/main.py: load_plant_data` → `db.complete_plant`). It is a copy taken from the bundled list or Wikipedia-derived data at add time, not a live reference to `data/plants.json` — so making it drift per plant needs no new "override" column, just writing to the column that already exists.
- The add flow (`_results.html`) currently posts straight to `POST /plants` the moment a search result is clicked: `hx-post="/plants" hx-vals='{"type_id":..., "name":...}'`. There is no intermediate step today.
- The watered flow (`POST /plants/{id}/watered` in `app/main.py`) sets `last_watered` to today and re-renders `_details.html` with `watered=true`, which shows "Watered! Next watering in N days."

## Goals / Non-Goals

**Goals:**
- The three condition questions and the three feedback buttons are optional at every step; a user who never engages with either gets exactly today's behaviour.
- All adjustments are fixed, named constants in code — no learned weights, no external data.

**Non-Goals:**
- Remembering the raw answers to the condition questions after they've been applied (only their effect, the resulting interval, is kept — see Decision 3).
- Changing anything about the Google Calendar sync; it keeps reading whatever `interval_days` currently is, unchanged.

## Decisions

### Decision 1: The three condition questions and their adjustments (needs the user's confirmation)

Asked once, between selecting a search result and the plant actually being added. Each is a 3-button choice with a neutral middle option; leaving the panel untouched (i.e. not pressing any of the directional buttons) is exactly the same as picking the middle, neutral button — simpler to build than a true "unanswered" tri-state, and behaviourally identical (0 adjustment).

| Question | Options and adjustment |
|---|---|
| Light | Low light **+2 days** · About right **+0** · Bright/direct light **−2 days** |
| Warmth | Cooler than average **+1 day** · About average **+0** · Warmer (e.g. near a radiator) **−1 day** |
| Pot / soil | Terracotta or unglazed clay (dries faster) **−1 day** · Not sure / other **+0** · Plastic or glazed ceramic (holds moisture) **+1 day** |

More light or more warmth means the compost dries faster, so the interval gets shorter; a porous pot dries faster too. These three combine by simple addition onto the bundled default, then the result is clamped (Decision 2). Recommended because it mirrors the direction (not the precision) of what Planta and Greg use light/pot for, discussed earlier in this project, kept to three fixed-size steps instead of a continuous model.

### Decision 2: Bounds (needs the user's confirmation)

The interval is clamped to **2–30 days** after every adjustment, whether from the add-time questions or from watering feedback. This comfortably contains the bundled defaults (4–21 days) with room to move in both directions. A single universal bound (rather than one scaled per species) is simplest to implement and explain, at the cost of being a little generous for a 4-day fern and a little tight for a 21-day cactus; flagged here rather than silently chosen because a per-species bound is also reasonable and would change the task breakdown.

### Decision 3: Watering feedback adjustment

"Soil was still wet" → **+1 day**. "Leaf was drooping" → **−1 day**. "Right on time" or dismissing → **+0**. Applied to the plant's current `interval_days` (whatever it has drifted to), clamped to the same 2–30 day bounds. Offered once, right after the existing "Watered! Next watering in N days." confirmation, as three buttons in the same panel; not a separate pop-up later, so no extra scheduling or follow-up logic is needed.

### Decision 4: Nothing new is stored except the resulting interval

The condition answers are applied once, immediately, to compute the starting `interval_days`; they are not saved anywhere, so there is no new "why is this plant's interval different" audit trail. Feedback events are likewise not logged individually — only their cumulative effect on `interval_days` remains. Chosen to keep the change small, matching "the smallest thing that answers it" from how this project has worked so far; a history of adjustments is a reasonable future idea but is not needed for the behaviour in the specs.

### Decision 5: Existing plants are untouched until their next feedback

A plant added before this change keeps its current `interval_days` exactly as it is; the first time its "Watered" is pressed, it gets the same optional feedback panel as any other plant, and only then can its interval move. No migration or backfill needed, because the column already holds a sensible value for every plant.

### Decision 6: Where the condition questions live in the request flow

Clicking a search result switches the add panel to a small confirmation screen (plant name, the three question groups, an "Add plant" button) instead of posting immediately. "Add plant" posts to `POST /plants` with the existing `type_id`/`name` fields plus the three chosen adjustments (as whole-day deltas, already computed client-side from which button is active, so the server only ever receives three small integers, not option names). The background fetch (`load_plant_data`) adds the chosen deltas once the bundled/Wikipedia interval is known, clamps, and stores the result — the same place `interval_days` is set today.

## Risks / Trade-offs

- **Fixed per-question amounts won't fit every plant** (a cactus already at 21 days moving by the same ±2 as a 4-day fern) → acceptable for a first version; the universal bounds prevent anything absurd, and the numbers are named constants, easy to retune later.
- **A user who mashes "leaf was drooping" repeatedly could bottom out at the minimum** → the minimum (2 days) is itself a safe floor, not an error state; the countdown and the calendar reminders keep working normally at the bound.
- **No record of why an interval is what it is** (Decision 4) → if this turns out to matter, a later change can add a log table without touching these specs.

## Open Questions

- The exact wording shown on the three buttons per question (e.g. "Low light" vs "Not much light") is a copy detail, not a behaviour change, and can be finalised during implementation without revisiting this design.
