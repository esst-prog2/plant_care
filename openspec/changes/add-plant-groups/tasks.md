## 1. Database layer

- [x] 1.1 Add the `groups` table to `_SCHEMA` and the `group_id` column to `_MIGRATIONS` in `app/db.py`; add `group_id` to the `Plant` dataclass and `_to_plant`; verify `Database.init()` creates both on a fresh db and adds the column to an old db without data loss (same style of check used in earlier changes)
- [x] 1.2 Add `Database` methods: `create_group(name) -> Group`, `list_groups() -> list[Group]`, `get_group(id) -> Group | None`, `rename_group(id, name)`, `delete_group(id)` (nulls `group_id` on that group's plants, then deletes the group row, in one transaction), `set_plant_group(plant_id, group_id | None)`, and `list_plants(group_id=None)` extended with an optional group filter (default `None` = every plant, unchanged behavior); `count_plants()` left unscoped since nothing needs a per-group count beyond `len(list_plants(group_id=...))`, which the landing page uses instead; verify each with unit tests (`tests/test_groups.py`), including that deleting a group leaves its former plants present and unassigned

## 2. Landing page and group CRUD

- [x] 2.1 Add `GET /` as the landing page: an "All" card with the total plant count, one card per group with its name and plant count, and a "+ New Group" control; new template; verify with a test for zero groups and for two groups with different plant counts
- [x] 2.2 Add `POST /groups` (create) wired to "+ New Group"; verify a new group appears on the landing page with a zero count
- [x] 2.3 Add `GET /groups/{id}/edit` (rename form into `#modal`) and `POST /groups/{id}/rename`; verify the landing page reflects the new name and the group's plants are unaffected
- [x] 2.4 Add `GET /groups/{id}/confirm-delete` and `POST /groups/{id}/delete`, mirroring `_confirm_remove.html`'s pattern; verify deleting a group removes its card but its former plants still show under "All" with no group (cancelling is a client-side-only no-op, same as the existing plant-removal confirm, so not separately tested, matching that existing untested case)

## 3. Scoped collection view

- [x] 3.1 Add `GET /groups/all` and `GET /groups/{group_id}` (registered in that order so "all" is never parsed as an id) rendering the existing 3×2 paged grid scoped to that group, with a small header bar: back arrow to `/`, a `<select>` to switch directly to another group or "All" (`onchange="location.href=this.value"`), and the existing "+ Add New Plant" control; verify opening a group shows only its plants and opening "All" shows every plant
- [x] 3.2 Extend `GET /grid` with an optional `view_group_id` query param (default `"all"`), and update `_grid.html`'s pager links to carry the current `view_group_id` through; verify pagination is computed independently per group (a group with 7 plants pages correctly regardless of how many plants exist elsewhere), and verify every existing call to `/grid` or `/` without a `view_group_id` still behaves exactly as before (param named `view_group_id`, not `group_id`, to stay distinct from the plant-assignment field of the same name elsewhere)

## 4. Assigning and moving a plant's group

- [x] 4.1 Add an optional group `<select>` to `_confirm_add.html` (listing every existing group plus "Unassigned") and a `group_id` form field to `POST /plants`; verify adding a plant with a group selected puts it under that group and under "All," and adding one without a selection puts it only under "All"
- [x] 4.2 Add a "move to group" form to `_details.html`, next to the existing photo-upload form, posting to a new `POST /plants/{plant_id}/group`; verify changing a plant's group moves it between the old and new group's scoped views and leaves it under "All" throughout, and verify choosing "Unassigned" removes it from any group

## 5. Verification

- [x] 5.1 Run the full test suite (`pytest`) and confirm it passes
- [x] 5.2 Manually verify in a real browser (throwaway db/photos dir, Playwright): create a group, add a plant assigned to it, confirm the landing page's count updates, open the group and confirm only that plant shows, switch to "All" via the dropdown and confirm every plant shows, move the plant to a different group from its details view, delete the first group and confirm the plant still appears under "All" with no group

## 6. Wrap-up

- [ ] 6.1 Append PLANNING_LOG.md lines for decisions as they're implemented (the `groups` table vs. a `_MIGRATIONS` column, the delete-nulls-group_id behavior, the plain-`<select>` switch control), per AGENTS.md — not batched at the end
- [x] 6.2 Update README: remove "room-based plant organization" from the "Not this term" list (now built), keep "room-specific to-do lists" listed there as still deferred, and add a short description of groups under a relevant section
