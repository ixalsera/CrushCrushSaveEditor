# Events

Events appear to come in two forms: parallel events (PEs) and limited-time events (LTEs). Parallel events appear to track their own
state in a `pes`-prefixed set of keys, likely because there is a separate game section for these (such as Fuzzy
Festival). LTEs are simply task based token accumulation and therefore do not get their own `pes` "namespace".

## Parallel Events

The table below lists known parallel events and their event IDs:

| ID   | Event                            | Date            |
|------|----------------------------------|-----------------|
| 27   | Fuzzy Festival (Ginger & Wasabi) | N/A (Paid DLC)+ |
| 53   | Valentines Event (Marybelle)     | June 2026       |
| 54   | Beach Bash (Nixie)               | July 2026       |

### Schemas

All event keys are prefixed with `pes` and their event ID (`pes<NN>`). The following table is an inferred generic schema for parallel
events based on only one dataset (excluding the mirrored keys from the root schema):

| Sub-key                                                                      | Shape   | Represents                                                                                                              |
|------------------------------------------------------------------------------|---------|-------------------------------------------------------------------------------------------------------------------------|
| `Goals`                                                                      | `int`   | Bitmask, purpose unconfirmed; likely a bitmask of the goals culminating in unlocking whatever the parallel event is for |
| `PurchasedTime`                                                              | `int`   |                                                                                                                         |
| `Start` (note: prefix is capital `P`, unlike every other parallel event key) | `long`  | Timestamp, shape consistent with `DateTime.ToBinary()` — when the event was started by the player                       |
| `TimeMultiplier`                                                             | `float` | Same meaning as root `TimeMultiplier`, scoped to this event                                                             |

For the known events, the following describes the keys unique to that event.

#### Fuzzy Festival (`pes27`)

##### Hobbies
Its `Hobby<Name>` instances use a **different 12 names** than the root profile: `Bravery`, `Caring`, `Charisma`,
`Creative`, `Focus`, `Innovation`, `Luck`, `Optimism`, `Peaceful`, `Responsible`, `Tenderness`, `Trustworthy`.

#### Beach Bash (`pes54`)

##### Girls
The following Girls are available in the Beach Bash parallel event, with corresponding entries: Iro, Roxxy, Nova, Shibuki, Sutra, Lustat and Nixie.

##### Hobbies
Its `Hobby<Name>` instances use a **different 12 names** than the root profile: `Adventurous`, `Brave`, `Buff`,
`Competetive`, `Cool`, `Culinary`, `Easygoing`, `Healthy`, `Independent`, `Patience`, `Sentimental`, `Thorough`.

## Limited-time Events (LTEs)

The game only seems to store the current achieved tokens and the previous event tokens. This is likely so that it can
calculate the cost (in diamonds) to complete the previous event if you were short of tokens.

The current event ID is tracked under the root `EventID` with tokens for the current and previous events stored under
`Event<N>Tokens`. The current `Event<N>Tokens` likely remains empty until the `Task` entries are rotated out for the
next event.

`Task` entries are removed when the event rolls over to the next one and then populated with however many `Task` keys
are required. Usually the amount of Tasks is calculated as `3 * eventDuration`, i.e. 3 tasks per day, but this can vary
according to the event.

Known Event IDs:

| ID  | Event              | Duration |
|-----|--------------------|----------|
| 118 | Newcomer           | 1 Day    |
| 307 | Roxxy              | 14 Days  |
| 308 | Roxxy's Outfits    | 14 Days  |
| 309 | Peanut Phone Pinup | 7 Days   |
