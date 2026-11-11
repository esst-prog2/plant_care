# plant-groups Specification

## Purpose

Lets the user organize plants into their own named groups (e.g. by room), with a landing page to create, rename, delete and open groups, and a way to assign or move a plant between groups.

## Requirements

### Requirement: Landing page shows "All" and every user-created group
The system SHALL show a landing page, as the application's entry point, with an "All" card showing the total number of plants, one card per user-created group showing that group's name and plant count, and a "+ New Group" control.

#### Scenario: No groups yet
- **WHEN** the user opens the application and has never created a group
- **THEN** the landing page shows only the "All" card and the "+ New Group" control

#### Scenario: Groups with counts
- **WHEN** the user has created two groups and has plants in each
- **THEN** the landing page shows both group cards with their current plant counts, and the "All" card's count includes every plant regardless of group

### Requirement: User can create, rename and delete a group
The system SHALL let the user create a group by typing a name, rename an existing group, and delete a group. Deleting a group SHALL require a confirmation. Deleting a group SHALL NOT delete its plants; they SHALL become unassigned and appear under "All" and no other group. The "All" card SHALL also be renamable, but SHALL NOT be deletable.

#### Scenario: Create a group
- **WHEN** the user activates "+ New Group" and types "Living room"
- **THEN** a new "Living room" card appears on the landing page with a plant count of zero

#### Scenario: Rename a group
- **WHEN** the user renames "Living room" to "Lounge"
- **THEN** the landing page shows the updated name, and plants previously assigned to it remain assigned to the same group under its new name

#### Scenario: Delete a group and confirm
- **WHEN** the user deletes a group that has plants in it and confirms
- **THEN** the group's card disappears from the landing page, and its former plants still appear under "All" with no group assigned

#### Scenario: Cancelled delete
- **WHEN** the user starts deleting a group and cancels the confirmation
- **THEN** the group and its plants are unchanged

#### Scenario: Rename "All"
- **WHEN** the user renames the "All" card to "Everything"
- **THEN** the landing page's card and the switch control in every scoped collection view show "Everything" instead of "All", and no delete control is offered for it

### Requirement: Opening a group or "All" shows a scoped, paged grid
The system SHALL let the user open any card from the landing page to reach the existing paged grid of plant cards, showing only that group's plants, or every plant when "All" is opened. Pagination SHALL be computed over the scoped set only.

#### Scenario: Open a group with few plants
- **WHEN** the user opens a group containing two plants
- **THEN** the system shows those two plants in the grid, with no page controls, and no plants from other groups

#### Scenario: Open a group with more than six plants
- **WHEN** the user opens a group containing seven plants
- **THEN** the system shows the first six on page 1 of 2 and the seventh on page 2, independently of how many plants exist in other groups

### Requirement: User can switch groups or return to the landing page
The system SHALL show a control to return to the landing page and a control to switch directly to a different group (or "All") while viewing a scoped grid, without first returning to the landing page.

#### Scenario: Return to the landing page
- **WHEN** the user activates the back control while viewing a group's grid
- **THEN** the system shows the landing page unchanged

#### Scenario: Switch directly to another group
- **WHEN** the user is viewing one group's grid and chooses a different group from the switch control
- **THEN** the system shows that other group's grid, scoped and paged independently

### Requirement: A plant can be assigned to at most one group, settable at add time or later
The system SHALL let the user optionally choose a group when adding a plant, and SHALL let the user change or remove a plant's group assignment later from its details view. A plant SHALL belong to at most one group at a time.

#### Scenario: Assign a group when adding a plant
- **WHEN** the user adds a plant and selects an existing group in the add form
- **THEN** the new plant appears under that group and under "All," and not under any other group

#### Scenario: Add a plant without choosing a group
- **WHEN** the user adds a plant without selecting a group
- **THEN** the new plant appears only under "All"

#### Scenario: Move a plant to a different group later
- **WHEN** the user opens a plant's details view and assigns it to a different group than its current one
- **THEN** the plant appears under the newly chosen group and no longer under its previous group, and still appears under "All"

#### Scenario: Unassign a plant from its group
- **WHEN** the user opens a plant's details view and chooses "Unassigned"
- **THEN** the plant no longer appears under any group, but still appears under "All"
