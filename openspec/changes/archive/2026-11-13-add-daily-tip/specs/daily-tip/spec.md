## Purpose

Gives every page a small, warm, plant-themed touch — a short motivational message that is the same for everyone on a given day and changes daily, instead of a static or random one.

## ADDED Requirements

### Requirement: A daily message is shown on every page
The system SHALL show a short, plant-themed motivational message on the landing page, every scoped collection view, and the Upcoming view. The message SHALL be chosen deterministically from a fixed set of 10 messages based on the current date, so every page shows the same message on a given day.

#### Scenario: Same message across different pages on the same day
- **WHEN** the user views the landing page, a scoped collection view, and the Upcoming view on the same day
- **THEN** all three show the identical message

#### Scenario: Message changes the next day
- **WHEN** the current date advances by one day
- **THEN** the message shown is a different one of the 10, not necessarily the next in the user's own viewing order, but consistently determined by the date

#### Scenario: Rotation cycles back after 10 days
- **WHEN** the current date advances by exactly 10 days from any given day
- **THEN** the message shown is the same one that was shown on the original day
