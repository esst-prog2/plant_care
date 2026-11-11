## 1. Research the 50-species data (no code yet)

- [x] 1.1 For each of the 15 new species, find light requirement and a watering-day estimate from general knowledge, consistent with the style of the existing 41 entries, and record them in a scratch table
- [x] 1.2 For each of the 50 species (new and carried-over), look up the real English Wikipedia article title and verify it live (actual HTTP request, not assumed) resolves to a page with a usable summary and photo, the same way the original 41-entry list was verified; record any title that needed adjusting from the first guess
- [x] 1.3 For each of the 50 species, look up the ASPCA toxic/non-toxic plant list and record one of "Toxic to pets", "Non-toxic to pets" or "Unknown/not evaluated" plus the ASPCA page checked (label set narrowed from the original 4-way plan, see PLANNING_LOG.md 2026-11-06)
- [x] 1.4 For each of the 50 species, write a humidity label (Low/Average/High) and a one-sentence propagation tip from general knowledge
- [x] 1.5 Append one line per decided number/name/source to PLANNING_LOG.md as the research is done (per AGENTS.md), not batched at the end

## 2. Build the new bundled list

- [x] 2.1 Write the new `data/plants.json` with all 50 entries (id, name, light, watering_days, wikipedia, toxicity, humidity, propagation), reusing the existing id/name/wikipedia/watering_days for the 35 carried-over species and the researched values for the 15 new ones, and verify it is valid JSON with no duplicate ids
- [x] 2.2 Verify the file still satisfies the existing pinned expectations: contains `monstera` and `pilea` ids, has at least 40 entries, Monstera's wikipedia is "Monstera_deliciosa", Pilea's watering_days is 7

## 3. Carry the new fields through the data layer

- [x] 3.1 Add `toxicity`, `humidity`, `propagation` to `PlantType` in `app/providers/base.py` and populate them in `app/providers/local_json.py`'s loader, and verify with a unit test that a loaded plant type exposes all three
- [x] 3.2 Add `toxicity`, `humidity`, `propagation` migrations to `_MIGRATIONS` in `app/db.py`, add the three fields to the `Plant` dataclass and `_to_plant`, and extend `complete_plant`'s signature and UPDATE statement to store them; verify `Database.init()` on a fresh db creates the columns and on an old db (missing columns) adds them without data loss
- [x] 3.3 Pass the three new fields from `service.get(...)`'s result through `app/main.py`'s `load_plant_data` into `db.complete_plant(...)`, and verify by adding a plant end-to-end (test or manual) that the stored row has non-null toxicity/humidity/propagation

## 4. Show the new fields in the UI

- [x] 4.1 Add toxicity, humidity and propagation rows to `app/templates/_details.html`'s `<dl>`, each falling back to "Not available" when null, and verify visually (via the `run` skill or manual browser check) that a newly-added plant shows all five fields and an old plant (added before this change) shows "Not available" for the three new ones without erroring

## 5. Update specs, tests and docs

- [ ] 5.1 Run `openspec archive update-plant-catalog` only after implementation and the user's sign-off (do not archive during this task list)
- [x] 5.2 Run the full test suite (`pytest`) and confirm it passes, updating any test in `tests/test_providers.py` or elsewhere whose fixed expectations about specific species were deliberately changed by this list swap (e.g. if a test hardcodes a removed id)
- [x] 5.3 Update the README wherever it names specific bundled species or describes the details view's fields, so it matches the new list and the three new fields
- [x] 5.4 Append a final PLANNING_LOG.md line summarizing the completed swap (count of species added/removed, confirmation that every Wikipedia title was live-verified)
