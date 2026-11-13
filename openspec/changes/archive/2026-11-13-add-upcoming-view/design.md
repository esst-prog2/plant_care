## Context

`app/care.py`'s `plant_days_left(plant, today)` already returns `None` for a plant that isn't `READY` yet, and otherwise a signed day count (negative = overdue, 0 = due today, positive = days left) — exactly the sort key this view needs, with no extra status-priority logic required. `app/main.py`'s `card_view(plant, today)` already turns that into the same `label` text used on every card ("Watering: Due today!", "N days overdue", "N days left"), and `db.list_plants(group_id=...)` already supports the "All"/scoped filtering this view reuses. `index.html` and `collection.html` each define their own `<header class="topbar">` independently (no shared nav partial exists yet in `base.html`). See proposal.md for motivation.

## Goals / Non-Goals

**Goals:**
- Reuse `plant_days_left`/`card_view`'s existing label wording and the existing `group_id`/"All" filtering convention exactly, rather than inventing new status text or a second filtering mechanism.
- Make the view reachable the same way from both pages that have a topbar today.

**Non-Goals:**
- No new persistent nav component/partial shared across templates — out of scope for the size of this change. Each topbar gains its own "Upcoming" link, the same way each already has its own page-specific buttons.
- No pagination on the Upcoming list in this change; a single user's plant count is small enough (the existing grid pages at 6 per page, but an aggregate list reads fine unpaged for realistic collection sizes). Revisit if this becomes a problem.
- No change to Google Calendar sync behavior; this view reads the same local `plants` data the sync already reads from, independently.

## Decisions

**1. Sort key is the plain signed `days_left` value, ascending.**
`plant_days_left` already returns negative-for-overdue, 0-for-due-today, positive-for-future. Sorting the ready plants by that number ascending produces exactly the required order (most overdue first, then due today, then soonest-future) with no separate priority mapping. Alternative considered: bucket into overdue/due/upcoming groups first, then sort within each — rejected as unnecessary complexity when a single numeric sort already gives the right order.

**2. New route `GET /upcoming`, accepting the same `view_group_id` convention as `/grid` and the collection views.**
Mirrors `_parse_view_group_id` (`"all"` → `None`, else the int group id) already used by `collection_view`/`grid`. No new filter concept, no new query-param name. Alternative considered: a `group_id` path segment like `/groups/{id}`'s own pattern — rejected to keep the "all plants, optionally scoped" nature of this view distinct from the groups-as-pages routes it is not one of.

**3. Each row is built from the existing `card_view()` dict plus the plant's group name, not a new serialization.**
`card_view(plant, today)` already computes `label`, `status`, `days`, `is_due` consistently with every card on the site. The Upcoming route builds the list, sorts it, and resolves each plant's `group_id` to a name (or the "All" setting name when unassigned) via the existing `db.list_groups()`/`get_setting(ALL_GROUP_NAME_KEY, ...)`. No new per-plant computation beyond that lookup.

**4. "Upcoming" is added as one more link in each template's own existing `<header class="topbar">`, not a new shared nav partial.**
`index.html` and `collection.html` already each define their own topbar with page-specific buttons ("+ New Group", "+ Add New Plant") plus the shared logo. Adding one more link to each is a two-line change in each template; introducing a shared nav partial/include would touch `base.html` and both templates for a single added link, which is more restructuring than this change's scope justifies. Revisit if a third page needs the same link later.

**5. The Upcoming view's own topbar gets a back arrow (`href="/"`) and no group-switch `<select>`, since group filtering here uses its own mechanism (see Decision 6), not the existing collection-view switcher.**
Keeps the page visually consistent with `collection.html`'s back-arrow pattern without implying it's a collection view scoped to one group's grid.

**6. Group filtering on the Upcoming view uses a `<select>` that reloads the page via `location.href`, matching `collection.html`'s existing group-switch control exactly (same markup pattern, `view_group_id` values).**
Consistent with an established, already-working pattern in this codebase rather than introducing HTMX-driven filtering for a page that's a full reload anyway when switching groups elsewhere.

## Risks / Trade-offs

- **[Risk]** A user with many plants could make the unpaged list long. **Mitigation:** accepted for now (Non-Goals); the existing grid's 6-per-page cards already demonstrate collections here are small in practice, and an unpaged *list* (not cards) comfortably holds more rows per screen than a card grid does.
- **[Trade-off]** No shared nav partial means two templates to update if a future page needs the same "Upcoming" link a third time. Accepted: two call sites don't justify a refactor; revisit at three.
