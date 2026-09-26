## Why

Keeping several houseplants alive means remembering which one needs water and when, and each species has different light and watering needs. Today this lives in memory or scattered notes, so plants get forgotten. plant_care gives a single screen that shows every plant and how many days are left until its next watering, and puts each watering into the user's Google Calendar so the reminder arrives on the phone. Reminders come from Google, not from the user's computer, because the computer is not switched on every day while the phone almost always has internet. This is the first useful version; the repository currently contains only the README, the OpenSpec scaffolding and the code written under this change.

## What Changes

- Add a homepage showing the user's plants as cards in a 3×2 grid of at most six per page, with page controls for larger collections.
- Add the ability to add a plant by searching a plant-type list and selecting a match, and to remove a plant.
- When a plant is added, fill in its light requirements and watering schedule from a bundled list of common houseplants, and automatically fetch its photo and a short description from Wikipedia, with a placeholder illustration when they cannot be fetched.
- Show a per-plant watering countdown (days left) with a colour-coded status (red when due, green when watered) and a "Watered" button that resets the countdown to the plant's watering interval.
- Show a plant's detailed care instructions when its card is clicked.
- Keep the next two all-day to-dos per plant in the user's Google account, due on the plant's next two watering dates, so they show in the Google Calendar app and can be ticked off on the phone; the second one keeps a reminder waiting if the computer stays off.
- When the user ticks a to-do off in Google, the next time the app runs it takes the completion date as the last watering, so the countdown counts from then and not from when the computer was switched on, and brings the plant's two to-dos back in line.
- **Replaces** the earlier idea of a daily email summary: no email is sent at all, and the README's "daily automated email summary" is superseded by the calendar reminders.

Out of scope for this change (README "Not this term"): room-based organisation, room-specific to-do lists, care history and growth analytics.

## Capabilities

### New Capabilities
- `plant-collection`: the grid of plant cards on the homepage, adding a plant via search-and-select, removing a plant, and viewing a plant's detailed care instructions.
- `plant-care-data`: searching the bundled list of houseplants by name, taking light requirements and watering schedule from it, and fetching the photo and a short description from Wikipedia, with a placeholder when Wikipedia cannot be reached.
- `watering-tracker`: the per-plant days-left countdown, due/OK status display, and the "Watered" action that resets the countdown.
- `calendar-reminders`: the two all-day Google to-dos per plant, kept in step with the app in both directions: created, moved and deleted as plants are added, watered and removed, and read back so that watering ticked off on the phone restarts the countdown from the completion date.

### Modified Capabilities
<!-- None: openspec/specs/ is empty, so all capabilities are new. The earlier `email-notifications` capability is dropped from this change. -->

## Impact

- New application code (frontend, backend, persistence, background sync); the stack is Python, FastAPI, HTMX and SQLite (see `design.md`).
- New external dependencies: Wikipedia's free page-summary service for photos and descriptions (no key; it requires requests to name the project in the User-Agent) and Google Tasks/Calendar in the user's own Google account. No free plant-care API was found that supplies light and watering for common houseplants (Perenual's free plan was tested with a real key and does not), so that care data is bundled. Google is reached through a small Apps Script web app in the user's own account, because Google Cloud asked for a payment method (see `design.md`); no payment method may be attached.
- Needs a way to store each plant's last-watered date and its Google to-do references between sessions, and a periodic background sync while the app runs.
- Reminder notifications are delivered by Google's apps; how an all-day to-do notifies on the phone depends on the Calendar app's settings; the user chose this all-day model knowing that (see `design.md`, Risks).
- Already written email code (transport, daily send, standalone command, related settings and tests) is removed by the implementation tasks.
- No existing specs are affected.
