## ADDED Requirements

### Requirement: User can give feedback after watering that adjusts the interval
After pressing "Watered", the system SHALL offer the user an optional, dismissible choice between three outcomes for that watering: "soil was still wet", "leaf was drooping", or "right on time". Choosing "soil was still wet" SHALL lengthen the plant's interval, used for future waterings, by a small fixed number of days. Choosing "leaf was drooping" SHALL shorten it by the same fixed number of days. Choosing "right on time", or dismissing the choice without picking one, SHALL leave the interval unchanged. The interval SHALL stay within a documented minimum and maximum number of days regardless of how much feedback accumulates over time.

#### Scenario: Soil was still wet
- **WHEN** the user presses "Watered" and then chooses "soil was still wet"
- **THEN** the plant's interval for future waterings is longer than it was before, by the fixed adjustment

#### Scenario: Leaf was drooping
- **WHEN** the user presses "Watered" and then chooses "leaf was drooping"
- **THEN** the plant's interval for future waterings is shorter than it was before, by the fixed adjustment

#### Scenario: Right on time
- **WHEN** the user presses "Watered" and then chooses "right on time"
- **THEN** the plant's interval is unchanged

#### Scenario: Dismissed without choosing
- **WHEN** the user presses "Watered" and dismisses the feedback step without choosing any of the three outcomes
- **THEN** the plant's interval is unchanged

#### Scenario: Interval does not run away
- **WHEN** repeated "leaf was drooping" feedback on the same plant would shorten its interval below the documented minimum
- **THEN** the interval stops at the minimum and does not go lower

#### Scenario: Repeated feedback keeps the same shape
- **WHEN** the user next presses "Watered" on a plant whose interval was previously adjusted by feedback
- **THEN** the countdown resets to that plant's current (possibly adjusted) interval, not the bundled default for its type
