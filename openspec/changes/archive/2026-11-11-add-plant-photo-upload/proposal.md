## Why

The plant's photo is currently always whatever Wikipedia supplies (or a placeholder if that fails) — there is no way to show the user's own plant instead of the species' generic Wikipedia picture. This was already named as a planned next step in the README ("Own photo upload for each plant, which would take priority over the Wikipedia photo") but never designed or built.

## What Changes

- Add a photo-upload control to the plant's details view, letting the user replace the shown photo (Wikipedia photo or placeholder) with their own image file, for a plant that has already been added.
- The uploaded photo is stored the same way an automatically-downloaded photo is (same directory, same per-plant filename scheme, same allowed types and size cap), so it is served and persists exactly like today's photo.
- Once a user photo is uploaded, the Wikipedia photo credit line no longer applies and stops being shown for that plant.
- Out of scope for this change: removing an uploaded photo (reverting to the Wikipedia photo or placeholder), editing/cropping the image, and choosing a photo before the plant exists (at add time).

## Capabilities

### New Capabilities
- `plant-photo-upload`: lets the user upload their own photo for an existing plant, replacing whatever photo is currently shown, with validation for file type, size and plant readiness.

### Modified Capabilities
(none — the existing capabilities' stated requirements are unchanged; `plant-care-data`'s "fetched data is stored with the plant" requirement is about the automatic Wikipedia fetch and is not altered by a later manual replacement)

## Impact

- `app/main.py`: new route, e.g. `POST /plants/{plant_id}/photo`.
- `app/photos.py`: a new function alongside `store_photo()` for saving an uploaded file (reusing its `MAX_BYTES` and allowed-content-type constants rather than duplicating them).
- `app/templates/_details.html`: a small upload form near the hero photo; the Wikipedia credit line's visibility becomes conditional on there being no user photo.
- `app/db.py`: no schema change expected (reuses the existing `photo` column); `data_source` may need a new value or an existing one repurposed to represent "user-uploaded" so the credit line can be hidden correctly — decided in design.md.
