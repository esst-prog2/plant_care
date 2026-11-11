## Why

The user wants to organize plants into their own named groups (e.g. by room), something the README explicitly deferred in week one ("Not this term: room-based plant organization"). With the core features now built, there's room to take this on before the project wraps up.

## What Changes

- A new landing page becomes the app's entry point: an "All" card plus one card per user-created group, each showing a plant count, with a "+ New Group" control.
- Clicking a card opens today's 3×2 paged grid, now scoped to that group's plants ("All" behaves exactly like today's homepage). Inside that view, a back arrow returns to the landing page and a dropdown switches directly to a different group without going back first.
- Groups can be renamed and deleted after creation. Deleting a group does not delete its plants — they become unassigned (fall back into "All").
- Adding a plant gains an optional group choice in the existing confirm-add step; a plant's group can also be changed later from its details view. A plant belongs to at most one group at a time.
- Room-specific Google Calendar reminders remain explicitly out of scope (README's other deferred item; unaffected by this change).

## Capabilities

### New Capabilities
- `plant-groups`: user-created, named groups that plants can be organized into — the landing page, group create/rename/delete, switching between a group's scoped collection view and another group or "All", and assigning/moving a plant's group.

### Modified Capabilities
- `plant-collection`: the "Homepage shows plants as cards in a paged grid" requirement is renamed and reworded — the paged 3×2 grid is no longer the app's first screen, and pagination/card counts are now scoped to whichever group (or "All") is being viewed, instead of always covering every plant.

## Impact

- `app/db.py`: new `groups` table (id, name) in `_SCHEMA`; new nullable `group_id` column on `plants` via the existing `_MIGRATIONS` pattern; `list_plants()` gains an optional group filter; new CRUD methods for groups and for moving a plant's group.
- `app/main.py`: new landing-page route, group CRUD routes, a group-scoped collection route, and an optional `group_id` on the existing `/grid` fragment route; the add-plant form and route gain an optional group field; a new route to change a plant's group from its details view.
- New templates for the landing page, group cards, new/rename-group forms, and a confirm-delete step (mirroring `_confirm_remove.html`); `_grid.html`'s pager links and `_confirm_add.html`/`_details.html` gain group-related controls.
- `tests/test_web.py` (or a new `tests/test_groups.py`) and a live browser check for the new landing page and group-switching flow.
