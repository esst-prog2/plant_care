## MODIFIED Requirements

### Requirement: User can create, rename and delete a group
The system SHALL let the user create a group by typing a name, rename an existing group, and delete a group. Deleting a group SHALL require a confirmation. Deleting a group SHALL NOT delete its plants; they SHALL become unassigned and appear under "All" and no other group. The "All" card SHALL also be renamable, but SHALL NOT be deletable. The system SHALL let the user choose the group's cover image, either a built-in preset icon or an uploaded photo, when creating a group and later when editing it; a group whose cover has never been chosen SHALL keep showing an image automatically derived from its first-added plant's photo.

#### Scenario: Create a group
- **WHEN** the user activates "+ New Group" and types "Living room"
- **THEN** a new "Living room" card appears on the landing page with a plant count of zero

#### Scenario: Create a group with a preset cover
- **WHEN** the user creates a group and picks a built-in preset icon before confirming
- **THEN** the new group's card shows that preset icon as its cover, not the automatic first-plant cover

#### Scenario: Create a group with an uploaded cover
- **WHEN** the user creates a group and uploads a valid image file as its cover
- **THEN** the new group's card shows that uploaded image as its cover

#### Scenario: Change a group's cover later
- **WHEN** the user edits an existing group and picks a different preset, or uploads a new photo
- **THEN** the group's card immediately shows the newly chosen cover

#### Scenario: Invalid cover upload is rejected
- **WHEN** the user uploads a file that is not a supported image type, or over the existing size limit, while creating or editing a group
- **THEN** the group's cover is unchanged (the automatic cover if none was set, or the previous chosen cover) and an inline message explains the upload was rejected

#### Scenario: Rename a group
- **WHEN** the user renames "Living room" to "Lounge"
- **THEN** the landing page shows the updated name, and plants previously assigned to it remain assigned to the same group under its new name

#### Scenario: Delete a group and confirm
- **WHEN** the user deletes a group that has plants in it and confirms
- **THEN** the group's card disappears from the landing page, and its former plants still appear under "All" with no group assigned

#### Scenario: Deleting a group with an uploaded cover removes the file
- **WHEN** the user deletes a group whose cover is a photo they uploaded
- **THEN** the uploaded file is removed, while a group deleted with a preset cover never removes any shared preset asset

#### Scenario: Cancelled delete
- **WHEN** the user starts deleting a group and cancels the confirmation
- **THEN** the group and its plants are unchanged

#### Scenario: Rename "All"
- **WHEN** the user renames the "All" card to "Everything"
- **THEN** the landing page's card and the switch control in every scoped collection view show "Everything" instead of "All", and no delete control, and no cover picker, is offered for it
