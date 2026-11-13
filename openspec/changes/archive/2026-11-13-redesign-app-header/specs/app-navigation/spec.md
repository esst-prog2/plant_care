## Purpose

Gives the user one consistent, persistent way to move between the app's two top-level destinations from anywhere, instead of each page inventing its own mix of back links and buttons.

## ADDED Requirements

### Requirement: A persistent navigation control links to Groups and Upcoming from every page
The system SHALL show a persistent navigation control, present on the landing page, every scoped collection view, and the Upcoming view, linking to exactly two destinations — "Groups" (the landing page, or back to it from a scoped view) and "Upcoming" — and SHALL visually indicate which of the two is the page currently open.

#### Scenario: Groups indicated as current on the landing page
- **WHEN** the user is on the landing page
- **THEN** the persistent navigation shows "Groups" as the current destination and "Upcoming" as available but not current

#### Scenario: Groups indicated as current on a scoped collection view
- **WHEN** the user is viewing a single group's plant grid
- **THEN** the persistent navigation shows "Groups" as the current destination and lets the user open "Upcoming" from there

#### Scenario: Upcoming indicated as current on the Upcoming view
- **WHEN** the user is on the Upcoming view
- **THEN** the persistent navigation shows "Upcoming" as the current destination and "Groups" as available but not current
