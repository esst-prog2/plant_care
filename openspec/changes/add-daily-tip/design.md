## Context

See proposal.md for motivation. The app already has a shared header partial (`app/templates/_header.html`, from the `redesign-app-header` change) included identically by every page, and a `clock: Callable[[], date] | None = None` parameter threaded through `create_app()` for testable "today" logic everywhere else in the app (e.g. `_upcoming_rows`, `_due_count`). This change reuses both rather than introducing anything new.

## Goals / Non-Goals

**Goals:**
- One deterministic, testable rule for "today's message" that any page can use with zero per-route code.
- Visually light — a single line, not a new "notice" box competing with the header's already-tuned height.

**Non-Goals:**
- No admin UI to edit the 10 messages — they are a plain Python list in code, changed by editing the source like any other copy in the app.
- No per-user or per-session variation — the message is a function of the date only, identical for every visitor on a given day.
- No localization — English, like the rest of the app's UI copy.

## Decisions

**1. The message renders as one new line inside `_header.html`, between the app-bar and each page's own page-toolbar.**
```html
<header class="app-bar">
  ...
</header>
<p class="daily-tip">{{ daily_tip() }}</p>
```
Because `_header.html` is already included identically by `index.html`, `collection.html`, and `upcoming.html`, this is the only template edit needed — no per-page changes. Placed after the app-bar (not inside it) to avoid disturbing the nav row's already-tuned horizontal layout and padding.

**2. "Today's message" is a Jinja global function, following the existing `asset_version` global's registration pattern, evaluated per-request.**
```python
TIPS = [ ... 10 strings ... ]

def daily_tip() -> str:
    return TIPS[clock().timetuple().tm_yday % len(TIPS)]

templates.env.globals["daily_tip"] = daily_tip
```
`asset_version` is computed once at startup because it depends on a file's mtime, not "today" — this is a genuinely different case, so it's registered as a *callable* global instead of a precomputed value, letting every template call `{{ daily_tip() }}` and get the current day's message using the app's live, overridable `clock()`. No route changes needed, and the existing `clock` test fixture already makes this deterministic in tests.

**3. The 10 messages** (plain English, warm/encouraging tone matching the Upcoming view's "All caught up!" copy, no emojis):
1. "Every leaf you keep alive is a small victory."
2. "Plants don't rush — neither should you."
3. "A little water today, a little more green tomorrow."
4. "Your plants are rooting for you."
5. "Consistency is the best fertilizer."
6. "Even the toughest cactus appreciates a little care sometimes."
7. "Slow growth is still growth."
8. "A watered plant is a happy plant."
9. "Take a breath — your plants are thriving because of you."
10. "Small steps, deep roots."

**4. Styling stays deliberately minimal to avoid reintroducing the header-height regression fixed earlier in `redesign-app-header`.**
```css
.daily-tip {
  margin: 0; padding: .35rem 1.5rem; font-size: .85rem; font-style: italic;
  color: var(--muted); text-align: center;
}
```
No background, no border — a single muted line, visually distinct from the existing `.notice`/`.notice.ok` classes (which signal actual warnings/confirmations elsewhere and must not be reused for decorative content, per the proposal's Impact section). Verified live with Playwright during implementation (same approach used for every prior header change this session) that this doesn't reintroduce unwanted scrolling on a short page.

## Risks / Trade-offs

- **Risk:** Adding any line to the header could re-trigger the scrolling complaint from earlier in `redesign-app-header`. → **Mitigation:** kept to one thin, small-font line (decision 4); measured live with Playwright against the same short-page scenario (a group with one plant) that surfaced the original regression.
- **Risk:** `day_of_year % 10` means two adjacent days can occasionally land on messages that read oddly back-to-back (no guaranteed non-repetition across consecutive days beyond what the fixed order already gives). → **Mitigation:** accepted — the spec only requires determinism and a 10-day cycle, not any ordering guarantee between adjacent days; this matches a simple, testable rule over a more complex (and harder to test) "don't repeat the previous day's message" rule the proposal never asked for.
