## Why

The HW4 spike found that no citable horticultural source gives a fixed watering interval in days for any of 12 checked plants — real advice ties watering to the state of the compost and the season, not a day count. The app already labels its interval as an estimate rather than a verified fact. The natural next step is to make that estimate better for the user's actual plant: let it start from a couple of quick facts about where the plant sits, and let it adjust from what the user actually observes when watering, instead of staying a single fixed number for the plant's whole life.

## What Changes

- When adding a plant, after selecting its type, ask a few optional questions about this specific plant's conditions (how much light it gets, how warm the spot is, the pot/soil situation). Answering adjusts the bundled starting interval by a fixed, documented rule; skipping leaves the bundled estimate unchanged.
- After pressing "Watered", offer an optional, dismissible follow-up with three choices: "soil was still wet", "leaf was drooping", "right on time". The first lengthens the plant's interval, the second shortens it, the third leaves it unchanged; each adjustment is small and the interval stays within a minimum and maximum.
- The stored watering interval becomes a value that can drift per plant over time, rather than a constant copied once from the bundled list.

Out of scope for this change: any machine-learning or community-data model (the adjustments are fixed, documented rules); moisture sensors or other hardware; changing how Google Calendar reminders are scheduled (they still read the plant's current interval, whatever it now is).

## Capabilities

### New Capabilities
<!-- None: this changes how an existing value is set and adjusted, not the add/water/remove flows themselves. -->

### Modified Capabilities
- `plant-care-data`: adds the optional add-time condition questions and the rule that adjusts the bundled starting interval from the answers.
- `watering-tracker`: adds the optional post-watering feedback and the rule that adjusts the plant's interval from it, and notes that a plant's interval can now differ from the bundled default over its lifetime.

## Impact

- Database: each plant needs to store its current (possibly adjusted) interval separately from the bundled default, so the bundled list is never overwritten; existing plants added before this change keep their current interval unchanged until they next receive feedback.
- UI: a new short step in the add-plant flow, and a new small panel after "Watered"; no change to the grid, search, removal, or Google reminder flows.
- No new external dependencies.
