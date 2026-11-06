## 1. Storage layer

- [x] 1.1 Add `store_uploaded_photo()` to `app/photos.py`: takes the uploaded file's bytes and content type, validates against the existing `MAX_BYTES`/`_EXTENSIONS` constants, deletes any existing file for that plant id with a different extension, writes the new file to `photos_dir / f"{plant_id}{extension}"`, and returns the web path or `None` on a validation failure; verify with a unit test covering a valid upload, a rejected type, an oversized file, and the old-extension-file-gets-deleted case
- [x] 1.2 Add the `photo_is_custom` migration to `_MIGRATIONS` in `app/db.py`, add the field to the `Plant` dataclass and `_to_plant`, and add a `Database.set_custom_photo(plant_id, photo_path)` method that sets `photo` and `photo_is_custom=1`; verify `Database.init()` adds the column to an old database without data loss (same style of check used in `update-plant-catalog`)

## 2. Route and wiring

- [x] 2.1 Add `POST /plants/{plant_id}/photo` to `app/main.py`: reuse `ready_plant()`, call `store_uploaded_photo()`, call `db.set_custom_photo()` on success, and re-render the details fragment either way (success shows the new photo, failure shows an inline error and the unchanged photo); verify with a test for a successful upload, a rejected type, an oversized file, and a 404 for an unready/unknown plant

## 3. UI

- [x] 3.1 Add an upload form (`<input type="file">` + submit, `hx-post`/`hx-encoding="multipart/form-data"`, targeting the details fragment) near the hero photo in `app/templates/_details.html`
- [x] 3.2 Update the credit line in `_details.html` to show `Text: Wikipedia` instead of `Photo and text: Wikipedia` when `card.plant.photo_is_custom` is truthy and a description is still present, and to show nothing extra when there is no description; verify with tests for: no upload yet (unchanged combined line), after upload with a description present (text-only line), after upload with no description (no credit line)
- [x] 3.3 Manually verify in a real browser (throwaway db/photos dir, `ONLINE_PHOTOS` off is fine): add a plant, open its details, upload a real image file, confirm the hero photo updates immediately and the card's photo updates after a grid refresh; then try an unsupported file type and confirm the existing photo stays and an error is shown

## 4. Wrap-up

- [x] 4.1 Run the full test suite (`pytest`) and confirm it passes
- [x] 4.2 Append PLANNING_LOG.md lines for decisions made along the way (the `photo_is_custom` column choice, the credit-line wording split, the delete-old-extension-file behavior) as they're implemented, per AGENTS.md — not batched at the end
- [x] 4.3 Update the README's "What comes next" list to remove the now-built "Own photo upload" line, and add a short mention of it under "Where the plant data comes from" or wherever fits, matching how other shipped features are documented
