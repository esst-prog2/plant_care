## 1. Backend: daily message selection

- [ ] 1.1 In `app/main.py`, add the `TIPS` list (the 10 messages from design.md) and a `daily_tip()` function that returns `TIPS[clock().timetuple().tm_yday % len(TIPS)]`; register it as a Jinja global (`templates.env.globals["daily_tip"] = daily_tip`), following the existing `asset_version` global's registration pattern
- [ ] 1.2 Verify with a unit test (using the existing `clock`/`TODAY` fixture pattern) that the same date always yields the same message, two dates 10 days apart yield the same message, and at least one other date yields a different message

## 2. Template and styling

- [ ] 2.1 Add `<p class="daily-tip">{{ daily_tip() }}</p>` to `app/templates/_header.html`, directly after the `</header>` closing tag (between the app-bar and each page's own page-toolbar)
- [ ] 2.2 Add the `.daily-tip` style to `app/static/style.css` per design.md's decision 4 (thin, muted, italic, centered, no background/border)

## 3. Verification

- [ ] 3.1 Run the full test suite (`pytest`) and confirm it passes
- [ ] 3.2 Manually verify live (throwaway db, Playwright): confirm the same message appears on the landing page, a collection view, and the Upcoming view on the same simulated day; confirm the header's total height still doesn't force an unnecessary scroll on a short page (same one-plant-group scenario used to verify the earlier header-height fix)

## 4. Wrap-up

- [ ] 4.1 Append a PLANNING_LOG.md line for this change once implemented, per AGENTS.md
