# plant_care

## 1. The demo
I open the plant_care homepage. The homepage appears on the screen with a 3×2 card grid. I click the "+ Add New Plant" button in the top left, type "Monstera" into the search bar, and select it from the list. The card loads: an API call running in the background fetches the photo of the plant and its key information (watering, light requirements, etc.). I click the red "Watering: Due today!" badge glowing on the Pilea card, then press the "Watered" button in the pop-up window. The status turns green, the countdown jumps to 7 days, and a notification arrives in my email inbox confirming that I have watered the plant.

## 2. The shape
in: Selecting plant types from a list, clicking a button when completing a task
out: Information about the selected plant, a counter resets upon clicking
on screen: Cards displayed in a grid view with the added plants, new ones can be added, old ones can be removed, and the counters can be reset by clicking the button

## 3. The size
First useful version:
- 3×2 grid layout with plant cards
- ability to add new plants and remove old ones
- automatic fetching of plant photo, light requirements and watering schedule via an external API
- days-left countdown timer for watering with a "Watered" action button to reset the clock
- daily automated email summary listing all gardening task on that day

Not this term:
- room-based plant organization - grouping plants by their specific locations/rooms within the apartment
- room-specific to-do lists - generating localized task lists based on room placement and immediate plant care needs
- care history and growth analytics — charts, logs, or photo timelines of past waterings and repottings

## 4. How we would know it works
- Correctly finds the plant type entered into the search bar, allowing me to select it and add it to my list.
- The email notification with the tasks arrives, and clicking the buttons correctly resets the counter.
- Clicking on the plant's card displays its detailed care instructions.

## 5. What could stop this

- Web Scraping Fragility: Layout changes or bot protections on target websites can break data extraction.
- External API Limits: Rate limits, downtime, or sudden paywalls can disrupt live data fetching.
- Offline Fallback: A local JSON mock file ensures the project stays fully functional and presentable anytime.
- Email & Timer Logic: Automated background emails and counter reset logic pose unfamiliar implementation challenges.
