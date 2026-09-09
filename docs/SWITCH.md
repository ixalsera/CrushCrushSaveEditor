# Switch vs PC Save Differences

Keys present in a Switch save that are absent from the PC saves sampled for this project.

Hobby/Job/Task field gaps between the PC and Switch key sets are deliberately left out of this file.

## GameState (root-level, always initialized)

| Key                         | Shape   | What we know                                                                                         |
|-----------------------------|---------|------------------------------------------------------------------------------------------------------|
| `GameStateBoost2EndTime`    | `long`? | Likely a holdover from the mobile version; ad-powered Speed Boost end timestamp                      |
| `GameStateTimeSkip2EndTime` | `long`? | Likely a holdover from the mobile version; ad-powered Time Skip end timestamp                        |
| `GameStateCreated`          | `long`? | Likely a save/account creation timestamp, distinct from `Date`/`DateUTC` which update on every write |
| `GameStateDateOffset`       | ?       | Likely a clock-drift or timezone offset paired with `Date`/`DateUTC`                                 |
| `GameStateCovid2020`        | `int`   | Unknown. Likely a flag for the short COVID phone fling                                               |

## Settings (root-level, always initialized)

| Key                    | Shape  | What we know                          |
|------------------------|--------|---------------------------------------|
| `SettingsIntrosOff`    | `flag` | Whether intro cutscenes are disabled  |
| `SettingsParticlesOff` | `flag` | Whether particle effects are disabled |
| `SettingsPopupsOff`    | `flag` | Whether image popups are disabled     |
| `SettingsLanguage`     | ?      | Selected UI language                  |

## Tutorial

| Key                 | Shape  | What we know                                                                                                |
|---------------------|--------|-------------------------------------------------------------------------------------------------------------|
| `ActiveTutorial`    | ?      | Likely which specific tutorial sequence is currently active, alongside the existing `Tutorial` step counter |
| `TutorialStep`      | `int`  | A separate step counter from root `Tutorial`.                                                               |
| `TutorialAffection` | `flag` | Likely a completion flag for an "affection" tutorial step                                                   |

## Misc top-level

| Key                   | Shape                         | What we know                                                                                 |
|-----------------------|-------------------------------|----------------------------------------------------------------------------------------------|
| `CabinFeverSave`      | `int`                         | Whether a save file from "Cabin Fever" was detected. Unlocks Mallory                         |
| `PendingTimelord`     | ?                             | Unknown                                                                                      |
| `UserLteOffset`       | `int`                         | Unknown. Possibly an adjustment applied when resolving the "current" LTE from root `EventID` |
| `PlayfabAwardedItems` | `blob` (base64 of plain text) | Likely Switch's equivalent of PC's documented `BlayfapAwardedItems`                          |
| `album0`-`album5`     | `int`                         | Memory Album unlock trackers                                                                 |
| `AyanoChibi2017`      | `int`                         | Unknown. Likely a tracker for the "Don't Notice Me, Senpai" event                            |
| `AyanoTimeBlock`      | `int`                         | Unknown. Likely whether the time block reward was unlocked from the above event              |
| `CurrentPanel`        | `string`                      | Likely which UI panel/tab was open when the save was written                                 |
| `NutakuItems2019`     | `int`                         | Unknown                                                                                      |
