## Context

`app/main.py`'s `_cover_photo(group_id)` always derives a group's cover from `db.list_plants(group_id=...)`'s first result's `.photo`, falling back to `/static/placeholder.svg`. `app/photos.py`'s `store_uploaded_photo(content, content_type, photos_dir, plant_id)` is the established upload path: validates against `MAX_BYTES`/`_EXTENSIONS`, writes to `photos_dir / f"{plant_id}{extension}"`. `app/main.py`'s plant photo-upload route appends a `?v=<secrets.token_hex(4)>` cache-busting suffix before storing the path, because a same-extension re-upload otherwise keeps the same URL and the browser serves a stale cached copy (a real bug hit and fixed earlier this session). `app/db.py` has one additive-migration mechanism (`_MIGRATIONS`) for new nullable columns on an existing table. See proposal.md for why covers are being added now.

## Goals / Non-Goals

**Goals:**
- A group's cover can be one of 8 built-in presets, or an uploaded photo, chosen at creation or later.
- When no cover has ever been chosen, behavior is unchanged (auto-derived from the first plant).
- Reuse the plant photo-upload path's validation and cache-busting rather than reinventing it.

**Non-Goals:**
- Cover customization for "All" — not asked for; stays auto-derived only.
- Multiple images per group, image cropping/editing, or reordering the preset picker.
- Any way to revert a group's cover back to "auto" once one has been chosen (mirrors plant photo upload, which also has no revert).

## Decisions

**1. One combined "Edit group" action replaces the rename-only flow.**
A group only has two editable things — its name and its cover — so a second button for cover-only editing would be more UI than the feature warrants. `_edit_group.html`'s button is renamed "Rename" → "Edit", and its form gains the same cover-picker partial used at creation, submitting name and cover together to `POST /groups/{group_id}/rename` (kept as the endpoint name since it's the group's one settings-save action, not renamed to avoid breaking the already-shipped "All" rename, which has no cover section and keeps posting the same way). "All"'s edit flow is untouched — same button label "Rename", same endpoint, no cover section, per the stated non-goal.

**2. 8 built-in presets, as static SVG files under `app/static/group-presets/`, referenced by filename, not a database enum.**
`leaf.svg`, `cactus.svg`, `succulent.svg`, `potted-plant.svg`, `flower.svg`, `vine.svg`, `fern.svg`, `palm.svg` — simple flat icon tiles in the app's green palette (matching the existing logo's visual language), each a visually distinct motif so they're tellable apart at card-thumbnail size. A file-based set means adding a 9th later is dropping in one file and one `<option>`, not a migration.

**3. `groups.photo` (nullable TEXT) holds either a preset's static path (`/static/group-presets/leaf.svg`) or an uploaded photo's path (`/photos/group-{id}{ext}?v=...`) — one column, no "kind" flag.**
The two are told apart by path prefix alone when it matters (deletion, below); nothing in the UI needs to know which one is active, unlike plants' `photo_is_custom` (which exists only to steer the Wikipedia credit line — groups have no such credit line to toggle).

**4. `store_uploaded_photo()` gains an optional `prefix: str = ""` parameter; a group's file is saved as `group-{group_id}{extension}`.**
A plant and a group can share the same numeric id, and both write into the same `photos_dir`; without a distinguishing prefix a plant's upload and a group's upload could silently overwrite each other. The existing plant upload call site passes no prefix (unchanged filenames, no migration of existing files needed).

**5. Choosing both a preset and uploading a file in the same submission: the uploaded file wins.**
An upload is a stronger, more specific signal of intent than leaving a preset radio at its default-selected value; silently preferring whichever happened to be submitted last would be harder to predict.

**6. Deleting a group deletes its uploaded cover file, but never a preset's static asset.**
`Database.delete_group` already nulls out its plants' `group_id` before deleting the row; the same method now also checks the outgoing `photo` value, and if it starts with `/photos/` (an upload, not a preset under `/static/`), deletes that file from disk first — otherwise every deleted group with a custom photo would leave an orphaned file behind forever, which this project has been careful to avoid elsewhere (the same-extension re-upload fix earlier this session existed specifically because of this kind of attention).

## Risks / Trade-offs

- **[Risk]** A group created before this change has `photo` as `NULL` after the migration → Mitigation: `_cover_photo()`'s fallback path is unchanged, so every existing group keeps showing its auto-derived cover exactly as before.
- **[Trade-off]** No revert-to-auto control once a cover is chosen → accepted, matching the plant photo-upload precedent's same trade-off.

## Migration Plan

1. Add the `photo` column to `groups` via `_MIGRATIONS`; applies idempotently on every `init()`.
2. Add the 8 preset SVG files to `app/static/group-presets/` — pure additions, no migration needed.
3. No data backfill: existing groups simply keep `photo = NULL` (today's auto-derived behavior).
