# Save Data Schema

This documents the schema of the plaintext produced by decoding a save file. It's derived from a
`../decoded/crushcrush.txt`. Cells are left **blank** where the key's purpose isn't immediately identifiable from the
data alone - these will be filled in as and when they are determined.

For Nintendo Switch-specific entries, see [SWITCH.md](SWITCH.md).

## How to read these tables

- **Key** is the *logical* key name. In the raw decoded text, a `::Name` line starts a section, and every following bare
  line (until the next `::`) is really `Name` + that line's own key concatenated together (see CLAUDE.md). The tables
  below already show the reconstructed logical key.
- **Shape** uses these type labels, inferred from the value-suffix convention observed in the file:

| Suffix                           | Type            | Notes                                                                                                                                                                                                                                                                       |
|----------------------------------|-----------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `i`                              | `int` (32-bit)  |                                                                                                                                                                                                                                                                             |
| `f`                              | `float`         |                                                                                                                                                                                                                                                                             |
| *(none)*                         | `long` (64-bit) | Every unsuffixed numeric value observed fits comfortably in an `int64` and several equal or approach `int64.MaxValue` exactly, but not `int32.MaxValue` — consistent with the underlying field being declared as a 64-bit integer type regardless of its current magnitude. |
| *(bare key, no `:value` at all)* | `flag`          | Presence-only, meaning `true`; the key is omitted entirely when `false`.                                                                                                                                                                                                    |
| base64-looking string            | `blob`          | An embedded base64 chunk, usually a packed bitmask or small binary struct. Some are just base64 of ASCII text (noted where found).                                                                                                                                          |

- Several long, unsuffixed timestamp-looking fields (very large or negative numbers, e.g. `LoginDate`, `DateUTC`,
  `Pes27Start`, `Task*Start`, `C*D`) are consistent with .NET's `DateTime.ToBinary()` encoding (a `long` ticks value
  with the top bits used to tag UTC/Local `DateTimeKind`, which is why some are negative and others exceed the normal
  max-ticks range).
- The `flag` shape's omitted-if-`0`/bare-if-`1` convention may apply to `int` fields generally, not just true booleans —
  `0` omitted, `1` written bare, `2`+ written as `Ni`.
- Where a key has its own set of sub-keys (e.g. `Girl<Name>`), the **Shape** column says `object` and points at that
  key's own schema table further down, instead of repeating its fields inline.
- Numbered/repeating keys (achievements, challenges, tasks, skills) are shown once as a pattern row (e.g. `ACH.<id>`)
  rather than one row per instance.

## Top-level keys

| Key                                                 | Shape                         | Represents                                                                                                                                               |
|-----------------------------------------------------|-------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------|
| `.speedboost.<size>.pri` (`large`/`medium`/`small`) | `int` (`~cost`)               | Diamond cost of a speed-boost purchase, encoded as `~cost` (i.e. `-(cost+1)`).                                                                           |
| `.speedboost.<size>.qty`                            | `int` (`~multiplier`)         | Speed multiplier granted (x2/x8/x64), encoded as `~multiplier`.                                                                                          |
| `.timeblocks.<size>.pri`                            | `int` (`~cost`)               | Diamond cost of a time-block purchase, encoded as `~cost`.                                                                                               |
| `.timeblocks.<size>.qty`                            | `int` (`~count`)              | Number of Time Blocks granted, encoded as `~count`.                                                                                                      |
| `.timeskip.<size>.pri`                              | `int` (`~cost`)               | Diamond cost of a time-skip purchase, encoded as `~cost`.                                                                                                |
| `.timeskip.<size>.qty`                              | `int` (`~hours`)              | Duration granted, in hours, encoded as `~hours`.                                                                                                         |
| `ACH`                                               | `object`                      | See [Achievement schema](#achievement-ach-schema)                                                                                                        |
| `AchievementCount`                                  | `int`                         | Total number of achievements unlocked                                                                                                                    |
| `ana.ev`                                            | `long`                        | ????                                                                                                                                                     |
| `ana.vid`                                           | `long`                        | ????                                                                                                                                                     |
| `AvailableJobs`                                     | `int` (bitmask)               | Bitmask of unlocked jobs, mapped to their internal ID and not alphabetically (i.e. `FAST FOOD` will be bit `0`)                                          |
| `BlayfapAwardedItems`                               | `blob` (base64 of plain text) | Decodes to a literal pipe-delimited list of unlocked Girls and events                                                                                    |
| `C<N>D` (e.g. `C1D`..`C46D`)                        | `long`                        | Phone Fling conversation last-seen. See [Phone Fling schema](#phone-fling-schema)                                                                        |
| `C<N>P` (e.g. `C1P`..`C46P`)                        | `blob`                        | Phone Fling conversation data. See [Phone Fling schema](#phone-fling-schema)                                                                             |
| `Completed`                                         | `object`                      | See [Completed schema](#completed-events-schema)                                                                                                         |
| `CurrentGirl`                                       | `int`                         | Index of the currently selected/active girl; likely only used to restore game state back to this specific girl on launch (instead of jumping to Cassie). |
| `dchk`                                              | `int`                         | ????; I suspect this might stand for "Drift Check" but it could just as well be "Data Checksum"                                                          |
| `Event<ID>Tokens` (e.g. `Event307Tokens`)           | `int`                         | Token/currency count for the numbered limited-time event; likely current and previous event IDs                                                          |
| `EventID`                                           | `int`                         | ID of the currently active limited-time event                                                                                                            |
| `events.popupinfo`                                  | JSON object                   | Per-event popup display tracking: `{"<event-key>": {"shownCount": int, "shownAt": ISO-8601 timestamp}}`                                                  |
| `GameState`                                         | `object`                      | See [GameState schema](#gamestate-schema)                                                                                                                |
| `Girl<Name>`                                        | `object`                      | See [Girl schema](#girl-schema). One instance per girl in the roster (~80+ seen)                                                                         |
| `GirlsPreviouslyUnlocked`                           | `blob` (17-byte bitmask)      | Bitmask, 1 bit per girl in the roster, tracking girls unlocked _at least once this save_.                                                                |
| `GirlsUnlocked`                                     | `blob` (17-byte bitmask)      | Bitmask, 1 bit per girl in the roster, tracking girls unlocked _within this reset_.                                                                      |
| `HasSeenFuzzyExternalPurchaseConfirmation`          | `flag`                        | Whether a specific purchase-confirmation dialog has been shown; no idea what this is for                                                                 |
| `Hobby<Name>`                                       | `object`                      | See [Hobby schema](#hobby-schema). 12 instances seen                                                                                                     |
| `Job<Name>`                                         | `object`                      | See [Job schema](#job-schema). ~20 instances seen                                                                                                        |
| `LastPesId<N>` (`0`-`9`)                            | `string`                      | A recently-seen parallel event ID; slot `N` is a recency-ordered list, not a stat index                                                                  |
| `Playfab`                                           | `object`                      | See [Playfab schema](#playfab-schema)                                                                                                                    |
| `Prereg`                                            | `flag`                        | Likely whether pre-registration content is unlocked; unconfirmed                                                                                         |
| `SaveFileVersion`                                   | `flag`                        | Bare in this sample — expected a version number here; treat as unconfirmed                                                                               |
| `Settings`                                          | `object`                      | See [Settings schema](#settings-schema)                                                                                                                  |
| `Skill<N>` (`0`-`11`)                               | `object`                      | See [Skill schema](#skill-schema)                                                                                                                        |
| `Task`                                              | `object`                      | See [Task schema](#task-schema)                                                                                                                          |
| `TermsVersionAccepted`                              | `flag`                        | Whether the current Terms of Service version has been accepted                                                                                           |
| `ticketboothSeen`                                   | `flag`                        | Whether the "ticket booth" UI element/prompt has been seen                                                                                               |
| `TimeMultiplier`                                    | `float`                       | Current overall time-speed multiplier                                                                                                                    |
| `Tutorial`                                          | `int`                         | Tutorial progress step/stage reached                                                                                                                     |
| `UnlockedPFS`                                       | `blob` (bitmask)              | Bitmask of unlocked Phone Flings. See [FLINGS.md](FLINGS.md) for more information.                                                                       |

## GameState schema

Prefix: `GameState`.

Root-level player state.

| Sub-key               | Shape    | Represents                                                                                                                                                                           |
|-----------------------|----------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `Build`               | `string` | Game build identifier the save was written by (e.g. `447_d0d00b4`)                                                                                                                   |
| `Date`                | `long`   | Timestamp (local time) of when this game state/save file was created, `DateTime.ToBinary()` with `DateTimeKind.Local`. Decodes to the same instant as `DateUTC` (to the millisecond) |
| `DateCount`           | `int`    | Number of dates the user has gone on, in total; unconfirmed                                                                                                                          |
| `DateUTC`             | `long`   | Timestamp (UTC) of when this game state/save file was created, `DateTime.ToBinary()` with `DateTimeKind.Utc`. Agrees with `Date` to the millisecond                                  |
| `Diamonds`            | `long`   | Premium currency balance                                                                                                                                                             |
| `GiftCount`           | `int`    | Total gifts given, across all girls                                                                                                                                                  |
| `HeartCount`          | `long`   | Total affection/heart points accumulated, across all girls                                                                                                                           |
| `Hobbies`             | `int`    | Count or bitmask of unlocked hobbies                                                                                                                                                 |
| `Ids`                 | `string` | SPS ID                                                                                                                                                                               |
| `LoginDate`           | `long`   | Timestamp (UTC) of the last time the game was launched, `DateTime.ToBinary()` with `DateTimeKind.Utc`.                                                                               |
| `Money`               | `long`   | Soft/spendable currency balance                                                                                                                                                      |
| `NSFW`                | `flag`   | Whether NSFW content mode is enabled                                                                                                                                                 |
| `PendingMultiplier`   | `float`  | Current pending Reset Boost multiplier                                                                                                                                               |
| `PokeCount`           | `int`    | Number of times girls have been "poked"                                                                                                                                              |
| `PurchasedMultiplier` | `float`  | Multiplier obtained via a purchase                                                                                                                                                   |
| `Seconds`             | `float`  | Elapsed seconds counter (exact reference point unconfirmed)                                                                                                                          |
| `TotalIncome`         | `long`   | Lifetime total money earned                                                                                                                                                          |
| `TotalTime`           | `int`    | Lifetime total play time (unit unconfirmed — likely seconds or minutes)                                                                                                              |

## Girl schema

Prefix: `Girl<Name>` (e.g. `GirlCassie`, `GirlMio`).

One block per girl. This represents their current level's state as well as some lifetime trackers.

Both `DateCount` and `GiftCount` are suffixed with a number from `1` to `3`, where present. It seems that this
represents in which slot that Gift or Date tracker sits (`Hearts` is always slot 0 of 4). If no progress has been made
towards the Gift/Date, this value is likely to not be present rather than set to 0 (although, see the above note
regarding how the save file treats integer values of `0` and `1`). If the current level does not require Date or Gift
progression in order to level up, the respective entry will not be present.

See [GIRLS.md](GIRLS.md) for more information such as clothing/outfit bit mapping tables.

| Sub-key                       | Shape           | Represents                                                                                 |
|-------------------------------|-----------------|--------------------------------------------------------------------------------------------|
| `Clothing`                    | `int` (bitmask) | Currently equipped clothing/outfit                                                         |
| `DateCount<N>` (`1`-`3` seen) | `int`           | Count of dates completed towards level progress (see above regarding the relevance of `N`) |
| `Dates`                       | `int` (bitmask) | The Date required for progression this level (See [GIRLS.md](GIRLS.md) for mapping)        |
| `GiftCount<N>` (`1`-`3` seen) | `int`           | Count of gifts completed towards level progress (see above regarding the relevance of `N`) |
| `Hearts`                      | `long`          | Accumulated Hearts *for this level*                                                        |
| `LifeDates`                   | `int` (bitmask) | Bitmask of the Dates completed for this Girl (See [GIRLS.md](GIRLS.md) for mapping)        |
| `LifeOutfits`                 | `int` (bitmask) | Lifetime unlocked outfits/costumes for this girl                                           |
| `Love`                        | `int` (`0`-`9`) | Relationship tier; 9 represents "Lover" level                                              |

**Notes and Cautions**:

- `GirlPamulzebub` and `GirlQuillzone` **are** distinct girls with their own independent `Hearts` etc, they are **not**
  sub-objects of Pamu/Quill - there is no real parent-child relationship. They only *look* like sub-keys because the
  save's prefix-compression groups consecutive lines by shared leading substring, and the reconstructed keys
  `GirlPamulzebubHearts`/`GirlQuillzoneHearts` happen to start with the literal text "GirlPamu"/"GirlQuill", so the
  compressor folds them under that `::` section header (rendered as trailing `lzebubHearts`/`zoneHearts` suffix lines).
  Take care when editing: the section header's girl and the trailing suffix-only entries beneath it are different girls.
- Not all girls seem to follow the same shape. Locked girls appear as both:
  ```
  ::
  Girl<NAME>Hearts:0
  ```
  and
  ```
  ::Girl<NAME>
  Hearts:0
  ```
- It's not known whether simply setting a `Girl` object to non-zero will unlock her, although it's unlikely. See the
  root keys `GirlsPreviouslyUnlocked` and `GirlsUnlocked`.

## Hobby schema

Prefix: `Hobby<Name>` (e.g. `HobbyAngst`, `HobbySmart`).

One block per each of the 12 core game hobbies (`Angst`, `Badass`, `Buff`, `Funny`, `Lucky`, `Motivation`, `Mysterious`,
`Smart`, `Suave`, `TechSavvy`, `Tenderness`, `Wisdom`)

This is the base tracking data for a Hobby. Each Hobby is paired with a [Skill](#skill-schema) based on its _in-game
order_ - i.e. `Suave` maps to `Skill1` etc. - where the Skill tracks the total level of the Hobby.
See [Skill schema](#skill-schema) below.

**Notes** — Parallel events that incorporate hobbies use a **different** set of hobby names (see [EVENTS.md](EVENTS.md)
for a list of known Event hobbies).

| Sub-key           | Shape   | Represents                                          |
|-------------------|---------|-----------------------------------------------------|
| `Active`          | `flag`  | Whether this hobby is currently enabled             |
| `MultiplierCount` | `flag`  | Whether this Hobby is "Gilded"                      |
| `Time`            | `float` | Total time invested in this Hobby                   |
| `TimeL`           | `long`  | Time invested in this Hobby _for the current level_ |

## Job schema

Prefix: `Job<Name>` (e.g. `JobART`, `JobZOO`).

One block for each of the core jobs (`ART`, `CASINO`, `CLEANING`, `COMPUTERS`, `FAST FOOD`, `HUNTING`, `LEGAL`,
`LIFEGUARD`, `LOVE`, `MOVIES`, `RESTAURANT`, `SLAYING`, `SPACE`, `SPORTS`, `WIZARD`, `ZOO`) and any DLC exclusive jobs
(`DIGGER` (Charlotte), `PLANTER` (Suzu), `MECH` (Kaiju), `UNKNOWN` (Frost Event)).

| Sub-key      | Shape           | Represents                                                                                      |
|--------------|-----------------|-------------------------------------------------------------------------------------------------|
| `Active`     | `flag`          | Currently working this job                                                                      |
| `Experience` | `long`          | Total XP earned in this job                                                                     |
| `Gilded`     | `flag`          | Whether the job is "Gilded", i.e. has the bonus earnings modifier applied (costing 10 diamonds) |
| `Level`      | `int` (`0`-`9`) | Current job level                                                                               |
| `Locked`     | `flag`          | Whether the job is unlocked. Yes, really. Probably a dev typo.                                  |
| `Time`       | `float`         | Current work timer/progress                                                                     |

## Achievement (`ACH`) schema

Prefix: `ACH`.

Sub-keys are numeric achievement IDs, internal to the game; no name mapping is available from the save alone but can be
inferred. See [ACHIEVEMENTS.md](ACHIEVEMENTS.md) for the ID→name mapping.

| Sub-key pattern | Shape           | Represents                                  |
|-----------------|-----------------|---------------------------------------------|
| `ACH.<id>`      | `int` (bitmask) | Progress/tier value for achievement `<id>`. |

Root-level `AchievementCount` (see top-level table) is the total count these sum/unlock to.

## Phone Fling schema

See [FLINGS.md](FLINGS.md) for the mapping between fling ID and the actual Girl it represents, where relevant.

| Sub-key pattern | Shape  | Represents                                                                                                                                                                        |
|-----------------|--------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `C<N>D`         | `long` | DateTime the conversation was last *viewed* or, if additional requirements are needed to unlock the next message, `int64.MaxValue`. `0` if the fling has not yet started/unlocked |
| `C<N>P`         | `blob` | Packed binary data; see [FLINGS.md](FLINGS.md) for the structure                                                                                                                  |

## Completed events schema

Prefix: `Completed`.

See [EVENTS.md](EVENTS.md) for more information about events.

| Sub-key      | Shape            | Represents                               |
|--------------|------------------|------------------------------------------|
| `2018Events` | `long` (bitmask) | Bitmask of completed weekly events       |
| `2019Events` | `long` (bitmask) | Bitmask of completed weekly events       |
| `2020Events` | `long` (bitmask) | Bitmask of completed weekly events       |
| `Events`     | `blob` (bitmask) | Bitmask of completed limited-time events |

## Playfab schema

Prefix: `Playfab`.

[Playfab](https://playfab.com) is a common third-party game-backend service; these keys are almost certainly related to
it. It's unlikely whether these fields can be edited as they will likely re-sync from PlayFab at next launch.

| Sub-key          | Shape            | Represents                                                                                         |
|------------------|------------------|----------------------------------------------------------------------------------------------------|
| `FlingPurchases` | `long` (bitmask) | Bitmask of purchased Core Girl flings, one bit per fling, filled low-to-high in fixed roster order |
| `Inventory`      | `int` (bitmask)  | Playfab-tracked inventory item bitmask                                                             |
| `Participation`  | `blob` (bitmask) | Bitmask tracking the parallel event(s) that have been participated in                              |

## Settings schema

Prefix: `Settings`.

| Sub-key        | Shape             | Represents                                                           |
|----------------|-------------------|----------------------------------------------------------------------|
| `Alphabetic`   | `flag`            | Whether girls are sorted alphabetically in lists                     |
| `DisableCloud` | `flag`            | Whether cloud backup is disabled for this save file. See note below. |
| `Effects`      | `float` (`0`-`1`) | Sound effects volume                                                 |
| `Music`        | `float` (`0`-`1`) | Music volume                                                         |
| `Voice`        | `float` (`0`-`1`) | Voice volume                                                         |

**Notes**:

- Even with cloud backups disabled, some data is still fetched from Playfab (or Blayfap which could be SPS' own
  implementation of a cloud service). Notably, some premium unlocks seem to be stored server side and the
  `BlayfapAwardedItems` array is fetched fresh each game launch.

## Skill schema

Prefix: `Skill`

Skill represents the level of a [Hobby](#hobby-schema); these map to the hobby's internal ID, **NOT** to its
alphabetical ordinal. It seems to relate to other data about the player/avatar as well since the customization options
are rolled in to this too.

| Sub-key pattern | Shape            | Represents                                                                                               |
|-----------------|------------------|----------------------------------------------------------------------------------------------------------|
| `Skill<N>`      | `int` (`0`-`75`) | Skill/stat level for the hobby represented by `N`                                                        |
| `Gender`        | `int`            | Player gender selection                                                                                  |
| `Hair`          | `int`            | Selected player hairstyle ID                                                                             |
| `Hat`           | `int`            | Selected hat ID                                                                                          |
| `Plushy`        | `int`            | Selected plushy/collectible ID (although I've not seen this in-game); this could also just be the hat ID |

## Task schema

Prefix: `Task`.

Tasks relate to the current Limited-time Event (see [EVENTS.md](EVENTS.md) for more information). Generally, there are
three tasks per day for each day the event is active, so the number of `Task` sub-keys may vary. If there is no active
LTE, there will likely be no Task entries (such as with a fresh save).

| Sub-key pattern    | Shape  | Represents                                                                                                                                                                                       |
|--------------------|--------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `Task.<N>Start`    | `long` | Timestamp of when the user commenced LTE task `N` (`0` = not yet started). Decodes as raw/`DateTimeKind.Unspecified` ticks (no Utc/Local tag bits set), unlike the tagged `GameState` timestamps |
| `Task.<N>Complete` | `flag` | Task `N`'s objective has been completed                                                                                                                                                          |
| `Task.<N>Claimed`  | `flag` | Task `N`'s reward has been claimed                                                                                                                                                               |

# Parallel Event Schemas

Parallel events have their own set of key/values that are seemingly prefixed with `pes` - likely standing for Parallel
Event State - and the event number. See [EVENTS.md](EVENTS.md) for the event table, schema, and individual event
schemas.
