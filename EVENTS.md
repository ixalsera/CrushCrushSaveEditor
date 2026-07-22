# Events

Events appear to come in two forms: parallel events and limited-time events. Parallel events appear to track their own state in a `pes`-prefixed set of keys,
likely because there is a separate game section for these (such as Fuzzy Festival). LTEs are simply task based token accumulation and therefore do not get
their own `pes` "namespace".

## Parallel Events
Currently, the suspected event mapping is:

| Event                                             | Prefix                                                                             |
|---------------------------------------------------|------------------------------------------------------------------------------------|
| Fuzzy Festival (Paid DLC)                         | `pes27`                                                                            |

### Schemas
#### Fuzzy Festival (`pes27`)

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

## Limited-time Events (LTEs)
The game only seems to store the current achieved tokens and the previous event tokens. This is likely so
that it can calculate the cost (in diamonds) to complete the previous event if you were short of tokens.

The current event ID is tracked under the root `EventID` with tokens for the current and previous events
stored under `Event<N>Tokens`. The current `Event<N>Tokens` likely remains empty until the `Task` entries
are rotated out for the next event.

`Task` entries are removed when the event rolls over to the next one and then populated with however many `Task` keys are required.
Usually the amount of Tasks is calculated as `3 * eventDuration`, i.e. 3 tasks per day.

Known Event IDs:

| Event ID | Event           | Duration |
|----------|-----------------|----------|
| 118      | Newcomer        | 1 Day    |
| 307      | Roxxy           | 14 Days  |
| 308      | Roxxy's Outfits | 14 Days  |
| 309      | Peanut Pinup    | 7 Days   |
