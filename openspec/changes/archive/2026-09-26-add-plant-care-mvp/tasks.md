## 1. Decisions and project setup

- [x] 1.1 Verify PLANNING_LOG.md records the stack decision (Option A: Python, FastAPI, HTMX, SQLite), the "only free solutions" rule and the "start local, cloud scheduler later if needed" plan, each naming the decider
- [x] 1.2 Check the free plant-data sources and choose ones that need no payment method: Perenual is tested with a real key and rejected (design Decision 4); verify by making one real Wikipedia page-summary request that returns a photo and a description for Monstera and Pilea, record the choice in PLANNING_LOG.md, and save the real response as a test sample
- [x] 1.3 Scaffold the Python project (FastAPI, Jinja2 templates with HTMX, SQLite), with dependencies, a start command and a `.gitignore` that excludes the environment file, database and downloaded photos; verify the app starts and serves an empty page
- [x] 1.4 Add an example environment file with placeholders for the API key, SMTP settings, recipient address and send time; verify no real secret is in any tracked file

## 2. Data model and countdown logic

- [x] 2.1 Create the persistence layer with the plant table and a "last summary sent" record, with all database access in one thin data-access module (design Decision 2); verify plants survive an application restart and that no other module opens the database directly
- [x] 2.2 Implement days-left and status (due, overdue, OK) from `last_watered`, interval and local date, with an injectable clock (design Decisions 3 and 9); verify unit tests cover the 7→6 day, closed-for-3-days, due today, 2 days overdue and 23:30 watering scenarios from the watering-tracker spec
- [x] 2.3 Implement "plants due today" selection used by the daily email; verify a unit test returns only due and overdue plants

## 3. Plant data provider and offline fallback

- [x] 3.1 Create the local JSON file with common houseplants including Monstera and Pilea (name, photo, light requirements, watering interval in days); verify the file loads and both plants are present
- [x] 3.2 Implement the provider interface with the local JSON implementation for search and care data; verify case-insensitive and partial-name search tests pass and an unknown name returns no results
- [x] 3.3 Implement the Wikipedia photo and description lookup (design Decision 4) with a User-Agent naming the repository, a timeout, and clear results for success, no picture and unreachable; verify tests against the recorded real responses and against failing fake transports
- [x] 3.4 Implement fallback from the external provider to the local one on network error, timeout, rate limit or error response, reporting which source was used; verify tests with a fake failing API cover each failure and the "not in local data" message
- [x] 3.5 Download and store the plant photo locally when a plant is added and keep the care data in the database; verify the card still renders its photo and details with the network disconnected
- [x] 3.6 Extend the bundled list to about 40 common houseplants, each with light, watering interval in days and Wikipedia article title; verify a test that every entry is complete and that Monstera and Pilea are present
- [x] 3.7 Rework the data service so search uses only the bundled list and adding a plant takes care data from the list and the photo and description from Wikipedia, with the placeholder and an offline notice when Wikipedia cannot be reached and no notice when it simply has no picture; remove the Perenual code, tests and settings and the online switch stays available; verify tests for unreachable, error and no-picture cases and that no Perenual reference remains
- [x] 3.8 Store the description and the credit link with the plant and show them in the details view; verify the details view shows the text and a working link for a plant added with Wikipedia data and neither for one added offline

## 4. Homepage and plant management

- [x] 4.1 Build the homepage with a fixed 3×2 card grid of at most six cards showing photo, name, watering status and the "+ Add New Plant" button, including the empty state; verify visually with zero, six and seven plants
- [x] 4.1a Add page controls (previous/next, current page and page count), hidden when there is one page and disabled at the ends, with the page clamped after removals and moved to the new plant after adding; verify with unit tests for the page calculation and by paging through seven and thirteen plants
- [x] 4.2 Build the add-plant search and select flow with a loading state and the "no plants found" message; verify by adding Monstera end to end and by searching for nonsense text
- [x] 4.3 Allow adding a second plant of a type already in the collection; verify two separate cards appear
- [x] 4.4 Implement plant removal with a confirmation step; verify confirm removes the card and cancel leaves it, and that a removed plant is absent from the "due today" selection
- [x] 4.5 Build the plant details view opened by clicking a card, showing photo, light requirements, watering schedule and the "Watered" button, and closable without changes; verify by opening and closing it on a card

## 5. Watering tracker in the interface

- [x] 5.1 Show days left with the green status on cards, and the red "Watering: Due today!" and overdue badges; verify with plants seeded at 3 days left, 0 days left and 2 days overdue
- [x] 5.2 Implement the "Watered" action reachable from the badge and the details view, which saves today as `last_watered` and turns the card green; verify a due plant shows its full interval afterwards and still does after a restart

## 6. Google Tasks reminders

- [x] 6.1 With the user, finish the checks and record the results in PLANNING_LOG.md naming the decider: (a) informational only, Option A stays either way: on the phone, create a date-only to-do due tomorrow in the Google Calendar app and note whether a notification arrives; (b) already found: Google Cloud asks for a payment method, so Apps Script is the access method (design Decision 7); (c) in a new project at script.google.com add the Tasks service and deploy a test web app, and note whether anything asks for a payment method, and if it does, stop and drop Google reminders. Verify the log has the results of (a) and (c)
- [x] 6.2 Extend the persistence layer with the "sync pending" flag and the last synced watering date per plant, and drop the "last summary sent" record; verify tests show these survive a restart and are cleared after a successful sync
- [x] 6.3 Define the Google Tasks client interface (create, update, complete and mark as recorded, list completed and open tasks with completion timestamps in the `plant_care` list, delete), an in-memory fake for tests, and a no-op client for when Google is not set up; verify contract tests pass against the fake
- [x] 6.4 Implement `reconcile` (design Decision 8) with the pull and push steps against the client interface; verify unit tests with the fake and a fake clock cover: tick 3 days before start with a 7-day interval shows 4 days left and two open to-dos 7 and 14 days after the tick, the second to-do left waiting when the app did not run, a tick on the second to-do, in-app watering completing the earliest to-do without being read back as a tick, a tick before and after the due date, a tick at 23:30 local time, phone tick versus in-app "Watered" (later date wins), a deleted to-do recreated, a moved due date restored, a removed plant's to-do deleted, a stray or third to-do in the list deleted, and other lists untouched
- [x] 6.5 Call the sync from the app: at start, every 10 minutes while running, and in the background after a plant is added, watered or removed; keep changes pending and log failures so pages never wait for Google and no watering is lost; verify tests with a failing fake client show the page loads, the watering is kept and the change is retried later
- [x] 6.6 Write the small Apps Script (kept in the repository as a file to paste into the user's script project) that creates, updates, lists and deletes to-dos in the `plant_care` list behind a shared secret, and the real client that calls its web app URL, with the URL and secret outside git; verify with the user's account that two to-dos are created in the `plant_care` list, one is ticked off on the phone, read back with its completion timestamp, and deleted
- [x] 6.7 Add the standalone `sync_tasks.py` command that runs one reconcile and reports the result; verify by running it by hand against the fake and against the real account
- [x] 6.8 Handle "Google not set up": all features work and the log states that calendar reminders are not configured; verify by starting the app without credentials
- [x] 6.9 Replace the email settings in the config and `.env.example` with the Google settings; verify the example file has only placeholders and no real secret is in any tracked file
- [x] 6.10 Remove the email code: the transport, the daily send and standalone command, the send-time scheduler, their tests, the "plants due today" selection if nothing else uses it, and the email settings; verify the test suite passes and a search finds no leftover SMTP or email code

## 7. Final verification

- [x] 7.1 Walk through the README demo with real Wikipedia photos and the real Google account (open homepage, add Monstera and see its two to-dos in the Google Calendar app, mark Pilea watered in the app and see its to-dos move, then tick another plant's to-do on the phone with the app closed, start the app and verify the countdown counts from the tick date), and verify each step behaves as described
- [x] 7.2 Repeat the walkthrough with the network disconnected and verify the offline notice appears, the countdown still works, and a watering pressed while offline shows up in Google after the network is back
- [x] 7.3 Write a short README section on setup, environment variables and how to run the app, and verify a fresh clone can follow it to a running app
- [x] 7.4 Run `openspec validate add-plant-care-mvp` and verify it passes with no errors
- [x] 7.5 Update the README setup section for Google reminders (settings, one-time sign-in, how the sync works, the limitation that the dates are realigned only when the app next runs, so only one reminder waits if the computer stays off); verify a fresh copy of the tracked files can follow it to a running app
- [x] 7.6 With the user's approval, update the README sections that still describe the email (the demo and "The size") to describe Google Calendar reminders; verify the user has approved the wording
- [x] 7.7 Run `openspec validate add-plant-care-mvp` again after the changes and verify it passes with no errors
