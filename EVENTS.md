# Events

## Mapping
Currently, the suspected event mapping is:

| Event                     | Prefix  |
|---------------------------|---------|
| Fuzzy Festival (Paid DLC) | `pes27` |
| Roxxy                     | `pes53` |
| Roxxy (Outfits)           | `pes54` |

## Schemas

### Fuzzy Festival (`pes27`)

| Sub-key                                                          | Shape   | Represents                                                                                                            |
|------------------------------------------------------------------|---------|-----------------------------------------------------------------------------------------------------------------------|
| `pes27Goals` (also `pes53Goals`)                                 | `int`   | Bitmask, purpose unconfirmed; likely a bitmask of the goals culminating in unlocking Ginger & Wasabi in the core game |
| `pes27PurchasedTime`                                             | `int`   |                                                                                                                       |
| `Pes27Start` (note capital `P`, unlike every other `pes27*` key) | `long`  | Timestamp, shape consistent with `DateTime.ToBinary()` — when the event was started by the player                     |
| `pes27TimeMultiplier`                                            | `float` | Same meaning as root `TimeMultiplier`, scoped to this event                                                           |

Its `Hobby<Name>` instances use a **different 12 names** than the root
profile: `Bravery`, `Caring`, `Charisma`, `Creative`, `Focus`,
`Innovation`, `Luck`, `Optimism`, `Peaceful`, `Responsible`,
`Tenderness`, `Trustworthy`.
