## Context

`app/photos.py`'s `store_photo()` downloads a *remote* image and saves it to `config.photos_dir / f"{plant_id}{extension}"`, returning the web path `/photos/{plant_id}{extension}`; it is only ever called once, from `app/main.py`'s background `load_plant_data`, right after a plant is created. `Plant.photo` (the stored web path) is never touched again afterwards by any existing code path — there is no re-fetch, no sync, nothing. So "the user's photo takes priority over the Wikipedia photo" is not a race to arbitrate: it is simply "the upload action, once added, is the only thing from here on that can change `photo`." `Plant.photo_credit` is a URL shown in `_details.html` as `Photo and text: <a href="...">Wikipedia</a>` — one combined line for both the picture and the description text, because today they always come from the same place.

See proposal.md for why this is being added.

## Goals / Non-Goals

**Goals:**
- Let the user replace the displayed photo for an already-added, `READY` plant with their own image file.
- Reuse the existing storage location, filename scheme, size cap and allowed file types from `app/photos.py` rather than introducing a second set of rules.
- Stop implying the replaced photo is "Wikipedia's" once a user photo is active, without losing the (still valid) text attribution for the Wikipedia description.

**Non-Goals:**
- Reverting to the Wikipedia photo or placeholder after a user photo is uploaded.
- Cropping, resizing in the UI, or otherwise editing the uploaded image beyond what's needed to store it.
- Choosing a photo at add time, before the plant exists.
- Re-validating or re-encoding the image beyond the existing content-type/size checks (no virus scanning, no dimension checks).

## Decisions

**1. New column `photo_is_custom` (INTEGER/boolean, default 0) on `plants`.**
Added via the existing `_MIGRATIONS` mechanism in `app/db.py` (same pattern used for `toxicity`/`humidity`/`propagation`). Repurposing `data_source` (`online`/`local`/`local-fallback`) was considered and rejected: that field describes the outcome of the *add-time* care-data lookup, and overloading it with a later, unrelated mutation (a manual photo replacement) would make `data_source` mean two different things depending on when it's read. A dedicated boolean is clearer and keeps `data_source` as a historical record of how the plant was added.

**2. `_details.html`'s credit line splits on `photo_is_custom`.**
- `photo_is_custom` false (today's existing behavior, unchanged): if `photo_credit` is set, show `Photo and text: Wikipedia`.
- `photo_is_custom` true: if `about`/`photo_credit` are still set (the description came from Wikipedia and is still shown), show `Text: Wikipedia` instead — the photo credit no longer applies, but the description's attribution still does.

**3. New route `POST /plants/{plant_id}/photo`, multipart form field `photo`.**
Reuses `ready_plant()` (404 for an unknown or not-yet-`READY` plant, matching `Watered`/`Remove`). On success: stores the file, sets `photo` to the new web path, sets `photo_is_custom = 1`, and re-renders the plant's details fragment (hero image updates immediately, same `hx-target` pattern as the rest of the app). On validation failure (wrong content type or over the size cap): re-renders the same details fragment with an inline error message near the upload control — not a generic error page, not a silent no-op — and leaves the existing photo untouched.

**3a. The stored `photo` path carries a cache-busting query token on every upload.**
Found during a live check: when the new upload keeps the same extension as what it replaces (the common case, since most uploads are `.jpg`/`.png` like the original Wikipedia photo), the web path is byte-for-byte identical to before, so the browser's own image cache keeps showing the old picture even though the file on disk changed. `app/main.py`'s upload route appends `?v=<8 hex chars>` (`secrets.token_hex(4)`) to the path it passes to `set_custom_photo`, so the URL always changes. A wall-clock timestamp was considered and rejected: Windows' clock resolution can repeat within a millisecond for two quick uploads, which is exactly the scenario a regression test needs to cover reliably.

**4. `app/photos.py` gets a new `store_uploaded_photo()` function, not a change to `store_photo()`.**
Both end up writing to the same `photos_dir / f"{plant_id}{extension}"` path and share the `MAX_BYTES` and `_EXTENSIONS` constants, but their inputs are different enough (an `httpx` response to download vs. an already-received `UploadFile`'s bytes) that one function branching on which it got would be harder to read than two small functions sharing the same constants and naming scheme.

**5. Replacing an existing file for the same plant id deletes the old one first if its extension differs.**
E.g. a plant whose Wikipedia photo was `3.jpg` gets a `.png` upload: the new file is saved as `3.png` and the stale `3.jpg` is deleted, so `photos_dir` doesn't accumulate orphaned files for a plant that changes photo format. If the extension is the same, the upload simply overwrites the existing file.

## Risks / Trade-offs

- **[Risk]** A plant added before this change has `photo_is_custom` as `NULL` (not `0`) after the migration, since `ALTER TABLE ... ADD COLUMN` can't backfill a default for pattern consistency with other additive migrations in this codebase (e.g. `about`, `photo_credit` are also `NULL`-default, not empty-string-default) → Mitigation: the template checks truthiness (`if card.plant.photo_is_custom`), so `NULL`/`0`/missing are all treated the same as "not custom," which is the correct behavior for every existing plant.
- **[Trade-off]** No way to undo an upload in this change (stated non-goal) → accepted; the user can still remove and re-add the plant to get the Wikipedia photo back, which is a real (if clunky) escape hatch already provided by the existing Remove action.

## Migration Plan

1. Add the `photo_is_custom` migration to `app/db.py`'s `_MIGRATIONS`; applied idempotently on every `init()`, same as the three columns added in `update-plant-catalog`.
2. No data backfill needed — see the risk note above.
