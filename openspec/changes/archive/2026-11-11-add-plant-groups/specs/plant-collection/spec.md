## RENAMED Requirements
- FROM: `### Requirement: Homepage shows plants as cards in a paged grid`
- TO: `### Requirement: A group's collection view shows plants as cards in a paged grid`

## MODIFIED Requirements

### Requirement: A group's collection view shows plants as cards in a paged grid
The system SHALL display a group's plants (or every plant, for "All") as cards arranged in a grid of three columns by two rows, showing at most six cards per page. Each card SHALL show the plant's photo, name and watering status. When the scoped set has more than six plants, the system SHALL provide page controls to move between pages, and SHALL show which page is current and how many pages there are. This view is reached by opening a card on the landing page (see the plant-groups capability), not shown directly when the application opens.

#### Scenario: Plants are shown as cards
- **WHEN** the user opens a group (or "All") with six plants
- **THEN** the system shows six cards in a grid of three columns by two rows, each with photo, name and watering status, and no page controls

#### Scenario: Empty collection
- **WHEN** the user opens a group (or "All") with no plants
- **THEN** the system shows an empty grid with the "+ Add New Plant" button still available

#### Scenario: More plants than fit on one page
- **WHEN** the scoped set has seven plants
- **THEN** the system shows the first six on page 1 of 2, and the seventh alone on page 2

#### Scenario: Move between pages
- **WHEN** the scoped set has seven plants and the user activates the "next page" control on page 1
- **THEN** the system shows page 2 with the seventh plant, and a "previous page" control returns to page 1

#### Scenario: Page controls at the ends
- **WHEN** the user is on the first page, or on the last page, of a scoped set
- **THEN** the "previous page" control is unavailable on the first page and the "next page" control is unavailable on the last page

#### Scenario: Adding a plant to a full last page
- **WHEN** the scoped set has six plants and the user adds a seventh to that same scope
- **THEN** the system shows page 2 of 2 containing the new plant, or otherwise keeps the user on a page that lets them reach it
