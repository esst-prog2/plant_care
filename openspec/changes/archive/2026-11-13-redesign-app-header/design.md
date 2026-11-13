## Context

See proposal.md for motivation. The chosen visual direction ("Variant A", a two-tier app-shell) was already validated with the user via a hand-built, screenshotted mockup before this change was created (logged in PLANNING_LOG.md). This document covers how to wire that into the real templates/routes, not the visual direction itself.

Today, `index.html`, `collection.html`, and `upcoming.html` each define their own `<header class="topbar">` from scratch (confirmed via inspection — no shared partial exists). `.back` is used in exactly two places (`collection.html`, `upcoming.html`) and `.nav-link` in exactly two places (`index.html`, `collection.html`) — confirmed via grep, so both classes are fully removable once their markup is replaced.

## Goals / Non-Goals

**Goals:**
- One shared header partial used identically by all three pages.
- Zero behavior change to any existing control (group select, "+ New Group", "+ Add New Plant", group filter) — only where they visually live changes.
- No new backend state or route parameters needed for the active-nav indicator.

**Non-Goals:**
- Does not touch the plant grid, group grid, or dialog markup/behavior.
- Does not add any new navigable destination beyond the two that already exist (Groups, Upcoming) — a third destination is a future change, not this one.
- Does not restyle the page toolbar's own controls (select, buttons) beyond relocating them into the new second row; their existing classes (`.primary`, `select`, etc.) are reused as-is.

## Decisions

**1. Active-destination state is a plain Jinja variable, not a backend parameter.**
Each of the three templates always maps to exactly one nav destination — `index.html` and `collection.html` are always "Groups" (a specific group is still part of Groups, not a third destination), `upcoming.html` is always "Upcoming". So each template sets `{% set active_nav = "groups" %}` (or `"upcoming"`) immediately before including the shared partial; Jinja's default `{% include %}` behavior passes the current template's local context, so no change to any route in `app/main.py` is needed. Alternative considered: pass `active_nav` from each route function — rejected as unnecessary indirection for a value that is static per-template.

**2. The shared partial is `_header.html`, included at the very top of each page's `{% block content %}`, before that page's own toolbar markup.**
```html
{% block content %}
{% set active_nav = "groups" %}
{% include "_header.html" %}
<div class="page-toolbar">
  ...page-specific controls...
</div>
...rest of the page...
{% endblock %}
```
`_header.html` itself renders the logo and the two-destination pill nav, using `active_nav` to decide which pill gets the `.active` class. This mirrors the project's existing partial-inclusion pattern (`{% include "_grid.html" %}` etc.) rather than introducing a templating mechanism the project doesn't already use.

**3. `.back` and `.nav-link` are deleted outright, not deprecated.**
Both classes' only usages are removed as part of relocating the collection/Upcoming views' markup into the new structure (confirmed via grep: `.back` only in `collection.html`/`upcoming.html`; `.nav-link` only in `index.html`/`collection.html`). After the three templates are updated, grep again to confirm zero remaining references before deleting their CSS rules.

**4. The new second-row page toolbar is a plain flex row, matching the existing `.topbar` pattern, and both rows wrap at narrow widths rather than introducing a new breakpoint.**
The existing `.topbar` is `display:flex; align-items:center; gap:1rem` with no wrap. Since the new app-bar (tier 1) only ever has a logo and a 2-item pill nav, it will never overflow. The page-toolbar (tier 2) carries the same content the old single-row topbar carried minus the removed back-arrow and nav-link — i.e. strictly less content than today's row already handles on mobile — so no new breakpoint is needed; `flex-wrap: wrap` is added defensively to both rows for safety and verified live at a narrow viewport.

**5. The group-filter/group-switch `<select>` and the page action button keep their exact existing `hx-get`/`onchange` attributes and ids** (`#page-input`, `#group-input`, `#groups-page-input`, `#upcoming-group-input`, etc.) — only their visual container changes (now inside `.page-toolbar` instead of `.topbar`), so every existing htmx refresh/pagination mechanism keeps working unmodified.

## Risks / Trade-offs

- **Risk:** Deleting `.back`/`.nav-link` CSS could silently break something if a usage was missed. → **Mitigation:** grep for both class names across `app/templates/` after the template edits land, before deleting the CSS; run the full test suite; manually verify all three pages live.
- **Risk:** The existing tests asserting `'href="/upcoming"' in ...` or similar link-presence checks could be coupled to the old markup shape. → **Mitigation:** inspect each existing test before changing templates; the new pill nav still renders a plain `<a href="/upcoming">`, so these assertions keep passing unchanged — confirmed by reading the relevant tests before implementation starts.
