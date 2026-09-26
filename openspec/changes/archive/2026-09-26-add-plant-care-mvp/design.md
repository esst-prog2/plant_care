## Context

The repository started greenfield: only the README and OpenSpec scaffolding. See proposal.md for motivation and the specs for required behaviour.

Constraints that shape the design:
- Course project with one developer; simplicity and demonstrability matter more than scale.
- Three parts have no prior implementation experience: fetching photos from an online service, talking to Google (access and the Tasks API), and a background sync while the app runs (the README flags these kinds of parts as risks).
- The README requires an offline fallback so the demo always works: the bundled plant list and the placeholder illustration provide it.
- The user's computer is not switched on every day, but the phone almost always has internet and the Google Calendar app. Reminders and the "I watered it" signal therefore have to live in Google, not in the local app.

Why Google Tasks: email was dropped (it would only arrive when the computer runs). A plain Calendar event has no "done" state, so a tick on the phone could not be read back. Google Tasks items show in the Google Calendar app, can be ticked off there, and the API returns the completion timestamp.

Assumptions (recorded rather than asked, because they do not change the specs):
- Single user, single device, one Google account, no login to the app.
- The application is running now and then (start, and while the user uses it); it does not need to be running on the due date.
- The homepage shows a fixed 3×2 grid of at most six cards and pages through larger collections (user decision); the page number is not persisted between sessions.

## Goals / Non-Goals

**Goals:**
- Small enough to finish in one term and to demonstrate end to end, including offline.
- Countdown values that are always correct after a restart, without a background job maintaining them, and correct after a watering was recorded on the phone while the computer was off.
- The online photo source and Google Tasks each sit behind a narrow interface so they can be swapped or faked in tests, and the app works fully when Google is not set up or not reachable.

**Non-Goals:**
- Multiple users, accounts, or hosted deployment.
- Native mobile apps, or controlling when and how the phone shows a notification (that is decided by the Google apps).
- Anything under the README's "Not this term" list.

## Decisions

Cost rule (user decision): only free solutions, no payment method attached anywhere, so nothing can incur cost. If a free tier stops being free, the feature degrades or is dropped rather than paid for.

### Decision 1: Application stack — Option A chosen by the user

| Option | Composition | For | Against |
|---|---|---|---|
| A. Python, server-rendered | FastAPI + Jinja2 templates with HTMX, SQLite, APScheduler, Google API client | One language and one process; Python already installed; almost no frontend build tooling; scheduler runs in the same process | Less "modern SPA" feel; card interactions rely on HTMX fragments |
| B. TypeScript, SPA + API | React (Vite) frontend, Express backend, SQLite, `node-cron`, `googleapis` | Rich interactive UI; large ecosystem | Two codebases and a build step; more moving parts for a solo term project |
| C. TypeScript full-stack | Next.js with API routes, SQLite, `node-cron` | One codebase | Background jobs do not fit serverless-style hosting; heavier framework to learn |

**Chosen: Option A.** Fewest moving parts, one language, and an in-process background job for the sync. All three options are free (open source); the cost rule is decided by hosting, Google access and the photo source, not by the language.

### Decision 2: Persistence in SQLite

Store plants in a local SQLite database: id, plant type id, display name, photo path, light requirements, watering interval in days, date added, last watered date, plus a "sync pending" flag and the last-watered date that Google already knows about (so an in-app watering can complete the right to-do). Google to-dos are recognised by a marker in their notes that carries the plant id, so their ids are not stored locally: the Google list is the record of what exists, and the to-dos of a removed plant are found and deleted as strays on the next sync. Plant ids are never reused.
- Chosen over a JSON file because concurrent writes from the web handler and the background sync are safer, and queries stay trivial.
- Chosen over a server database because there is no hosting and a single user.
- All database access goes through one thin data-access module, so that SQLite can later be replaced without touching the rest of the application.

### Decision 3: Store `last_watered` and derive the countdown

Days left = `interval − (today − last_watered)` using the local calendar date. The countdown is never decremented by a job.
- Correct after restarts and while the application is closed (watering-tracker spec).
- This is what makes a phone tick work: the sync only has to set `last_watered` to the completion date and the countdown is right.
- Alternative rejected: a stored counter decremented nightly, which drifts if the job is missed.

### Decision 4: Bundled care list, Wikipedia for photo and description (user decision)

Light requirements and the watering interval come from a bundled JSON list of about 40 common houseplants (name, Wikipedia article title, light, interval in days). Searching the list is a plain case-insensitive substring search. The values are general-knowledge approximations, not scientific data.

The photo and a short description are fetched from Wikipedia's page-summary service (`/api/rest_v1/page/summary/<title>`, thumbnail and extract) when a plant is added. The service needs no key, but Wikimedia rejects requests without contact details in the User-Agent (HTTP 403, seen in a real test), so requests send a User-Agent that names the project repository. The photo lookup sits behind a small interface so it can be faked in tests and switched off.
- Rejected: Perenual. Tested with a real free key: search works, but Monstera and Pilea (beyond the free species 1-3000) come back with "Upgrade Plans" placeholders for photo, light and watering and their detail calls answer HTTP 429; searches for 16 other common houseplants gave no usable data, and even free-range species had empty watering and sunlight.
- Rejected for now: Trefle (care data almost empty) and Open Plantbook (sensor values, no watering interval in days).
- Rejected: scraping websites, which the README already identifies as fragile.
- Photos and text come from Wikipedia/Wikimedia Commons under their own licences; the details view links to the article as the credit. For personal use this is fine; publishing the app would need the licence terms checked.

### Decision 5: Copy the photo and care data at add time

When a plant is added, save the care fields in the database, download the photo to a local folder, and store the description and the credit link. Views then never call the online source (plant-care-data spec). If Wikipedia cannot be reached or refuses, the plant is still added with the placeholder illustration and marked so the card says offline data was used; a photo found later is not fetched retroactively.
- Alternative rejected: hotlinking Wikipedia's image URL, which breaks offline and if the URL changes.

### Decision 6: Reminder model — two all-day Google Tasks per plant (Option A chosen by the user)

Each plant has two open to-dos in a dedicated Google Tasks list (name `plant_care`), both titled "Water <plant>", with date-only due dates `last_watered + interval` and `last_watered + 2 × interval`. The second one is there so that a reminder is still waiting when the computer stays off after the first one is ticked off (user decision). Their notes carry a marker with the plant id. When the user ticks one off, Google stores the completion timestamp.

| Option | What it is | Verdict |
|---|---|---|
| **A. To-do only, all-day** | Two Google Tasks per plant, date only | **Chosen by the user, and it stays the choice even if the phone does not notify.** Simplest; the tick on the phone is the done signal. |
| B. To-do plus timed event | The task for completion, plus a timed Calendar event at a set hour with a popup | Not used. Would be the way to get a guaranteed timed notification if the user ever wants it. |
| Calendar event only | Event with popup | Rejected: no "done" state, so the phone tick could not be read back. |
| Recurring event or task | Repeats every interval | Rejected: the Tasks API has no recurrence and events have no completion. |
| Email | Daily summary | Rejected by the user: it only arrives when the computer runs. |

The Tasks API stores only the date of a due date and cannot read or write a time of day, so an API-created to-do is always all-day. That is why Option A means "all-day", and why whether and when the phone notifies depends on the Calendar app's all-day notification settings; the user accepts this.

### Decision 7: Google access method — Apps Script web app (decided from the user's payment-method check)

Tasks belong to the user's personal account, so a service account cannot reach them. Options:

| Option | How | Notes |
|---|---|---|
| OAuth desktop flow, published "In production" — rejected: Google Cloud asked for a payment method | The user signs in once in a browser; the app stores a refresh token | Needs a Google Cloud project with the Tasks API enabled and a consent screen. Google's documentation says refresh tokens of an external app in "Testing" status expire after 7 days, so the app must be "In production" (unverified, personal use, with the warning screen). Tokens also expire after 6 months without use, and the sign-in screen shows an "unverified app" warning. |
| **Apps Script web app — chosen** | A small script in the user's own Google account exposes create, list, update and delete over HTTPS; the app calls it with a shared secret | No Google Cloud project or OAuth in the app. The user pastes the script and deploys it once; the endpoint is protected only by the secret. Free limits (for example 5,000 Calendar events created per day) are far above what is needed; billing and access details were not confirmed in the documentation. |
| Service account | | Rejected: cannot access a personal Tasks list. |

**Result:** the user tried creating a Google Cloud project and the console asked for a payment method. That breaks the no-payment rule, so the OAuth option is out and the **Apps Script web app** is used. The script is kept in the repository as a file to paste into the user's own script project; it only touches the `plant_care` list, runs as the user, and accepts a call only when it carries the shared secret. Still to confirm on the user's account (task 6.1): that adding the Tasks service to an Apps Script project and deploying it as a web app asks for no payment method. If it does, Google reminders are dropped and the app stays without them (it works without Google by design). The Calendar API documentation notes that exceeding its quota is planned to cost money later in 2026; the volume here is a handful of calls per sync, and Apps Script's own daily limits are far above that.

Credentials (the web app URL and the shared secret) live in a file or environment variables outside git.

### Decision 8: One reconcile step, in both directions

A single function `reconcile` makes the plants and the Google list agree, and everything else calls it: the app at start, a background job every 10 minutes while running, a best-effort background call after a plant is added, watered or removed, and a standalone command `sync_tasks.py` for use by hand. A lock keeps two runs from overlapping.

1. Pull: read the tasks of the `plant_care` list, including completed ones, and ignore completed to-dos that the app completed itself (marked in their notes as recorded). For each plant with a completed to-do, set `last_watered` to the local calendar date of the latest completion timestamp, but never to an earlier date than the one already stored (the later watering wins). Read completed tasks explicitly (show completed and hidden), because the list may hide them.
2. Push: for each plant, compute the two planned due dates `last_watered + interval` and `last_watered + 2 × interval`. Take the plant's open to-dos ordered by due date and match them to these dates: move the due date of a to-do that differs, create missing ones (a completed or deleted to-do simply counts as missing), and delete any extra open to-do. When the plant was watered in the app since the last sync, first complete its earliest open to-do and mark it as recorded in its notes, so it is not read back later as a phone tick. Delete to-dos of removed plants (from the pending-delete table) and to-dos in the list that belong to no plant. Tasks outside the list are never read or changed.
3. Failures leave the plant marked "sync pending" and are logged; the next reconcile retries. The web request never waits for Google.

The Tasks API list parameters (completed and hidden tasks) are not spelled out in the reference page that was checked, so the real client is verified against a real list in the tasks below.

### Decision 9: Testing approach

Unit-test the countdown calculation with a fake clock, including midnight and overdue cases from the specs. Test the photo lookup and its fallback with a fake failing source and with a recorded real Wikipedia response. Test `reconcile` against an in-memory fake Google client with a fake clock: tick while off, the second to-do left waiting, a tick on the second to-do, early and late ticks, late-evening timestamp, both-places conflict, deleted and moved to-dos, removed plants, foreign tasks untouched, and failures. The no-op client is used when Google is not set up. Manual checks for the visual grid, the real Google round trip and the phone notification.

## Risks / Trade-offs

- **An all-day to-do may not produce a push notification on the phone** (the search results suggest date-only tasks may only follow the Calendar app's all-day notification settings) → the user decided to keep the all-day model regardless; the phone check in task 6.1 is informational, and a timed event (Option B) can be added later if wanted.
- **After a phone tick, the plant's dates are only realigned when the app next runs** → until then the plant's second to-do stays in Google as a coming reminder, but on the old schedule (up to one interval away from the tick date), and only one reminder is waiting. The countdown stays correct. Keeping two to-dos ahead (user decision) reduces this, but a long time with the computer off after a second tick can still leave no reminder. With Apps Script, a later improvement could let the script realign the dates itself on a timer even when the computer is off; not planned now.
- **The Apps Script endpoint can be called by anyone who has its URL** → protect it with a long random shared secret kept outside git; the script can only touch the `plant_care` list; redeploy with a new secret if it leaks.
- **Apps Script needs re-approval or its limits or terms change** → the daily limits are far above the need; the app keeps working without reminders and logs the problem.
- **Google Cloud asked for a payment method (confirmed by the user)** → the OAuth route is rejected; the same payment-method check is repeated for Apps Script in task 6.1.
- **Wikipedia refuses or changes its service** (it already answered 403 until the User-Agent named the project) → placeholder illustration, data copied at add time, the photo source behind an interface, and a switch to turn online photos off.
- **Bundled care values are approximate** → the interval and light are shown on the card and details so a wrong value is noticeable; the list is a plain file that is easy to correct or extend.
- **Wikipedia's images and text have their own licences** → the details view links to the article as the credit; check the terms before publishing the app.
- **Time zones and the completion date** → the completion timestamp is UTC; convert to the local date before use, and test the late-evening case.
- **The user edits the app's to-dos in Google** → the reconcile step restores due dates and recreates deleted to-dos, at the cost of overriding manual changes.
- **Secrets accidentally committed (API key, Google credentials)** → Environment variables or ignored files, an example env file with placeholders, and the real files in `.gitignore`.
- **A solo learner tackling three unfamiliar areas at once** → Task order in tasks.md delivers a working offline app first (grid, add/remove, countdown), then online photos, then Google.

## Open Questions

- Google access method: Apps Script (decided). Still open: whether Apps Script itself asks for a payment method, checked in task 6.1.
- Whether an all-day to-do notifies on the phone: Option A stays either way (user decision); the phone check in task 6.1 only records what happens.
