## MODIFIED Requirements

### Requirement: Light and watering needs come from the bundled list
Each plant type in the bundled list SHALL have light requirements and a starting watering interval expressed as a whole number of days. When a plant type is selected, the system SHALL fill in light requirements automatically from the bundled list, without the user entering any of it. The system SHALL fill in a starting watering interval from the bundled list, which the user MAY refine for this specific plant via the optional condition questions (see "User can refine the starting interval with this plant's conditions").

#### Scenario: Care data filled in for a selected plant
- **WHEN** the user selects "Monstera"
- **THEN** the new card shows the plant's light requirements and a watering interval in days

#### Scenario: Works without internet
- **WHEN** the device has no internet connection
- **THEN** the user can still search the bundled plants, add one, see its light and watering information and use the watering countdown

## ADDED Requirements

### Requirement: User can refine the starting interval with this plant's conditions
Before a plant is added, after its type has been selected, the system SHALL offer the user a small set of optional questions about that specific plant's light, warmth and pot/soil situation. Each answered question SHALL adjust the bundled starting interval by a fixed, documented amount for that answer; leaving a question unanswered SHALL NOT change the interval for that question. Skipping every question SHALL leave the plant's starting interval exactly equal to the bundled default for its type. The adjusted starting interval SHALL stay within a documented minimum and maximum number of days.

#### Scenario: All questions skipped
- **WHEN** the user adds a plant without answering any condition question
- **THEN** the plant's starting interval is exactly the bundled default for its type

#### Scenario: One condition answered
- **WHEN** the user answers only the light question with a non-default option, and leaves the warmth and pot/soil questions unanswered
- **THEN** the plant's starting interval differs from the bundled default by exactly that answer's fixed adjustment

#### Scenario: Starting interval stays within bounds
- **WHEN** the combined adjustment from the answered questions would put the starting interval below the documented minimum, or above the documented maximum
- **THEN** the starting interval is clamped to that minimum or maximum instead of going further
