## Why

A group's cover image currently always auto-derives from its first-added plant's photo, with no way to pick something else. The user wants to choose a cover — either a built-in preset icon or their own uploaded photo — both when creating a group and later by editing it, the same flexibility plants already have for their own photo.

## What Changes

- 8 built-in preset cover icons (plant/nature motifs, matching the app's existing visual language) that can be picked for a group's cover.
- A group's cover can also be a user-uploaded photo, validated the same way a plant photo upload is.
- Both the preset picker and the upload control are available when creating a new group, and later from one combined "Edit group" action (renamed from "Rename") that handles the name and the cover together.
- When neither a preset nor a photo has ever been chosen, the cover keeps auto-deriving from the group's first plant, exactly as it works today.
- Out of scope: cover customization for "All" (the user's request was specifically about creating a group); multiple covers per group; reordering or deleting individual presets from the picker.

## Capabilities

### Modified Capabilities
- `plant-groups`: group creation and the group-edit flow gain a cover picker (preset or upload); a stored cover takes priority over the automatic first-plant-photo fallback.

## Impact

- `app/db.py`: new nullable `photo` column on `groups` (via the existing `_MIGRATIONS` pattern); `create_group()` gains an optional initial cover; new `set_group_photo(group_id, photo)`.
- `app/photos.py`: `store_uploaded_photo()` gains an optional filename `prefix` parameter so a group's upload (`group-{id}{ext}`) can't collide with a plant's (`{id}{ext}`) in the same `photos_dir`.
- `app/main.py`: `_cover_photo()` checks the stored `groups.photo` first, falling back to today's auto-derived logic; `POST /groups` accepts an optional preset choice or uploaded file; a new combined cover-and-rename flow replaces the rename-only one; group deletion removes an uploaded cover file (never a preset's static asset).
- New static assets under `app/static/group-presets/` (8 SVG icons).
- Templates: `_new_group.html` and `_edit_group.html` gain a shared cover-picker partial.
