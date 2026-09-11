# Achievements (WIP)

See [SCHEMA.md](SCHEMA.md#achievement-ach-schema) for the `ACH.<id>` key shape. This file tracks the ID →
actual-achievement mapping, which isn't available from the save alone.

Achievement IDs appear to be identical between the PC and Switch versions; Nutaku, who is not present in the Switch
version of the game, still has her achievement ID but it is never set.

## Bitmask-per-tier mechanism

Each `ACH.<id>` value is a bitmask where one bit = one tier/level of that achievement. Every bit that gets newly set
increments the root-level `AchievementCount` by exactly 1.

Achievements for girls track the highest Love level ever reached for that Girl across resets. Similarly, Job/Hobby
achievements track the highest Job/Hobby level ever achieved across resets.

## Mapping (Incomplete)

| ID | Name                           |
|----|--------------------------------|
| 0  | Cassie (Level)                 |
| 1  | Mio (Level)                    |
| 2  | Quill (Level)                  |
| 3  | Elle (Level)                   |
| 4  | Nutaku (Level)[^1]             |
| 5  | Iro (Level)                    |
| 6  | Bonnibel (Level)               |
| 7  | Ayano (Level)                  |
| 8  | Fumi (Level)                   |
| 9  | Bearverly (Level)              |
| 10 | Nina (Level)                   |
| 11 | Alpha (Level)                  |
| 12 | Pamu (Level)                   |
| 13 | Luna (Level)                   |
| 14 | Eva (Level)                    |
| 15 | Karma (Level)                  |
| 16 | Sutra (Level)                  |
| 17 | Dark One (Level) (Unconfirmed) |
| 18 | Q-piddy (Level) (Unconfirmed)  |
| 19 | Fast Food (Level)              |
| 20 | Restaurant (Level)             |
| 21 | Cleaning (Level)               |
| 22 | Lifeguard (Level)              |
| 23 | Artist (Level)                 |
| 24 | Computers (Level)              |
| 25 | Zoo (Level)                    |
| 26 | Hunting (Level)                |
| 27 | Gambler (Level)                |
| 28 | Sports (Level)                 |
| 29 | Paralegal (Level)              |
| 30 | Actor (Level)                  |
| 31 | Space (Level)                  |
| 32 | Demon Hunter (Level)           |
| 33 | Love Doctor (Level)            |
| 34 | Wizard (Level)                 |
| 35 | Money (Lifetime)               |
| 36 | Money (Bank)                   |
| 37 | All Jobs (Level)               |
| 38 | Dates (Lifetime)               |
| 39 | Gifts (Lifetime)               |
| 40 | Hearts (Total)                 |
| 41 | Playtime                       |
| 42 | Hobby Unlocks                  |
| 43 | Endings (Unconfirmed)          |
| 44 | Reset Bonus (Unconfirmed)      |
| 55 | Catara (Level)                 |
| 57 | Peanut (Level) (Unconfirmed)   |
| 79 | Event Participation            |

[^1]: Not available on Switch.