# Events

Events come in two forms: ***parallel events** (PEs) and **limited-time events** (LTEs). Parallel events track their own
state in a `pes`-prefixed set of keys, likely because there is a separate game section for these (such as Fuzzy
Festival). LTEs are simply task-based token accumulation and therefore do not get their own "namespace".

## Parallel Events

The table below lists known parallel events and their event IDs:

| ID | Event          | Date           | Girl            |
|----|----------------|----------------|-----------------|
| 27 | Fuzzy Festival | N/A (Paid DLC) | Ginger & Wasabi |
| ?? | Frosty         | February 2026  | Aurora          |
| ?? | School Spirit  | March 2026     | Kyoko           |
| ?? | Spring Fling   | April 2026     | Penny           |
| ?? | Spooky         | April 2026     | Nightingale     |
| ?? | Outer Space    | May 2026       | Loola           |
| ?? | High Fantasy   | June 2026      | Moonbeam        |
| 53 | Valentine's    | June 2026      | Marybelle       |
| 54 | Beach Bash     | July 2026      | Nixie           |
| 55 | Time Warp      | August 2026    | Polly           |
| 56 | School Spirit  | September 2026 | Ling Ling       |

### Schemas

All parallel event keys are prefixed with `pes` and their event ID (`pes<NN>`; see above). The following table is an
inferred generic schema for parallel events (excluding the mirrored keys from the root schema):

| Sub-key                                                                      | Shape   | Represents                                                                                        |
|------------------------------------------------------------------------------|---------|---------------------------------------------------------------------------------------------------|
| `Goals`                                                                      | `int`   | Bitmask of the goals culminating in unlocking whatever the parallel event is for                  |
| `PurchasedTime`                                                              | `int`   |                                                                                                   |
| `Start` (note: prefix is capital `P`, unlike every other parallel event key) | `long`  | Timestamp, shape consistent with `DateTime.ToBinary()` — when the event was started by the player |
| `TimeMultiplier`                                                             | `float` | Same meaning as root `TimeMultiplier`, scoped to this event                                       |

For the known events, the following describes the keys unique to that event.

#### Fuzzy Festival

##### Hobbies

Its `Hobby<Name>` instances use a **different 12 names** than the root profile: `Bravery`, `Caring`, `Charisma`,
`Creative`, `Focus`, `Innovation`, `Luck`, `Optimism`, `Peaceful`, `Responsible`, `Tenderness`, `Trustworthy`.

#### Beach Bash

##### Girls

The following Girls are available in the Beach Bash parallel event, with corresponding entries: Iro, Roxxy, Nova,
Lustat, Shibuki, Sutra and Nixie.

##### Hobbies

Its `Hobby<Name>` instances use a **different 12 names** than the root profile: `Adventurous`, `Brave`, `Buff`,
`Competetive`, `Cool`, `Culinary`, `Easygoing`, `Healthy`, `Independent`, `Patience`, `Sentimental`, `Thorough`.

#### Time Warp

##### Girls

The following Girls are available in the Time Warp parallel event, with corresponding entries: Polly, Bearverly,
Vellatrix, Shibuki and Honey.

##### Hobbies

Its `Hobby<Name>` instances use a **different 12 names** than the root profile: `Communication`, `Creativity`,
`Elegance`, `Experimentation`, `Fashion`, `Focus`, `Observant`, `Patience`, `Science`, `Stamina`, `Strength`, `Taste`.

##### Other keys

`Girl<name>LoveHighMark` (`int`) tracks each girl's highest `Love` value reached, with the girl's name lowercased
instead of the usual `Girl<Name>` capitalization, e.g. `Girl` + `bearverly` + `LoveHighMark`. This is likely used to
prevent you from getting Time Crystals for progress after a soft reset (as opposed to tracking this with achievements as
I suspect the main game does).

`GameStateTimeline` tracks the current Timeline you are in for the event.

`GameStateTimeCrystalCount` (`int`) tracks the count of Time Crystals obtained throughout the event - one is awarded per
novel Love-level-up across any of the event's Girls (re-reaching a level already hit before does not grant another).
TimeCrystals are consumed to "Time Warp" (soft reset).

---------

## Limited-time Events (LTEs)

The game only seems to store the current achieved tokens and the previous event tokens. This is likely so that it can
calculate the cost (in diamonds) to complete the previous event if you were short of tokens.

The current event ID is tracked under the root `EventID` with tokens for the current and previous events stored under
`Event<N>Tokens`. The current `Event<N>Tokens` likely remains empty until the `Task` entries are rotated out for the
next event.

`Task` entries are removed when the event rolls over to the next one and then populated with however many `Task` keys
are required. Usually the amount of Tasks is calculated as `3 * eventDuration`, i.e. 3 tasks per day, but this can vary
according to the event.

### Duration

LTEs that unlock either a Girl or her outfits seem to run for 14 days while Pinup LTEs only run for 7. The singular
known exception to this rule is the "Newcomer" event which is only 1 day long (presumably so you can finish it in a
single sitting and not miss out if you forget to play the game subsequently).

When first introduced (2017), all LTEs were ~7 days long and alternated roughly between Outfit and Pinup LTEs. As of
2019, the current Girl-Outfit-Pinup pattern commenced, although still at 7 days each.

### Known LTEs:

For a full list of historical LTEs, see the [Crush Crush Wiki](https://crush-crush.fandom.com/wiki/Weekly_Event)
or [Sad Panda Studios Wiki](https://wiki.sadpandastudios.com/Weekly_Event). This includes LTEs that are tracked in the
`Completed.20nnEvents` keys.

#### Weekly Events (PC)

The table below is derived from the information at the wiki above. It may or may not be correct. If you are going to use
this information to flip bits for `Completed.20xx.Events`, bear in mind that it is unlikely that a real save would have
every bit flipped since the bring-backs/repeats would be skipped in subsequent years.

| Year | Events | Of Which Bring-Backs |
|------|--------|----------------------|
| 2017 | 12     | 0                    |
| 2018 | 48     | 2                    |
| 2019 | 41     | 9                    |
| 2020 | 32     | 7                    |
| 2021 | 21     | 8                    |

The table below maps current event IDs (i.e. those for `Completed.Events`) to known events and gives their duration:

| ID  | Event                 | Duration |
|-----|-----------------------|----------|
| 118 | Newcomer              | 1 Day    |
| 307 | Roxxy                 | 14 Days  |
| 308 | Roxxy's Outfits       | 14 Days  |
| 309 | Peanut Phone Pinup    | 7 Days   |
| 310 | Sirina                | 14 Days  |
| 311 | Sirina's Outfits      | 14 Days  |
| 312 | Sawyer and Lake Pinup | 7 Days   |
| 313 | Tessa                 | 14 Days  |
| ??? | Tessa's Outfits       | 14 Days  |
| ??? | Alpha's Pinup         | 7 Days   |
| ??? | Esper                 | 14 Days  |
| ??? | Esper's Outfits       | 14 Days  |
| ??? | School Pinup          | 7 Days   |
| ??? | Rosa                  | 14 Days  |
| ??? | Rosa's Outfits        | 14 Days  |
| ??? | Holiday Pinup         | 7 Days   |
| ??? | Odango                | 14 Days  |
| ??? | Odango's Outfits      | 14 Days  |

#### Weekly Events (Switch)

Switch LTEs always seem to run for 7 days instead of the 7/14 for PC.

| ID | Event               |
|----|---------------------|
| 47 | Jelle (Unconfirmed) |
| 48 | Quillzone           |
| 49 | Bonchovy            |
| 50 | Spectrum            |