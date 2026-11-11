## Context

Today `GET /` renders `index.html` with a 3×2 paged grid over every plant (`db.list_plants()`, no filter), and `GET /grid?page=N` re-renders just that grid fragment for pagination/HX-Trigger refreshes. `app/db.py` has one table (`plants`) and an additive-column migration pattern (`_MIGRATIONS`); there is no second table yet. Every existing modal flow (add, confirm-add, details, photo upload, confirm-remove) renders into the single `#modal` div in `base.html`. See proposal.md for why groups are being added now.

## Goals / Non-Goals

**Goals:**
- A landing page as the new entry point, with per-group plant counts.
- Full group CRUD (create, rename, delete) without ever deleting a plant.
- The existing grid/pagination behavior, now scoped to whichever group (or "All") is being viewed.
- A plant's group assignable at add time and changeable later, single group at a time.

**Non-Goals:**
- Multiple groups per plant.
- Room-specific Google Calendar reminders (README's other, still-deferred "Not this term" item) — unaffected by this change.
- Reordering/sorting groups on the landing page, or any drag-and-drop; groups list in creation order.
- Any import/export or bulk re-assignment of plants between groups.

## Decisions

**1. Routes.**
- `GET /` — the new landing page (groups overview).
- `GET /groups/all` and `GET /groups/{group_id}` — the existing 3×2 paged grid, scoped to all plants or to one group. The literal `/all` path is registered before `/{group_id}` in `app/main.py`, the same ordering trick already used for `/plants/confirm` vs `/plants/{plant_id}`, so "all" is never parsed as a group id.
- `GET /grid?group_id=<id-or-"all">&page=N` — the existing paged-grid fragment, now taking an optional `group_id` (defaulting to `"all"` so every current caller/test that omits it keeps working unchanged).
- `POST /groups` (create), `GET /groups/{id}/edit` + `POST /groups/{id}/rename`, `GET /groups/{id}/confirm-delete` + `POST /groups/{id}/delete` — group CRUD, mirroring the existing confirm-add/confirm-remove modal pattern.
- `POST /plants/{plant_id}/group` — change a plant's group from its details view (`group_id` form field, empty/omitted means unassign).
- `POST /plants` (add-plant) gains an optional `group_id` form field, same optional-with-default-0/empty pattern as `light_delta`/`warmth_delta`/`pot_delta`.

**2. Schema: a new `groups` table, not a `_MIGRATIONS` column.**
`_MIGRATIONS` only ever adds columns to the existing `plants` table; a second table is new territory. `_SCHEMA` gets a second `CREATE TABLE IF NOT EXISTS groups (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL)` statement (`executescript` already runs multiple statements). `plants` gains a nullable `group_id INTEGER` column via the normal `_MIGRATIONS` entry — no `FOREIGN KEY` constraint, consistent with this codebase's existing style (SQLite doesn't enforce FKs here by default, and no other column uses one either); the application layer is the only thing that keeps `group_id` meaningful.

**3. Deleting a group nulls out its plants' `group_id`, in the same transaction as the delete.**
Chosen default, called out here per the user's own request to confirm it: `Database.delete_group(group_id)` runs `UPDATE plants SET group_id=NULL WHERE group_id=?` then `DELETE FROM groups WHERE id=?` inside one `with closing(...) as conn, conn:` block, so a deleted group's plants simply fall back into "All" — never deleted themselves, matching this project's general caution around destructive actions.

**4. "Move to group" lives in the plant's details view, next to the existing photo-upload form.**
Same small-inline-form pattern already established there. The selector offers every existing group plus an "Unassigned (All only)" option; it is also the exact control reused (pre-filled, optional) in `_confirm_add.html` at add time, so there is only one piece of markup logic for "pick a group" to maintain, not two.

**5. The in-group dropdown lists every other group plus "All", and sits beside the back arrow in a new small header bar above the grid.**
E.g. `[&larr; All groups]  [Switch to: <select>]  [+ Add New Plant]`. The `<select>` is plain HTML (`onchange="location.href=this.value"`), not htmx, since it's a full navigation to a different scoped view rather than a fragment swap — simpler than wiring a new htmx target for what is just "go to this other URL."

**6. Landing-page cards show the group's name and its plant count** (`SELECT COUNT(*) FROM plants WHERE group_id=?`, and total plant count for "All"). Cheap to compute, and a bare name-only card would raise the obvious question "how many plants are in here" with no answer on screen.

**7. Rename and delete are modal flows (`GET .../edit`, `GET .../confirm-delete`), not inline-on-card editing.**
Consistent with every other mutation in this app happening in `#modal` (add, confirm-add, details, confirm-remove) — an inline-edit card would be the first exception to that pattern for no real benefit here.

## Risks / Trade-offs

- **[Risk]** Existing tests/calls to `GET /grid` and `GET /` without any group parameter must keep returning every plant, unscoped → Mitigation: `group_id` defaults to `"all"` everywhere it's read, so omitting it is indistinguishable from explicitly asking for "All."
- **[Trade-off]** No many-to-many grouping, so a plant that's conceptually in two rooms needs two separate app entries today anyway (unrelated to this change) or picking one group → accepted per the user's own choice of single-group membership over flexibility.
- **[Risk]** A plant's `group_id` pointing at a deleted group would silently show it nowhere if deletion didn't null it out first → Mitigated by Decision 3's same-transaction null-out.

## Migration Plan

1. Add the `groups` table to `_SCHEMA` and the `group_id` column to `_MIGRATIONS`; both apply idempotently on every `init()`, same as every previous additive change this project has made.
2. No data backfill: existing plants simply start with `group_id = NULL` (unassigned, visible under "All," exactly as they are today).
3. Rollback is a plain `git revert`; the added table/column are inert if the code reverts, nothing else depends on them.
