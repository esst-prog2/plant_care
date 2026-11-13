## 1. Shared header partial

- [ ] 1.1 Create `app/templates/_header.html`: the logo/wordmark (reusing the exact existing `.logo`/leaf-SVG markup from `index.html`/`collection.html`/`upcoming.html`) plus a pill-style nav with two links — "Groups" (`href="/"`) and "Upcoming" (`href="/upcoming"`) — where the one matching the `active_nav` variable (`"groups"` or `"upcoming"`) gets an `active` class; verify by rendering it with each value and checking which link carries the class
- [ ] 1.2 Add `.app-bar`, `.app-nav`, `.app-nav a.active` styles to `app/static/style.css` using the existing palette (`--green` filled pill for the active destination, `--muted` text with no background for the inactive one), matching the validated mockup

## 2. Page toolbar row

- [ ] 2.1 Add a `.page-toolbar` style to `app/static/style.css` (flex row, `flex-wrap: wrap`, matching the existing `.topbar` spacing) for each page's own relocated controls

## 3. Wire up each page

- [ ] 3.1 In `index.html`, set `active_nav = "groups"`, include `_header.html`, and move the "+ New Group" button into a `.page-toolbar` row below it; remove the old `.nav-link` "Upcoming" link and the old inline logo markup (now owned by `_header.html`)
- [ ] 3.2 In `collection.html`, set `active_nav = "groups"`, include `_header.html`, and move the group-switch `<select>` and "+ Add New Plant" button into a `.page-toolbar` row below it; remove the old `.back` link, the old `.nav-link` "Upcoming" link, and the old inline logo markup — keep every existing `hx-get`/`onchange`/id attribute on the relocated controls unchanged
- [ ] 3.3 In `upcoming.html`, set `active_nav = "upcoming"`, include `_header.html`, and move the group-filter `<select>` (and the `#upcoming-group-input` hidden input) into a `.page-toolbar` row below it; remove the old `.back` link and the old inline logo markup
- [ ] 3.4 Grep `app/templates/` for `class="back"` and `class="nav-link"` to confirm zero remaining usages, then delete the now-unused `.back` and `.nav-link` rules from `app/static/style.css`

## 4. Tests

- [ ] 4.1 Add tests asserting the persistent nav's active-state: on `/` and on a scoped `/groups/{id}` view, "Groups" carries the active indicator and "Upcoming" does not; on `/upcoming`, the reverse
- [ ] 4.2 Run the existing `test_upcoming_reachable_from_landing_page` / `test_upcoming_reachable_from_a_collection_view` tests and confirm they still pass unmodified (the new pill nav still renders `href="/upcoming"`)

## 5. Verification

- [ ] 5.1 Run the full test suite (`pytest`) and confirm it passes
- [ ] 5.2 Manually verify live (throwaway db, Playwright) on all three pages: the persistent nav shows the right active destination, every relocated control (group select/filter, "+ New Group", "+ Add New Plant") still works exactly as before, navigating via the "Groups"/"Upcoming" pills works, and the layout doesn't overflow or wrap awkwardly at a narrow (~375px) viewport width

## 6. Wrap-up

- [ ] 6.1 Append a PLANNING_LOG.md line for this change once implemented, per AGENTS.md
