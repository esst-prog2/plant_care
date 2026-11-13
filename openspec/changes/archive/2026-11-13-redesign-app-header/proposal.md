## Why

The topbar on every page (landing, collection view, Upcoming view) has been accumulating buttons and links with no shared design — each template builds its own `<header class="topbar">` from scratch, mixing a back arrow, a group selector, a page action button, and a plain "Upcoming" link in one flat row. The user flagged that this will only get more cluttered as more page-level controls get added, and asked for a more deliberate, polished design.

## What Changes

- Introduce a shared, persistent navigation control (a new `_header.html` partial) shown on every page, linking to the app's two top-level destinations — "Groups" and "Upcoming" — and visually indicating which one is currently open.
- Restructure each page's existing header into two tiers: the new persistent nav on top, and a page-specific toolbar row below it holding that page's own existing controls (group select, "+ New Group"/"+ Add New Plant" buttons) — relocated, not changed in behavior.
- Remove the per-page back arrow (`.back`) on the collection and Upcoming views; the persistent "Groups" nav destination now serves that purpose.
- Remove the now-unused `.nav-link` styling (the plain bordered "Upcoming" link it styled is replaced by the persistent nav).

## Capabilities

### New Capabilities
- `app-navigation`: a persistent, app-wide navigation control, present on every page, that links to the "Groups" and "Upcoming" destinations and indicates which one is currently open.

### Modified Capabilities
(none — `plant-groups`' "return to the landing page" control and `upcoming-view`'s "persistent top bar" control remain satisfied as-is; only their shared implementation changes, not their specified behavior)

## Impact

- `app/templates/`: new `_header.html` partial; `index.html`, `collection.html`, `upcoming.html` restructured to include it and drop their own duplicated logo/back/nav-link markup.
- `app/main.py`: each of the three routes passes which nav destination is active.
- `app/static/style.css`: new pill-nav and two-tier layout styles; removal of `.back` and `.nav-link` rules once nothing references them.
- `tests/`: new assertions that the persistent nav is present and correctly indicates the active destination on each page; existing tests asserting `/upcoming` or `/` link presence still pass since those destinations keep working, just via new markup.
