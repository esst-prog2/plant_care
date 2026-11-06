## 1. Interval adjustment logic

- [x] 1.1 Add a small pure module (or extend `app/care.py`) with the clamp bounds (2–30 days) and two functions: one that takes the bundled interval plus the three condition deltas and returns the clamped starting interval, one that takes a plant's current interval plus a feedback choice ("wet"/"drooping"/"on_time"/None) and returns the clamped adjusted interval; verify unit tests for each question's delta, combinations, clamping at both bounds, and each feedback choice including "on_time" and None leaving the value unchanged

## 2. Add-flow: condition questions

- [x] 2.1 Replace the search result's immediate `hx-post="/plants"` with a button that opens a confirmation step showing the plant's name and the three question groups (light, warmth, pot/soil), each a 3-button choice defaulting to the neutral middle option; verify by searching and selecting a plant that the confirmation step appears instead of an immediate add
- [x] 2.2 Wire the confirmation step's "Add plant" action to `POST /plants` carrying `type_id`, `name` and the three chosen deltas (small integers); verify a request with no button touched sends three zero deltas
- [x] 2.3 In `load_plant_data`, apply the three deltas to the bundled/Wikipedia interval before clamping and storing, using the 1.1 function; verify an end-to-end test that adding a plant with a "bright light" and "terracotta pot" answer produces the expected adjusted interval on the stored plant and on its card

## 3. Watered-flow: feedback

- [x] 3.1 Add the three feedback buttons ("soil was still wet", "leaf was drooping", "right on time") to the "Watered!" confirmation already shown by `_details.html`, each posting to a new endpoint with the plant id and the choice; verify the buttons render only right after watering, not on a plain details view
- [x] 3.2 Add `POST /plants/{id}/feedback` that loads the plant, computes the adjusted interval with the 1.1 function, stores it, and re-renders the details view without the feedback buttons (so it can't be submitted twice); verify tests for all three choices and for the interval persisting after a restart
- [x] 3.3 Make dismissing the feedback step (closing the modal without pressing a button) leave the interval unchanged; verify a test that closes without choosing and checks the interval is untouched

## 4. Cross-cutting checks

- [x] 4.1 Verify a plant added before this change (no adjustment ever applied) keeps working exactly as today until its first feedback is given
- [x] 4.2 Verify the Google Calendar sync reads whatever `interval_days` currently is (no change needed in `app/sync.py`, but add a test that a feedback-adjusted interval is reflected in the next sync's due dates)
- [x] 4.3 Run the full test suite and `openspec validate` for this change; fix anything broken

## 5. Manual check

- [x] 5.1 Add a real plant through the running app, answering the three questions, and confirm the shown interval matches the expected adjustment; press "Watered", choose a feedback option, and confirm the countdown reflects the new interval
