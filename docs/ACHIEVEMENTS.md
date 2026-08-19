# Achievements (WIP)

See [SCHEMA.md](SCHEMA.md#achievement-ach-schema) for the `ACH.<id>` key shape. This file tracks the ID →
actual-achievement mapping, which isn't available from the save alone.

## Bitmask-per-tier mechanism

Each `ACH.<id>` value is a bitmask where one bit = one tier/level of that achievement, not a single flag. Every bit that
gets newly set increments the root-level `AchievementCount` by exactly 1.

## Mapping (Incomplete)

| ID | Name           |
|----|----------------|
| 14 | Eva (Level)    |
| 55 | Catara (Level) |
