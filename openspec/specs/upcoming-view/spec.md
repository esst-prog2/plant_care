# upcoming-view Specification

## Purpose

Gives the user a single, date-sorted list of upcoming and overdue watering across their plants, so they don't have to open each group's grid or their phone's calendar to see what needs doing soon.

## Requirements

### Requirement: Upcoming view lists every ready plant sorted by urgency
The system SHALL provide an "Upcoming" view listing every plant whose data has finished loading, sorted so overdue plants come first (most overdue first), then the plant due today, then plants due later ordered by soonest due date. The view SHALL NOT apply any fixed lookahead cutoff; a plant with a long watering interval SHALL still appear, just further down the list.

#### Scenario: Mixed overdue, due-today and future plants
- **WHEN** the user has one plant 3 days overdue, one due today, and one due in 10 days
- **THEN** the Upcoming view lists the 3-days-overdue plant first, the due-today plant second, and the due-in-10-days plant third

#### Scenario: A plant with a long interval is not hidden
- **WHEN** the user has a plant whose next watering is 30 days away and no other plants are due sooner
- **THEN** that plant still appears in the Upcoming view, at the end of the list

#### Scenario: A still-loading plant is excluded
- **WHEN** a plant's care data has not finished loading yet
- **THEN** it does not appear in the Upcoming view until it is ready

### Requirement: Each row names the plant, its group, and its due status
The system SHALL show, for each plant in the Upcoming view, its name, the group it belongs to (or "All" if unassigned), and its due status in the same wording already used on its card (e.g. "Due today!", "N days overdue", "N days left").

#### Scenario: A row for an unassigned plant
- **WHEN** a plant has no group assigned
- **THEN** its Upcoming row shows "All" as its group

### Requirement: Upcoming view can be filtered by group
The system SHALL let the user filter the Upcoming view to a single group, using the same group-selection convention already used by the scoped collection views (including the "All" pseudo-group showing every plant regardless of group).

#### Scenario: Filtering to one group
- **WHEN** the user filters the Upcoming view to "Living room"
- **THEN** only plants assigned to "Living room" appear, still sorted by urgency

#### Scenario: Default is every plant
- **WHEN** the user opens the Upcoming view without choosing a group
- **THEN** it shows every plant regardless of group, equivalent to the "All" filter

### Requirement: A persistent top bar links to the Upcoming view from every page
The system SHALL show a persistent control, present on the landing page and on every scoped collection view, that opens the Upcoming view.

#### Scenario: Reachable from the landing page
- **WHEN** the user is on the landing page
- **THEN** the persistent control for the Upcoming view is visible and opens it

#### Scenario: Reachable from a scoped collection view
- **WHEN** the user is viewing a single group's plant grid
- **THEN** the persistent control for the Upcoming view is visible and opens it
