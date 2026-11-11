## Why

The bundled list of ~41 houseplants was picked by Claude as a plausible common-houseplant set, not chosen by the user. The user has since picked their own 50-species list (the ones they actually care about), so the bundled list should match it. At the same time, the plant details view only shows light and a watering estimate; the user wants it to also answer three more questions people ask when they get a new plant: is it safe around pets, does it want extra humidity, and how do you propagate it.

## What Changes

- Replace `data/plants.json`'s ~41 entries with the user's 50-species list. 35 species carry over from the current list unchanged (id/name/light/watering_days/wikipedia re-verified, not re-derived); 6 current entries that are not in the new list are removed (bird-of-paradise, air-plant, money-tree, umbrella-plant/Schefflera, lucky-bamboo, cast-iron-plant); 15 new species are added, each researched the same way the original list was built (light requirement, a watering-day estimate, and a live-verified English Wikipedia title). **BREAKING**: plant type ids for the 6 removed species disappear from the bundled list; any already-added plant of those types keeps working (its data is already stored on the plant row) but the type can no longer be searched or re-added.
- Add three new per-species fields to the bundled list and to the details view: toxicity (to pets/humans), humidity preference, and a short propagation tip. All 50 entries get all three fields filled in (no partial backfill).
- Toxicity is sourced from a single named, citable reference per species (see design.md); humidity and propagation are general-knowledge estimates, labelled the same way light and watering already are.

## Capabilities

### New Capabilities
(none)

### Modified Capabilities
- `plant-care-data`: the bundled list's content changes (different species), and each plant type gains toxicity, humidity preference and a propagation tip alongside light and watering interval.
- `plant-collection`: the card-click details view gains toxicity, humidity preference and propagation tip in addition to light and watering schedule.

## Impact

- `data/plants.json`: full replacement of entries (same schema shape, plus three new keys per entry).
- `app/providers/local_json.py` and `app/providers/base.py` (`PlantType`): add the three new fields to the parsed/typed plant record.
- `app/templates/_details.html`: show the three new fields.
- `tests/test_providers.py`: existing assertions about specific ids/fields (`monstera`, `pilea`, `len(raw) >= 40`, Monstera's `wiki_title`, Pilea's `watering_days`) must still hold against the new list, or be deliberately updated if the proposal's mapping changes any of them.
- `PLANNING_LOG.md`: every decided number/name/source along the way gets one line, per AGENTS.md.
