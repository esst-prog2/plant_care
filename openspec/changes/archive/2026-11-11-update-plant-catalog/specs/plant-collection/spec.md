## MODIFIED Requirements

### Requirement: Card click shows detailed plant information
The system SHALL show a plant's light requirements, watering interval, toxicity-to-pets rating, humidity preference and propagation tip when the user clicks the plant's card. Light, watering, humidity and propagation are shown as starting-point estimates rather than a verified schedule; toxicity is shown as a rating drawn from the ASPCA's published plant list rather than a general-knowledge guess, and is not a substitute for veterinary advice. The same view SHALL offer the "Watered" action for that plant.

#### Scenario: Open plant details
- **WHEN** the user clicks a plant's card
- **THEN** the system shows a details view with the plant's photo, name, light requirements, watering schedule, toxicity-to-pets rating, humidity preference, propagation tip and the "Watered" button

#### Scenario: Close plant details
- **WHEN** the details view is open and the user closes it
- **THEN** the system returns to the grid with no data changed

#### Scenario: Plant added before toxicity, humidity and propagation existed
- **WHEN** the user opens the details view of a plant added before these fields were introduced
- **THEN** the system shows "Not available" for toxicity, humidity and propagation instead of an error
