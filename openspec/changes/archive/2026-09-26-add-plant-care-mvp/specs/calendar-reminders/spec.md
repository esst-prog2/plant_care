## Purpose

Puts each plant's next two waterings into the user's Google account as all-day to-dos that show in the Google Calendar app, and keeps them in step with the app in both directions, so that a watering ticked off on the phone restarts the plant's countdown even if the computer was switched off at the time, and a reminder is still waiting if the computer stays off.

## ADDED Requirements

### Requirement: Every plant has all-day reminders for its next two waterings
The system SHALL keep exactly two open to-dos per plant in the user's Google account, so that a reminder is still waiting when the computer stays off after the first one has been ticked off. Each to-do SHALL be an all-day item without a time of day, named after the plant (for example "Water Monstera"). The first SHALL be due on the plant's next watering date, that is the date it was last watered plus its watering interval, and the second one interval later.

#### Scenario: Reminders created when a plant is added
- **WHEN** the user adds a plant with a 7-day interval and Google is reachable
- **THEN** two to-dos "Water <plant name>" exist in the user's Google account, due 7 and 14 days from today, as all-day items

#### Scenario: Reminder shows in the calendar app
- **WHEN** the user opens the Google Calendar app on the due date of the first to-do
- **THEN** the plant's to-do is listed for that day and can be ticked off there

#### Scenario: Two open reminders per plant
- **WHEN** the same plant is synchronised repeatedly
- **THEN** the user's Google account still holds exactly two open to-dos for that plant

### Requirement: Ticking a reminder off in Google records the watering
The system SHALL treat a to-do that the user has ticked off in Google as a watering of that plant on the date of the tick. When the system next synchronises, it SHALL set the plant's last-watered date to that completion date, so the countdown counts from the completion date and not from the day the application was started, and it SHALL bring the plant's two open to-dos to the completion date plus one interval and plus two intervals. If several of a plant's to-dos were ticked off, the latest completion date SHALL be used. The completion date SHALL be the calendar date, in the user's local time, of the moment the to-do was completed.

#### Scenario: Ticked while the computer was off
- **WHEN** the user ticks a plant's to-do off on the phone, the computer is off for three more days, and then the application is started; the plant has a 7-day interval
- **THEN** after synchronising the plant shows 4 days left, and its two open to-dos are due 7 and 14 days after the tick

#### Scenario: Ticked before the due date
- **WHEN** the user ticks a to-do off two days before its due date
- **THEN** the last-watered date becomes the tick date and the two open to-dos are due one and two intervals after it

#### Scenario: Ticked after the due date
- **WHEN** the user ticks a to-do off two days after its due date
- **THEN** the last-watered date becomes the tick date, not the due date

#### Scenario: Late-evening tick
- **WHEN** the user ticks a to-do off at 23:30 local time
- **THEN** the completion date is that local date, even though it is already the next day in UTC

#### Scenario: Second to-do ticked off
- **WHEN** the user ticks off the second, later to-do of a plant
- **THEN** the tick counts as a watering on the tick date and both open to-dos are brought to one and two intervals after it

#### Scenario: Computer stays off after a tick
- **WHEN** the user ticks the first to-do off on the phone and the application does not run afterwards
- **THEN** the plant's second to-do is still in Google as a coming reminder, and when the application next runs it moves that to-do to one interval after the tick and adds a new second to-do

#### Scenario: Card status refreshes
- **WHEN** the synchronisation records a watering from Google while the homepage is open
- **THEN** the plant's card shows the green status and the reset countdown after the page is refreshed

### Requirement: Watering in the application updates the reminders
When the user presses "Watered" in the application, the system SHALL complete the plant's earliest open to-do in Google and SHALL bring the plant's two open to-dos to today plus one interval and plus two intervals, so that the plant is not shown as due in Google.

#### Scenario: Watered in the application
- **WHEN** a plant is due today and the user presses "Watered" in the application
- **THEN** the due to-do is completed in Google and the two open to-dos are due one and two intervals from today

#### Scenario: Both places record a watering
- **WHEN** the user ticked a plant's to-do off yesterday on the phone and presses "Watered" in the application today before the system synchronised
- **THEN** the last-watered date is today, because the later watering date wins

### Requirement: Removing a plant removes its reminders
When the user removes a plant, the system SHALL delete the plant's to-dos from Google.

#### Scenario: Plant removed
- **WHEN** the user removes a plant that has open to-dos
- **THEN** the to-dos no longer appear in the user's Google account after synchronisation

#### Scenario: Removal while Google is unreachable
- **WHEN** the user removes a plant and Google cannot be reached
- **THEN** the plant is removed at once and its to-dos are deleted when Google is next reachable

### Requirement: The application keeps its reminders correct
The system SHALL bring each plant's two to-dos back in line with the plant's data whenever it synchronises. A to-do that the user deleted in Google SHALL be created again while the plant exists, a to-do whose due date was changed in Google SHALL get its planned due date restored, and a third open to-do for the same plant SHALL be deleted.

#### Scenario: Reminder deleted in Google
- **WHEN** the user deletes one of a plant's to-dos in Google and the system synchronises
- **THEN** the to-do is created again, so the plant has two open to-dos

#### Scenario: Due date moved in Google
- **WHEN** the user drags a to-do to another date in Google and the system synchronises
- **THEN** the due date is set back to the planned date

#### Scenario: Watering interval changes
- **WHEN** a plant's stored watering interval changes
- **THEN** the next synchronisation moves its two to-dos to the new planned dates

#### Scenario: Extra reminder for a plant
- **WHEN** a third open to-do for the same plant exists in the application's list
- **THEN** the system deletes the extra one on synchronisation

### Requirement: Synchronisation runs when the application starts and while it runs
The system SHALL synchronise with Google when the application starts, at regular intervals while it is running, and after a plant is added, watered or removed. The system SHALL also offer a command that runs the same synchronisation once on demand.

#### Scenario: Synchronise at start
- **WHEN** the application is started
- **THEN** it synchronises before or shortly after showing the homepage, so watering recorded on the phone is picked up

#### Scenario: Synchronise while running
- **WHEN** the user ticks a to-do off on the phone while the application is running
- **THEN** the application picks it up within the synchronisation interval, without a restart

#### Scenario: Synchronise on demand
- **WHEN** the user runs the synchronisation command
- **THEN** the same actions happen once and the result is reported

### Requirement: Google problems never block the application or lose data
If Google or the internet cannot be reached, the system SHALL complete the user's action locally, SHALL keep the pending change, and SHALL retry it on a later synchronisation. Failures SHALL be recorded and SHALL NOT crash the application or delay the page.

#### Scenario: Watered while offline
- **WHEN** the user presses "Watered" and Google cannot be reached
- **THEN** the countdown resets at once, and the to-dos are completed and realigned when Google is next reachable

#### Scenario: Plant added while offline
- **WHEN** the user adds a plant and Google cannot be reached
- **THEN** the plant is added with its card and countdown, and its to-dos are created on a later synchronisation

#### Scenario: Failure recorded
- **WHEN** a synchronisation fails
- **THEN** the failure is written to the application log and the homepage still loads normally

### Requirement: The application works without Google
If no Google access has been set up, the system SHALL work fully without reminders: plants, countdowns and the "Watered" action behave as usual, and the system SHALL report in its log that reminders are switched off.

#### Scenario: Not configured
- **WHEN** the application is started with no Google access configured
- **THEN** the homepage works normally and the log says that calendar reminders are not configured

### Requirement: Only the application's own to-dos are touched
The system SHALL keep its to-dos in a dedicated list in the user's Google account and SHALL NOT read, change or delete any other to-do, event or list.

#### Scenario: Other tasks left alone
- **WHEN** the user has other to-dos in Google and the system synchronises
- **THEN** those to-dos are unchanged

#### Scenario: Stray reminder removed
- **WHEN** the application's dedicated list contains a to-do that belongs to no plant
- **THEN** the system deletes it on synchronisation
