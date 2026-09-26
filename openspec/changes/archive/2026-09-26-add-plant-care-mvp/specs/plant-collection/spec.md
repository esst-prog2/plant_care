## Purpose

Lets the user see all of their plants at a glance on the homepage, add new plants by searching for a plant type, remove plants they no longer keep, and read detailed care instructions for any plant.

## ADDED Requirements

### Requirement: Homepage shows plants as cards in a paged grid
The system SHALL display the user's plants on the homepage as cards arranged in a grid of three columns by two rows, showing at most six cards per page. Each card SHALL show the plant's photo, name and watering status. When the user has more than six plants, the system SHALL provide page controls to move between pages, and SHALL show which page is current and how many pages there are.

#### Scenario: Plants are shown as cards
- **WHEN** the user opens the homepage and has six plants
- **THEN** the system shows six cards in a grid of three columns by two rows, each with photo, name and watering status, and no page controls

#### Scenario: Empty collection
- **WHEN** the user opens the homepage and has no plants
- **THEN** the system shows an empty grid with the "+ Add New Plant" button still available

#### Scenario: More plants than fit on one page
- **WHEN** the user has seven plants
- **THEN** the system shows the first six on page 1 of 2, and the seventh alone on page 2

#### Scenario: Move between pages
- **WHEN** the user has seven plants and activates the "next page" control on page 1
- **THEN** the system shows page 2 with the seventh plant, and a "previous page" control returns to page 1

#### Scenario: Page controls at the ends
- **WHEN** the user is on the first page, or on the last page
- **THEN** the "previous page" control is unavailable on the first page and the "next page" control is unavailable on the last page

#### Scenario: Adding a plant to a full last page
- **WHEN** the user has six plants and adds a seventh
- **THEN** the system shows page 2 of 2 containing the new plant, or otherwise keeps the user on a page that lets them reach it

### Requirement: User can add a plant by searching for its type
The system SHALL provide a "+ Add New Plant" button on the homepage. Activating it SHALL let the user type a plant name into a search bar and SHALL list the plant types matching the text. Selecting a match SHALL add a card for that plant to the grid.

#### Scenario: Successful search and add
- **WHEN** the user activates "+ Add New Plant", types "Monstera" and selects "Monstera" from the results
- **THEN** the system adds a Monstera card to the grid showing its photo and care information

#### Scenario: Partial text matches
- **WHEN** the user types "mons" into the search bar
- **THEN** the system lists plant types whose names contain "mons", case-insensitively

#### Scenario: No matching plant type
- **WHEN** the user types text that matches no plant type
- **THEN** the system shows a "no plants found" message and does not add any plant

#### Scenario: Same type added twice
- **WHEN** the user adds a plant type that is already in the collection
- **THEN** the system adds a separate second card, because the user may own several plants of the same type

### Requirement: User can remove a plant
The system SHALL let the user remove a plant from the collection. Removal SHALL require a confirmation, and once confirmed the plant's card and its watering data SHALL be deleted.

#### Scenario: Confirmed removal
- **WHEN** the user chooses to remove a plant and confirms
- **THEN** the system removes the card from the grid and the remaining cards close up the gap, pulling cards forward from the next page if there is one

#### Scenario: Removing the only plant on the last page
- **WHEN** the user is on page 2 which holds a single plant and removes it
- **THEN** the system shows page 1 instead of an empty page 2

#### Scenario: Cancelled removal
- **WHEN** the user chooses to remove a plant and cancels the confirmation
- **THEN** the plant stays in the collection unchanged

#### Scenario: Removed plant's reminder is deleted
- **WHEN** the user removes a plant that was due for watering
- **THEN** the plant's calendar reminder is deleted (see the calendar-reminders capability)

### Requirement: Collection persists between sessions
The system SHALL keep the user's plants and their watering state when the application is closed and reopened.

#### Scenario: Reopen the application
- **WHEN** the user adds two plants, closes the application and opens it again
- **THEN** the same two plants appear with the same remaining days until watering, adjusted for the time that has passed

### Requirement: Card click shows detailed care instructions
The system SHALL show a plant's detailed care instructions, including its light requirements and watering schedule, when the user clicks the plant's card. The same view SHALL offer the "Watered" action for that plant.

#### Scenario: Open plant details
- **WHEN** the user clicks a plant's card
- **THEN** the system shows a details view with the plant's photo, name, light requirements, watering schedule and the "Watered" button

#### Scenario: Close plant details
- **WHEN** the details view is open and the user closes it
- **THEN** the system returns to the grid with no data changed
