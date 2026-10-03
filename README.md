# plant_care

## 1. The demo
I open the plant_care homepage. The homepage appears on the screen with a 3×2 card grid. I click the "+ Add New Plant" button in the top left, type "Monstera" into the search bar, and select it from the list. The card loads: an API call running in the background fetches the photo of the plant and its key information (watering, light requirements, etc.). I click the red "Watering: Due today!" badge glowing on the Pilea card, then press the "Watered" button in the pop-up window. The status turns green, the countdown jumps to 7 days, and on my phone the plant's Google Calendar reminder moves ahead to the next watering date.

## 2. The shape
in: Selecting plant types from a list, clicking a button when completing a task
out: Information about the selected plant, a counter resets upon clicking
on screen: Cards displayed in a grid view with the added plants, new ones can be added, old ones can be removed, and the counters can be reset by clicking the button

## 3. The size
First useful version:
- 3×2 grid layout with plant cards
- ability to add new plants and remove old ones
- automatic fetching of the plant photo and a short description from Wikipedia; light requirements and an estimated watering interval come from a built-in list of common houseplants (general-knowledge estimates, not verified against a horticultural source — see "Where the plant data comes from")
- days-left countdown timer for watering with a "Watered" action button to reset the clock
- Google Calendar reminders: each plant gets two all-day to-dos for its next waterings, and ticking one off on the phone restarts the countdown from that day

Not this term:
- room-based plant organization - grouping plants by their specific locations/rooms within the apartment
- room-specific to-do lists - generating localized task lists based on room placement and immediate plant care needs
- care history and growth analytics — charts, logs, or photo timelines of past waterings and repottings

## 4. How we would know it works
- Correctly finds the plant type entered into the search bar, allowing me to select it and add it to my list.
- The Google Calendar reminders appear on the phone, ticking one off there restarts the counter from that day, and clicking the buttons in the app correctly resets the counter.
- Clicking on the plant's card displays its light requirements and watering interval.

## 5. What could stop this

- Web Scraping Fragility: Layout changes or bot protections on target websites can break data extraction.
- External API Limits: Rate limits, downtime, or sudden paywalls can disrupt live data fetching.
- Offline Fallback: A local JSON mock file ensures the project stays fully functional and presentable anytime.
- Google Sync & Timer Logic: Keeping the calendar reminders in step with the app and the counter reset logic pose unfamiliar implementation challenges.

## 6. Running the app

Needs Python 3.12 or newer (developed and tested on 3.14 under Windows). Everything used is free; no payment method is needed anywhere.

**For reviewers:** the app starts with no keys or accounts at all (steps below; the package versions are pinned in `requirements.txt`). The Google Calendar reminders need the owner's own Google account, so on a fresh copy they are switched off and the log says "Google calendar reminders are not configured"; everything else works, including the countdown, adding and removing plants, and Wikipedia photos. `python -m pytest` runs the automated tests. To see what was planned and decided, look at `openspec/specs/` (what the program does), `openspec/changes/archive/` (the plan, design and task list it was built from) and `PLANNING_LOG.md` (each decision, with whether the student or the AI made it).

```
python -m venv .venv
.venv\Scripts\activate            # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env            # macOS/Linux: cp .env.example .env
python run.py
```

Then open http://127.0.0.1:8000. The app works out of the box: it needs no keys, uses the built-in plant list, and fetches photos from Wikipedia when it can. Google reminders are optional (see below).

### Settings (`.env`)

| Variable | Meaning |
|---|---|
| `ONLINE_PHOTOS` | `on` (default) fetches a photo and short description from Wikipedia when a plant is added; `off` uses only the built-in data and a placeholder image. |
| `GOOGLE_SCRIPT_URL`, `GOOGLE_SCRIPT_SECRET` | Address and secret of your Apps Script web app (see below). Without both, the app works but has no reminders. |
| `SYNC_INTERVAL_MINUTES` | How often the running app syncs with Google. Default `10`. |

Never commit `.env`; it is ignored by git.

### Where the plant data comes from

The light and watering values come from the built-in list in `data/plants.json` (about 40 common houseplants). They are general-knowledge approximations, so correct them there if a plant needs something different; the list is a plain file and easy to extend. The photo and the short description are fetched from Wikipedia when a plant is added and stored with it, so they work offline afterwards. Without internet a placeholder illustration is shown and the plant says that offline data was used. The details view links to the Wikipedia article as the credit; Wikipedia's images and text have their own licences.

These watering intervals are not verified against a horticultural source. A spike checked 12 of the 41 plants directly against the RHS (Royal Horticultural Society): none of the 12 RHS pages state a watering interval as a number of days — they all tie watering to the state of the compost ("once the top 5cm feels dry") or to the season, never to a day count, and Kew's public plant pages carry no care guidance at all. So the app's day numbers are a rough default to check the plant by eye against, not a cited schedule; see `hw4-spike-evidence.md` for the 12 lookups and their URLs.

### Google reminders

Each plant gets two all-day to-dos ("Water Monstera") in a Google Tasks list called `plant_care`, one for its next watering and one for the one after. They show up in the Google Calendar app on your phone, where you can tick them off. When the app next syncs, a to-do you ticked off counts as a watering on the day you ticked it, so the countdown counts from then and not from when the computer was switched on, and the two to-dos move on accordingly. Pressing "Watered" in the app does the same in the other direction. The app syncs when it starts, every `SYNC_INTERVAL_MINUTES` minutes while it runs, and after a plant is added, watered or removed. To sync by hand: `python sync_tasks.py`.

One-time setup (free, no payment details):

1. Go to https://script.google.com and create a new project.
2. Replace its code with the contents of `google/Code.gs`.
3. In the left sidebar, next to **Services**, click **+**, choose **Google Tasks API** and click **Add**.
4. Open **Project Settings** (gear icon) and, under **Script properties**, add a property named `SHARED_SECRET` whose value is a long random string. Keep it private.
5. Click **Deploy > New deployment**, choose the type **Web app**, set **Execute as: Me** and **Who has access: Anyone**, and deploy. Approve the permissions when asked (Google warns that the script is unverified because it is your own; that is expected).
6. Copy the web app URL into `.env` as `GOOGLE_SCRIPT_URL` and the secret as `GOOGLE_SCRIPT_SECRET`.
7. Start the app (or run `python sync_tasks.py`) and check that the to-dos appear in Google Calendar or Google Tasks.

Good to know:
- Anyone who has both the web app URL and the secret can change the `plant_care` list, so keep them private. The script touches no other list.
- If you change `google/Code.gs` later, use **Deploy > Manage deployments** to publish a new version.
- The dates are only realigned when the app runs. If the computer stays off after you tick a to-do, the plant's second to-do keeps waiting in Google on the old schedule.
- Whether an all-day to-do makes the phone play a notification depends on the Calendar app's notification settings for all-day items.

### Tests

```
python -m pytest
```

## 7. What comes next

Ideas that were left out of the first version on purpose, to be planned as separate changes later (in addition to the items under "Not this term" above):
- Own notes for each plant: a free-text note in the plant's details view.
- Own photo upload for each plant, which would take priority over the Wikipedia photo.
- Condition-based correction of the watering interval, instead of a fixed number of days per species: a couple of questions at add time (light level, pot/soil) to adjust the starting estimate, and button feedback after watering (soil was still wet / leaf was drooping / right on time) to nudge it over time. This follows directly from the spike (`hw4-spike-evidence.md`): no citable source gives a fixed day count either, so the honest fix is to make the estimate adjustable from what the user actually observes, not to chase a better single number.
