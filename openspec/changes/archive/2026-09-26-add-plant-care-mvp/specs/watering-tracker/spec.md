## Purpose

Tracks when each plant next needs water, shows the days remaining and a clear due/OK status, and lets the user record a watering to restart the countdown.

## ADDED Requirements

### Requirement: Each plant shows a watering countdown
The system SHALL show on every plant card the number of whole days left until the plant's next watering, computed from the date it was last watered and its watering interval. A newly added plant SHALL be treated as watered on the day it is added.

#### Scenario: New plant countdown
- **WHEN** the user adds a plant whose watering interval is 7 days
- **THEN** its card shows 7 days left

#### Scenario: Countdown decreases with time
- **WHEN** one day passes after a plant with a 7-day interval was watered
- **THEN** its card shows 6 days left

#### Scenario: Countdown updates while the application is closed
- **WHEN** the application is reopened three days after a plant with a 7-day interval was watered
- **THEN** its card shows 4 days left

### Requirement: Due plants are flagged prominently
The system SHALL show a red "Watering: Due today!" badge on a card when zero days are left, and the same red badge with an overdue indication when the countdown has passed zero. A plant with one or more days left SHALL show a green status.

#### Scenario: Due today
- **WHEN** a plant has 0 days left
- **THEN** its card shows a red "Watering: Due today!" badge

#### Scenario: Overdue
- **WHEN** a plant was due two days ago and has not been watered
- **THEN** its card shows a red badge indicating that it is 2 days overdue

#### Scenario: Not yet due
- **WHEN** a plant has 3 days left
- **THEN** its card shows a green status with "3 days left"

### Requirement: User can mark a plant as watered
The system SHALL provide a "Watered" button for each plant, reachable by clicking the status badge or the card. Pressing it SHALL record today as the last watering date, reset the countdown to the plant's full watering interval and change the status to green.

#### Scenario: Water a due plant
- **WHEN** a plant is due today with a 7-day interval and the user presses "Watered"
- **THEN** the card shows 7 days left with a green status

#### Scenario: Water a plant early
- **WHEN** a plant has 4 days left and the user presses "Watered"
- **THEN** the countdown resets to the full interval

#### Scenario: Watered state persists
- **WHEN** the user marks a plant as watered and reopens the application the same day
- **THEN** the plant still shows the reset countdown

#### Scenario: Watered plant's reminder moves on
- **WHEN** a plant was due today and the user marks it as watered
- **THEN** its calendar reminder is completed and the next one is due a full interval from today (see the calendar-reminders capability)

### Requirement: Countdown day boundaries follow the local calendar date
The system SHALL count days by the user's local calendar date, so that a plant watered late in the evening is counted as watered on that date and the countdown decreases at local midnight.

#### Scenario: Watered late in the evening
- **WHEN** the user waters a plant with a 7-day interval at 23:30
- **THEN** the card shows 6 days left after local midnight
