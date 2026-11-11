## Context

Today `data/plants.json` has one row per plant type: `id`, `name`, `light`, `watering_days`, `wikipedia`. `app/providers/local_json.py` loads it into `PlantType` (`app/providers/base.py`), and `app/main.py`'s `load_plant_data` snapshots `light`/`interval_days` onto the `plants` row at add time via `Database.complete_plant` (`app/db.py`) — care data is never looked up live again after a plant is added, only the photo/description are (optionally) re-fetched. The `plants` table grows by additive, backward-compatible columns through the existing `_MIGRATIONS` dict in `app/db.py`, run on every `init()`.

See proposal.md for why the list is changing and why the three new fields are being added.

## Goals / Non-Goals

**Goals:**
- Swap `data/plants.json`'s content for the user's 50 species, each with a real, live-verified `wikipedia` title.
- Add `toxicity`, `humidity` and `propagation` to every one of the 50 entries, following the same "snapshot at add time, shown as a starting-point estimate" pattern as `light`/`watering_days`.
- Keep every already-added plant working: a plant of a type removed from the bundled list keeps its stored data and stays visible; it just can't be searched or added again.

**Non-Goals:**
- No live lookup of toxicity/humidity/propagation from any external API — all three are bundled, like light and watering already are.
- No change to the watering-estimate adjustment logic (`app/care.py`) — the new fields are informational only, not inputs to the interval calculation.
- No UI for editing these fields per-plant; they come from the bundled list only, same as today's light/watering.

## Decisions

**1. New fields live in `data/plants.json`, not fetched online.**
Toxicity, humidity and propagation are the same kind of fact as light and watering: general plant-level knowledge that doesn't vary per owned plant and that Wikipedia's summary endpoint doesn't reliably expose in a structured way. Keeping them in the bundled list keeps the data flow uniform (one local source for care facts, one online source for photo+description) instead of adding a second online dependency.

**2. Toxicity gets a cited source; humidity and propagation stay general-knowledge estimates.**
User decision (asked directly, since it changes how much verification work this change requires): toxicity for all 50 species is looked up against the ASPCA's published toxic/non-toxic plant list and recorded as such — this is a real safety fact (pets), not a scheduling preference, and the project already has precedent (HW4 spike) for not quietly presenting a guess as a fact. Humidity and propagation remain general-knowledge estimates, worded the same non-authoritative way `watering_days` already is in the README and the plant-collection spec ("starting-point estimate").

**3. Value format:**
- `toxicity`: short controlled label, one of `"Toxic to pets"`, `"Non-toxic to pets"`, `"Unknown/not evaluated"` — exactly ASPCA's own binary classification per plant page, not a severity grade of our own; ASPCA's pages do not publish a formal "mildly toxic" tier, and inventing one would mean judging symptom severity ourselves instead of quoting the source (decided with the user after finding this during research). Where the ASPCA list doesn't cover a species, the entry says so rather than guessing. Human toxicity is not separately tracked — the ASPCA list is pet-focused, and inventing a separate human-toxicity claim would reintroduce the same unverifiable-guess problem this decision is trying to avoid.
- `humidity`: short controlled label, one of `"Low"`, `"Average"`, `"High"` — scannable on the details view, consistent with how `light` is already a short phrase rather than a number.
- `propagation`: one short free-text sentence (e.g. "Stem cuttings in water root readily.") — propagation methods vary in wording enough that a fixed enum would lose real information; a single sentence stays scannable without needing a controlled vocabulary.

**4. Full backfill, no partial rollout.**
All 50 entries ship with all three new fields filled in in this same change; none are left null. A details view that shows "Toxicity: Not available" for most plants and real data for a handful would look broken, and the user has already signed up for the larger verification effort (confirmed: every Wikipedia title, old and new, gets a live-checked request before the list is finalized).

**5. Storage: three new nullable TEXT columns on `plants`, added the same way `about`/`photo_credit` were.**
`_MIGRATIONS` in `app/db.py` gets `toxicity`, `humidity`, `propagation` entries (`ALTER TABLE plants ADD COLUMN ... TEXT`). `Plant` (dataclass), `_to_plant`, `complete_plant` and `PlantType` all gain the three fields, mirroring exactly how `light`/`interval_days` already flow from the bundled list through `load_plant_data` into the stored row. Existing plants (added before this change) get `NULL` for all three new columns until removed and re-added — there's no retroactive backfill of already-stored plants, since the bundled-list snapshot model never re-applies catalog updates to existing rows (the same is true today if `light` or `watering_days` changes in the JSON for a type someone already added).

## Risks / Trade-offs

- **[Risk]** A removed bundled id (e.g. `umbrella-plant`) still exists on old plant rows and in old Google Tasks notes (`plant_care:<id>` markers use the plant's row id, not the type id, so this is not actually at risk) → Mitigation: type ids are only used for search/add, never stored as a foreign key the catalog must keep satisfying; removal is safe by construction, confirmed by reading `app/tasks_client.py`'s marker format.
- **[Risk]** ASPCA coverage gaps for less common genera (e.g. Guzmania, Beaucarnea) → Mitigation: use `"Unknown/not evaluated"` rather than inferring from a related genus.
- **[Risk]** `tests/test_providers.py` pins `monstera`/`pilea` ids, `len(raw) >= 40`, Monstera's `wiki_title`, Pilea's `watering_days == 7` → Mitigation: all four hold under the new list (both ids kept unchanged, 50 ≥ 40, Monstera and Pilea's wikipedia/watering values are unchanged carry-overs); tasks.md includes running the existing suite to confirm, not just asserting it from this table.
- **[Trade-off]** Existing plants added before this change show no toxicity/humidity/propagation (NULL) until re-added → accepted per Decision 5; the details template must render these fields as "Not available" rather than erroring on NULL, matching how `light` already handles a missing value today.

## Migration Plan

1. Add the three `_MIGRATIONS` entries in `app/db.py`; `init()` already applies missing migrations idempotently on every startup, so no separate migration script is needed.
2. Replace `data/plants.json` in one commit once every entry (new and carried-over) has a live-verified `wikipedia` title and all five care fields.
3. No rollback beyond `git revert` — the migration only adds nullable columns, so reverting the code change leaves harmless unused columns rather than breaking anything.
