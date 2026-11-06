## MODIFIED Requirements

### Requirement: Light and watering needs come from the bundled list
Each plant type in the bundled list SHALL have light requirements, a watering interval expressed as a whole number of days, a toxicity-to-pets rating, a humidity preference and a short propagation tip. When a plant type is selected, the system SHALL fill in these values automatically, without the user entering any of it.

#### Scenario: Care data filled in for a selected plant
- **WHEN** the user selects "Monstera"
- **THEN** the new card shows the plant's light requirements, a watering interval in days, a toxicity-to-pets rating, a humidity preference and a propagation tip

#### Scenario: Works without internet
- **WHEN** the device has no internet connection
- **THEN** the user can still search the bundled plants, add one, see its light, watering, toxicity, humidity and propagation information and use the watering countdown

#### Scenario: Toxicity not evaluated for a species
- **WHEN** the selected plant type's toxicity has no published ASPCA rating
- **THEN** the system shows "Unknown/not evaluated" for toxicity instead of guessing
