# plant-care-data Specification

## Purpose

Supplies the plant types the user can search for, with light requirements and a watering interval from a bundled list of common houseplants, plus a photo and short description fetched from Wikipedia, while staying usable when there is no internet.

## Requirements

### Requirement: Plant types are searchable by name
The system SHALL let the user search plant types by name in a bundled list of common houseplants and SHALL return the matching plant types with a display name. The list SHALL include at least Monstera and Pilea.

#### Scenario: Search returns matches
- **WHEN** the user searches for "Monstera"
- **THEN** the system returns a plant type named Monstera

#### Scenario: Search is case-insensitive and matches part of a name
- **WHEN** the user searches for "monstera", "MONSTERA" or "mons"
- **THEN** the system returns the same Monstera match each time

#### Scenario: Nothing matches
- **WHEN** the user searches for text that is in no plant name
- **THEN** the system returns no results

### Requirement: Light and watering needs come from the bundled list
Each plant type in the bundled list SHALL have light requirements and a watering interval expressed as a whole number of days. When a plant type is selected, the system SHALL fill in these values automatically, without the user entering any of it.

#### Scenario: Care data filled in for a selected plant
- **WHEN** the user selects "Monstera"
- **THEN** the new card shows the plant's light requirements and a watering interval in days

#### Scenario: Works without internet
- **WHEN** the device has no internet connection
- **THEN** the user can still search the bundled plants, add one, see its light and watering information and use the watering countdown

### Requirement: The photo and a short description are fetched automatically
When a plant is added, the system SHALL automatically fetch the plant's photo and a short description from Wikipedia. The details view SHALL show the description and a link to the Wikipedia article as the credit for the photo and text.

#### Scenario: Photo and description retrieved
- **WHEN** the user selects "Monstera" and Wikipedia is reachable
- **THEN** the new card shows a photo of the plant, and its details view shows a short description with a link to the Wikipedia article

#### Scenario: Card shown while data is loading
- **WHEN** the user selects a plant type and the data has not yet arrived
- **THEN** the system shows the card with a loading indication and updates it when the data arrives

### Requirement: A missing online photo never stops a plant from being added
If Wikipedia cannot be reached, rejects the request or returns an error, the system SHALL still add the plant with its light and watering information from the bundled list and a placeholder illustration instead of the photo, and SHALL tell the user that offline data was used. If Wikipedia is reachable but has no picture for the plant, the system SHALL show the placeholder without that notice.

#### Scenario: Wikipedia unavailable
- **WHEN** the user adds a plant and Wikipedia cannot be reached
- **THEN** the plant is added with its bundled care data and a placeholder image, and the card and details view show a notice that offline data was used

#### Scenario: No picture on the article
- **WHEN** Wikipedia is reachable but the plant's article has no picture
- **THEN** the plant is added with the placeholder image and no offline notice

### Requirement: Fetched data is stored with the plant
The system SHALL store the photo, description, credit link, light requirements and watering interval with the plant when it is added, so that later views of the plant do not depend on internet access.

#### Scenario: Details viewed without internet
- **WHEN** a plant was added while Wikipedia was reachable and the internet is later unavailable
- **THEN** the plant's card and details still show the stored photo, description, light requirements and watering interval
