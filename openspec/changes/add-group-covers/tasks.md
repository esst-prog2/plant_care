## 1. Storage layer

- [ ] 1.1 Add an optional `prefix: str = ""` parameter to `store_uploaded_photo()` in `app/photos.py`, building the filename as `f"{prefix}{owner_id}{extension}"`; verify with a unit test that a prefixed and an unprefixed call for the same numeric id write different files without colliding
- [ ] 1.2 Add 8 preset SVG files under `app/static/group-presets/` (`leaf.svg`, `cactus.svg`, `succulent.svg`, `potted-plant.svg`, `flower.svg`, `vine.svg`, `fern.svg`, `palm.svg`), simple flat icons in the app's green palette; verify by opening each file directly in a browser and confirming it renders a distinct, recognizable motif at a small size

## 2. Database layer

- [ ] 2.1 Add a nullable `photo` column to `groups` via `_MIGRATIONS` in `app/db.py`; add it to the `Group` dataclass and `_to_group`; verify `Database.init()` adds the column to an old database without data loss
- [ ] 2.2 Extend `create_group(name, photo=None)` to accept an optional initial cover; add `set_group_photo(group_id, photo)`; extend `delete_group` to delete the group's uploaded cover file (path starting with `/photos/`) from disk before deleting the row, and to never touch a preset path (starting with `/static/`); verify with unit tests: creating a group with a photo stores it, `set_group_photo` changes it, deleting a group with an uploaded cover removes the file, deleting a group with a preset cover does not touch any file
- [ ] 2.3 Update `app/main.py`'s `_cover_photo(group_id)` to return the group's stored `photo` first when set, falling back to today's auto-derived-from-first-plant logic otherwise; verify with a test that a group with a stored cover shows it regardless of which plants it contains

## 3. Create-group flow with a cover picker

- [ ] 3.1 Build a shared cover-picker partial (8 preset thumbnails as radio inputs + a file input for upload) included by both `_new_group.html` and the edit-group form; verify it renders all 8 presets
- [ ] 3.2 Extend `POST /groups` to accept an optional `preset` field and an optional `photo` file upload (uploaded file wins if both are given); on an invalid upload, re-render the create-group form with the name field preserved and an inline error, without creating the group; verify with tests: creating with a preset, creating with a valid upload, creating with an invalid upload shows an error and creates nothing, creating with neither leaves the new group's cover auto-derived (unchanged current behavior)

## 4. Combined edit-group flow

- [ ] 4.1 Rename `_edit_group.html`'s button/heading from "Rename" to "Edit" for real groups only (not "All", which keeps "Rename", no cover section, per the stated non-goal); add the same cover-picker partial, pre-selecting the group's current preset if it has one; verify the "All" edit modal is unchanged (no cover section, button still says "Rename")
- [ ] 4.2 Extend `POST /groups/{group_id}/rename` to also accept the optional `preset`/`photo` fields and apply a cover change in the same request as the name change; on an invalid upload, keep the existing name unchanged too and show an inline error rather than partially applying the edit; verify with tests: changing only the name, changing only the cover (preset and upload), changing both together, an invalid upload leaving both name and cover unchanged

## 5. Verification

- [ ] 5.1 Run the full test suite (`pytest`) and confirm it passes
- [ ] 5.2 Manually verify in a real browser (throwaway db/photos dir, Playwright): create a group picking a preset and confirm its card shows that icon; create a second group uploading a real photo and confirm its card shows it; edit the first group to switch to an uploaded photo and confirm the card updates; edit the second group back to a different preset and confirm that too; delete the uploaded-cover group and confirm its photo file is gone from the photos directory

## 6. Wrap-up

- [ ] 6.1 Append PLANNING_LOG.md lines for decisions as they're implemented (the combined Edit action, the preset set chosen, the upload-wins-over-preset rule, the delete-time file cleanup), per AGENTS.md — not batched at the end
- [ ] 6.2 Update the README wherever it describes groups, to mention the cover picker
