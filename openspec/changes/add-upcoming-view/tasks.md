## 1. Backend: aggregate and sort

- [ ] 1.1 In `app/main.py`, add a helper that builds the Upcoming list: for a given `group_id` (or `None` for "All"), call `db.list_plants(group_id=...)`, drop any plant where `card_view(plant, today)["loading"]` is true, build each row from `card_view()` plus the plant's group name (via `db.list_groups()`/`get_setting(ALL_GROUP_NAME_KEY, ...)` for unassigned), then sort ascending by `plant_days_left(plant, today)`; verify with a unit test that overdue/due-today/future plants come out in the right order and a loading plant is excluded
- [ ] 1.2 Add `GET /upcoming` accepting `view_group_id: str = "all"` (same convention as `/grid`/collection views, via the existing `_parse_view_group_id` helper), rendering the new template with the sorted rows, the current `view_group_id`, and the list of groups for the filter `<select>`; verify with a test that it returns 200 and lists plants sorted correctly

## 2. Template: the Upcoming page

- [ ] 2.1 Create `app/templates/upcoming.html` extending `base.html`, with a topbar (back arrow to `/`, a group-filter `<select>` matching `collection.html`'s switch-group pattern exactly — `onchange="location.href=this.value"`, options built from `/upcoming?view_group_id=...`, plus the logo) and a list of rows (plant name, group name, status label, same color convention as the existing `.badge` classes); verify by rendering it for a db with plants in different states and checking the HTML order and labels
- [ ] 2.2 Handle the empty state (no plants ready yet) with a message consistent with the existing "No plants yet" wording used elsewhere; verify with a test

## 3. Reachable from everywhere

- [ ] 3.1 Add an "Upcoming" link to `index.html`'s existing topbar; verify it's present in the landing page's HTML and links to `/upcoming`
- [ ] 3.2 Add an "Upcoming" link to `collection.html`'s existing topbar; verify it's present in a scoped collection view's HTML and links to `/upcoming`

## 4. Styling

- [ ] 4.1 Add list/row styles to `app/static/style.css` using the existing palette (`--green`, `--red`, `--muted`, `--line`), reusing the existing `.badge`/`.badge.ok`/`.badge.due`/`.badge.overdue` classes for the status labels rather than inventing new ones

## 5. Verification

- [ ] 5.1 Run the full test suite (`pytest`) and confirm it passes
- [ ] 5.2 Manually verify in a real browser (throwaway db, Playwright): several plants across two groups in different due states, confirm the Upcoming view's order, confirm filtering by group works, confirm the link is reachable from both the landing page and a collection view, confirm the empty state when no plants are ready

## 6. Wrap-up

- [ ] 6.1 Append a PLANNING_LOG.md line for this change once implemented, per AGENTS.md
