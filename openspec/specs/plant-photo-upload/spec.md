# plant-photo-upload Specification

## Purpose

Lets the user replace an already-added plant's shown photo with their own image file, so the collection can show the user's actual plant instead of the species' generic Wikipedia picture.

## Requirements

### Requirement: User can upload a photo for an existing plant
The system SHALL let the user choose an image file for a plant from the plant's details view and upload it to replace the currently shown photo (whether that is the automatically-fetched Wikipedia photo or the placeholder). The uploaded photo SHALL be shown immediately and SHALL persist like any other stored plant data.

#### Scenario: Successful upload replaces the shown photo
- **WHEN** the user uploads a valid image file for a plant
- **THEN** the plant's details view and its card show the uploaded photo instead of the previous one, without needing to reload the page

#### Scenario: Uploaded photo takes priority permanently
- **WHEN** a plant already has a user-uploaded photo
- **THEN** nothing else in the system (adding the plant again is not possible; no background process re-fetches a photo) ever replaces it except another upload by the user

### Requirement: Upload is validated the same way an automatic photo download is
The system SHALL accept only the image types already supported for automatically-downloaded photos and SHALL reject a file over the existing size limit, without adding the plant's photo or losing the existing one.

#### Scenario: Unsupported file type
- **WHEN** the user uploads a file that is not one of the supported image types
- **THEN** the system keeps the plant's current photo unchanged and shows an inline message explaining the upload was rejected

#### Scenario: File too large
- **WHEN** the user uploads an image larger than the existing size limit
- **THEN** the system keeps the plant's current photo unchanged and shows an inline message explaining the upload was rejected

#### Scenario: Upload for a plant that is not ready yet
- **WHEN** the user attempts to upload a photo for a plant whose data is still loading or failed
- **THEN** the system does not accept the upload

### Requirement: Photo credit reflects a user-uploaded photo
Once a plant's photo has been replaced by a user upload, the system SHALL stop crediting that photo to Wikipedia. A Wikipedia-sourced description shown alongside the photo SHALL keep its own text attribution.

#### Scenario: Credit line after an upload
- **WHEN** the user opens the details view of a plant whose photo was replaced by an upload, and the plant still has a Wikipedia description
- **THEN** the system shows the text attribution to Wikipedia but does not claim the photo is from Wikipedia

#### Scenario: Credit line before any upload
- **WHEN** the user opens the details view of a plant whose photo has never been replaced
- **THEN** the system shows the combined photo-and-text attribution to Wikipedia as before, unchanged by this capability
