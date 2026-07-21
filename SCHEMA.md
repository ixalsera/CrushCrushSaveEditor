# Save Data Schema

This documents the schema of the plaintext produced by decoding a save file
(see [AGENTS.md](AGENTS.md) for the decode format itself). It's derived from a 
`decoded/crushcrush.txt`. Cells are left **blank** where the key's purpose
isn't immediately identifiable from the data alone — fill those in manually
once confirmed against the game.

## How to read these tables

- **Key** is the *logical* key name. In the raw decoded text, a `::Name`
  line starts a section, and every following bare line (until the next
  `::`) is really `Name` + that line's own key concatenated together (see
  AGENTS.md). The tables below already show the reconstructed logical key.
- **Shape** uses these type labels, inferred from the value-suffix
  convention observed in the file:

| Suffix                           | Type            | Notes                                                                                                                                                                                                                                                                       |
|----------------------------------|-----------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `i`                              | `int` (32-bit)  |                                                                                                                                                                                                                                                                             |
| `f`                              | `float`         |                                                                                                                                                                                                                                                                             |
| *(none)*                         | `long` (64-bit) | Every unsuffixed numeric value observed fits comfortably in an `int64` and several equal or approach `int64.MaxValue` exactly, but not `int32.MaxValue` — consistent with the underlying field being declared as a 64-bit integer type regardless of its current magnitude. |
| *(bare key, no `:value` at all)* | `flag`          | Presence-only. Appears to mean either "this boolean is `true`" or "this field is at its type's default/zero value and was written without a value" — the file doesn't disambiguate; treat as unconfirmed until verified in-game.                                            |
| base64-looking string            | `blob`          | An embedded base64 chunk, usually a packed bitmask or small binary struct. Some are just base64 of ASCII text (noted where found).                                                                                                                                          |

- Several long, unsuffixed timestamp-looking fields (very large or negative
  numbers, e.g. `LoginDate`, `DateUTC`, `Pes27Start`, `Task*Start`, `C*D`)
  are consistent with .NET's `DateTime.ToBinary()` encoding (a `long` ticks
  value with the top bits used to tag UTC/Local `DateTimeKind`, which is why
  some are negative and others exceed the normal max-ticks range). This is
  a strong structural inference, not a confirmed fact — noted per-row below.
- Where a key has its own set of sub-keys (e.g. `Girl<Name>`), the **Shape**
  column says `object` and points at that key's own schema table further
  down, instead of repeating its fields inline.
- Numbered/repeating keys (achievements, challenges, tasks, skills) are
  shown once as a pattern row (e.g. `ACH.<id>`) rather than one row per
  instance.

## Top-level keys

| Key                                                  | Shape                         | Represents                                                                                                                                                   |
|------------------------------------------------------|-------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `.speedboost.<size>.pri` (`large`/`medium`/`small`)  | `int` (negative)              | Shop price for a speed-boost purchase, per size tier; unconfirmed                                                                                            |
| `.speedboost.<size>.qty`                             | `int` (negative)              | Quantity/count associated with a speed-boost purchase, per size tier; unconfirmed                                                                            |
| `.timeblocks.<size>.pri`                             | `int` (negative)              | Shop price for a time-block purchase, per size tier; unconfirmed                                                                                             |
| `.timeblocks.<size>.qty`                             | `int` (negative)              | Quantity/count for a time-block purchase, per size tier; unconfirmed                                                                                         |
| `.timeskip.<size>.pri`                               | `int` (negative)              | Shop price for a time-skip purchase, per size tier; unconfirmed                                                                                              |
| `.timeskip.<size>.qty`                               | `int` (negative)              | Quantity/count for a time-skip purchase, per size tier; unconfirmed                                                                                          |
| `ACH`                                                | `object`                      | See [Achievement schema](#achievement-ach-schema)                                                                                                            |
| `AchievementCount`                                   | `int`                         | Total number of achievements unlocked                                                                                                                        |
| `ana.ev`                                             | `long`                        |                                                                                                                                                              |
| `ana.vid`                                            | `long`                        |                                                                                                                                                              |
| `AvailableJobs`                                      | `int`                         | Bitmask; bit count (~19 set bits) is close to the number of distinct `Job<Name>` types seen in this file (20), suggesting one bit per job type — unconfirmed |
| `BlayfapAwardedItems`                                | `blob` (base64 of plain text) | Decodes to a literal pipe-delimited list, likely of DLC girls as it seems to contain the Kaiju girls and, most recently, Lumi.                               |
| `C<N>D` (e.g. `C1D`..`C46D`)                         | `long`                        | Confirmed: Phone Fling feature. See [Phone Fling schema](#phone-fling-schema)                                                                                |
| `C<N>P` (e.g. `C1P`..`C46P`)                         | `blob`                        | Confirmed: Phone Fling feature. See [Phone Fling schema](#phone-fling-schema)                                                                                |
| `Completed`                                          | `object`                      | See [Completed schema](#completed-schema)                                                                                                                    |
| `CurrentGirl`                                        | `int`                         | Index of the currently selected/active girl; likely only used to restore game state back to this specific girl on launch (instead of jumping to Cassie).     |
| `dchk`                                               | `int`                         |                                                                                                                                                              |
| `Event<ID>Tokens` (e.g. `Event307Tokens`)            | `int`                         | Token/currency count for the numbered limited-time event; unconfirmed                                                                                        |
| `EventID`                                            | `int`                         | ID of the currently active/most recent limited-time event; unconfirmed                                                                                       |
| `events.popupinfo`                                   | JSON object                   | Per-event popup display tracking: `{"<event-key>": {"shownCount": int, "shownAt": ISO-8601 timestamp}}`                                                      |
| `GameState`                                          | `object`                      | See [GameState schema](#gamestate-schema)                                                                                                                    |
| `Girl<Name>`                                         | `object`                      | See [Girl schema](#girl-schema). One instance per girl in the roster (~80+ seen)                                                                             |
| `GirlsPreviouslyUnlocked`                            | `blob` (17-byte bitmask)      | Bitmask, likely 1 bit per girl in the roster, tracking girls unlocked at some earlier point (vs. currently, see next)                                        |
| `GirlsUnlocked`                                      | `blob` (17-byte bitmask)      | Bitmask, likely 1 bit per girl in the roster, tracking currently-unlocked girls                                                                              |
| `HasSeenFuzzyExternalPurchaseConfirmation`           | `flag`                        | Whether a specific purchase-confirmation dialog has been shown; no idea what this is for                                                                     |
| `Hobby<Name>`                                        | `object`                      | See [Hobby schema](#hobby-schema). 12 instances seen                                                                                                         |
| `Job<Name>`                                          | `object`                      | See [Job schema](#job-schema). ~20 instances seen                                                                                                            |
| `LastPesId<N>` (`0`-`9`)                             | `string`                      | A recently-seen limited-time event (LTE) ID (see `pes27`/`pes53`/`pes54` below); slot `N` is a recency-ordered list, not a stat index                        |
| `Playfab`                                            | `object`                      | See [Playfab schema](#playfab-schema)                                                                                                                        |
| `Prereg`                                             | `flag`                        | Likely whether pre-registration content is unlocked; unconfirmed                                                                                             |
| `SaveFileVersion`                                    | `flag`                        | Bare in this sample — expected a version number here; treat as unconfirmed                                                                                   |
| `Settings`                                           | `object`                      | See [Settings schema](#settings-schema)                                                                                                                      |
| `Skill<N>` (`0`-`11`)                                | `object`                      | See [Skill schema](#skill-schema)                                                                                                                            |
| `Task`                                               | `object`                      | See [Task schema](#task-schema)                                                                                                                              |
| `TermsVersionAccepted`                               | `flag`                        | Whether the current Terms of Service version has been accepted                                                                                               |
| `ticketboothSeen`                                    | `flag`                        | Whether the "ticket booth" UI element/prompt has been seen                                                                                                   |
| `TimeMultiplier`                                     | `float`                       | Current overall time-speed multiplier                                                                                                                        |
| `Tutorial`                                           | `int`                         | Tutorial progress step/stage reached                                                                                                                         |
| `UnlockedPFS`                                        | `blob` (3-byte bitmask)       | Unknown. If unset, it seems to read `/n+a` (i.e. not applicable). Possibly Peanut Fling?                                                                     |

## GameState schema

Prefix: `GameState`. Root-level player state.

| Sub-key               | Shape          | Represents                                                                                                                                                                                                                                                                                    |
|-----------------------|----------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `Build`               | `string`       | Game build identifier the save was written by (e.g. `447_d0d00b4`)                                                                                                                                                                                                                            |
| `Date`                | `long`         | Confirmed: timestamp (local time) of when this game state/save file was created, `DateTime.ToBinary()` with `DateTimeKind.Local`. Decodes to the same instant as `DateUTC` (to the millisecond)                                                                                               |
| `DateCount`           | `int`          | Number of dates the user has gone on, in total; unconfirmed                                                                                                                                                                                                                                   |
| `DateUTC`             | `long`         | Confirmed: timestamp (UTC) of when this game state/save file was created, `DateTime.ToBinary()` with `DateTimeKind.Utc`. Agrees with `Date` to the millisecond                                                                                                                                |
| `Diamonds`            | `long`         | Premium currency balance                                                                                                                                                                                                                                                                      |
| `GiftCount`           | `int`          | Total gifts given, across all girls                                                                                                                                                                                                                                                           |
| `HeartCount`          | `long`         | Total affection/heart points accumulated, across all girls                                                                                                                                                                                                                                    |
| `Hobbies`             | `int`          | Count or bitmask of unlocked hobbies                                                                                                                                                                                                                                                          |
| `Ids`                 | `string` (hex) | Device/install identifier; unconfirmed                                                                                                                                                                                                                                                        |
| `LoginDate`           | `long`         | Confirmed: timestamp (UTC) of the last time the game was launched, `DateTime.ToBinary()` with `DateTimeKind.Utc`. Observed identical to `pes27GameStateLoginDate` in the same save — login time appears to be shared across the root profile and LTE profiles rather than tracked per-profile |
| `Money`               | `long`         | Soft/spendable currency balance                                                                                                                                                                                                                                                               |
| `NSFW`                | `flag`         | Whether NSFW content mode is enabled                                                                                                                                                                                                                                                          |
| `PendingMultiplier`   | `float`        | Current pending Reset Boost multiplier                                                                                                                                                                                                                                                        |
| `PokeCount`           | `int`          | Number of times a girl has been "poked"/clicked                                                                                                                                                                                                                                               |
| `PurchasedMultiplier` | `float`        | Multiplier obtained via a purchase                                                                                                                                                                                                                                                            |
| `Seconds`             | `float`        | Elapsed seconds counter (exact reference point unconfirmed)                                                                                                                                                                                                                                   |
| `TotalIncome`         | `long`         | Lifetime total money earned                                                                                                                                                                                                                                                                   |
| `TotalTime`           | `int`          | Lifetime total play time (unit unconfirmed — likely seconds or minutes)                                                                                                                                                                                                                       |

## Girl schema

Prefix: `Girl<Name>` (e.g. `GirlCassie`, `GirlMio`). One block per girl. This represents their current level's state as well as some lifetime trackers.

Both `DateCount` and `GiftCount` are suffixed with a number from `1` to `3`, where present. It seems that this represents in which slot that Gift or Date tracker sits (`Hearts` is always slot 0 of 4). If no progress has been made towards the Gift/Date, this value is likely to not be present rather than set to 0.

| Sub-key                       | Shape                    | Represents                                                                                                      |
|-------------------------------|--------------------------|-----------------------------------------------------------------------------------------------------------------|
| `Clothing`                    | `int` (bitmask)          | Currently equipped clothing/outfit, likely a bitmask/flag value; exact options and mappings yet to be confirmed |
| `DateCount<N>` (`1`-`3` seen) | `int`                    | Count of dates required to progress (see above regarding the relevance of `N`)                                  |
| `Dates`                       | `int`                    | Bare/zero in samples seen — current date count (relationship to `DateCount<N>` unconfirmed)                     |
| `GiftCount<N>` (`1`-`3` seen) | `int`                    | Count of gifts required to progress (see above regarding the relevance of `N`)                                  |
| `Hearts`                      | `long`                   | Accumulated Hearts *for this level*                                                                             |
| `LifeDates`                   | `int`                    | Lifetime total dates been on with this girl                                                                     |
| `LifeOutfits`                 | `int` (bitmask)          | Lifetime unlocked outfits/costumes for this girl                                                                |
| `Love`                        | `int` (`0`-`9` observed) | Relationship tier; 9 represents "Lover" level                                                                   |

**Notes and Cautions**:
- `GirlPamulzebub` and `GirlQuillzone` are distinct objects for the respective "demon" or "kaiju" versions of Pamu and Quill. Don't mix them up (or get confused!)!
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
- It's not known whether simply setting a `Girl` object to non-zero will unlock her, although it's unlikely.

## Hobby schema

Prefix: `Hobby<Name>` (e.g. `HobbyAngst`, `HobbySmart`). One block per each of the 12 core game hobbies (`Angst`, `Badass`, `Buff`, `Funny`, `Lucky`,
`Motivation`, `Mysterious`, `Smart`, `Suave`, `TechSavvy`, `Tenderness`,
`Wisdom`)

**Notes** — Limited-time events (LTEs; `pes27` etc) that incorporate hobbies use a **different** set of 12 hobby names (see below).

| Sub-key           | Shape   | Represents                                                |
|-------------------|---------|-----------------------------------------------------------|
| `Active`          | `flag`  | This hobby is currently enabled                           |
| `MultiplierCount` | `flag`  | Whether this hobby is "Gilded"                            |
| `Time`            | `float` | Current progress timer (toward next level-up, presumably) |
| `TimeL`           | `long`  | Lifetime total time invested in this hobby                |

## Job schema

Prefix: `Job<Name>` (e.g. `JobART`, `JobZOO`). One block for each of the core jobs (`ART`,
`CASINO`, `CLEANING`, `COMPUTERS`, `DIGGER`, `FAST FOOD`, `HUNTING`,
`LEGAL`, `LIFEGUARD`, `LOVE`, `MECH`, `MOVIES`, `PLANTER`, `RESTAURANT`,
`SLAYING`, `SPACE`, `SPORTS`, `UNKNOWN`, `WIZARD`, `ZOO`).

| Sub-key      | Shape   | Represents                                                                                                                                                             |
|--------------|---------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `Active`     | `flag`  | Currently working this job                                                                                                                                             |
| `Experience` | `long`  | Total XP earned in this job                                                                                                                                            |
| `Gilded`     | `flag`  | Whether the job is "Gilded", i.e. has the bonus earnings modifier applied (costing 10 diamonds)                                                                        |
| `Level`      | `int`   | Current job level                                                                                                                                                      |
| `Locked`     | `flag`  | Present on most jobs that also have `Experience > 0`, and absent on untouched jobs — the opposite of what the name suggests at first glance; exact meaning unconfirmed |
| `Time`       | `float` | Current work timer/progress                                                                                                                                            |

## Achievement (`ACH`) schema

Prefix: `ACH`. Sub-keys are numeric achievement IDs (internal to the game;
no name mapping available from the save alone).

| Sub-key pattern                     | Shape                              | Represents                                                                                                                    |
|-------------------------------------|------------------------------------|-------------------------------------------------------------------------------------------------------------------------------|
| `ACH.<id>` (e.g. `ACH.0`, `ACH.42`) | `int`, or `flag` if at its default | Progress/tier value for achievement `<id>`. Which ID corresponds to which in-game achievement is unknown from this file alone |

Root-level `AchievementCount` (see top-level table) is the total count these
sum/unlock to.

## Phone Fling schema

See [FLINGS.md](FLINGS.md) for the mapping between fling ID and the actual Girl it represents.

| Sub-key pattern   | Shape   | Represents                                                                                                                                                              |
|-------------------|---------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `C<N>D`           | `long`  | DateTime of message last received or, if additional requirements are needed to unlock the next message, `int64.MaxValue`. `0` if the fling has not yet started/unlocked |
| `C<N>P`           | `blob`  | Packed binary data, structure not decoded; potentially the state of the message (i.e. at which point in the conversation you are at)                                    |

## Completed schema

Prefix: `Completed`.

| Sub-key      | Shape                    | Represents                                                                |
|--------------|--------------------------|---------------------------------------------------------------------------|
| `2018Events` | `long`                   | `0` in sample — likely a bitmask of 2018 limited-time events completed    |
| `2019Events` | `long`                   | `0` in sample — likely a bitmask of 2019 limited-time events completed    |
| `2020Events` | `long`                   | `0` in sample — likely a bitmask of 2020 limited-time events completed    |
| `Events`     | `blob` (15-byte bitmask) | Bitmask of completed limited-time events (only one bit set in the sample) |

## Playfab schema

Prefix: `Playfab`. [Playfab](https://playfab.com) is a common third-party
game-backend service; these keys are almost certainly related to it.

| Sub-key          | Shape                   | Represents                                                                |
|------------------|-------------------------|---------------------------------------------------------------------------|
| `FlingPurchases` | `long`                  | A purchase counter                                                        |
| `Inventory`      | `int` (bitmask)         | Playfab-tracked inventory item bitmask                                    |
| `Participation`  | `blob` (7-byte bitmask) | Likely which Playfab experiment/segment groups this player is enrolled in |

## Settings schema

Prefix: `Settings`.

| Sub-key      | Shape             | Represents                                       |
|--------------|-------------------|--------------------------------------------------|
| `Alphabetic` | `flag`            | Whether girls are sorted alphabetically in lists |
| `Effects`    | `float` (`0`-`1`) | Sound effects volume                             |
| `Music`      | `float` (`0`-`1`) | Music volume                                     |
| `Voice`      | `float` (`0`-`1`) | Voice volume                                     |

## Skill schema

Prefix: `Skill<N>` (`0`-`11`, 12 total — matching the count of `Hobby<Name>`
entries, which may or may not mean each index maps 1:1 to a specific
hobby's stat; unconfirmed but likely).

| Sub-key pattern   | Shape   | Represents           |
|-------------------|---------|----------------------|
| `Skill<N>`        | `int`   | Skill/stat level `N` |

Also appears under `Settings` as `Skill.Gender`, `Skill.Hair`, `Skill.Hat`,
`Skill.Plushy` in this file — likely player-avatar customization fields
rather than "skill" stats:

| Sub-key   | Shape   | Represents                                                           |
|-----------|---------|----------------------------------------------------------------------|
| `Gender`  | `flag`  |                                                                      |
| `Hair`    | `int`   | Selected hairstyle ID                                                |
| `Hat`     | `flag`  |                                                                      |
| `Plushy`  | `int`   | Selected plushy/collectible ID (although I've not seen this in-game) |

## Task schema

Prefix: `Task`. Sub-keys are numbered `0`-`41` (in this sample) with three
possible suffixes each. These map to the three daily tasks during LTEs (Roxxy, Roxxy (Outfits) etc.)

| Sub-key pattern    | Shape   | Represents                                                                                                                                                                                                  |
|--------------------|---------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `Task.<N>Start`    | `long`  | Confirmed: timestamp of when the user commenced LTE task `N` (`0` = not yet started). Decodes as raw/`DateTimeKind.Unspecified` ticks (no Utc/Local tag bits set), unlike the tagged `GameState` timestamps |
| `Task.<N>Complete` | `flag`  | Task `N`'s objective has been completed                                                                                                                                                                     |
| `Task.<N>Claimed`  | `flag`  | Task `N`'s reward has been claimed                                                                                                                                                                          |

# Event Schemas

Limited-time events (LTEs) have their own set of key/values that are seemingly prefixed with `pes` and the event number. Currently, the suspected event mapping is:

| Event                    | Prefix  |
|--------------------------|---------|
| Furry Friends (Paid DLC) | `pes27` |
| Roxxy                    | `pes53` |
| Roxxy (Outfits)          | `pes54` |

## Furry Friends LTE

| Sub-key                                                          | Shape   | Represents                                                                                                            |
|------------------------------------------------------------------|---------|-----------------------------------------------------------------------------------------------------------------------|
| `pes27Goals` (also `pes53Goals`)                                 | `int`   | Bitmask, purpose unconfirmed; likely a bitmask of the goals culminating in unlocking Ginger & Wasabi in the core game |
| `pes27PurchasedTime`                                             | `int`   |                                                                                                                       |
| `Pes27Start` (note capital `P`, unlike every other `pes27*` key) | `long`  | Timestamp, shape consistent with `DateTime.ToBinary()` — likely when this profile was created                         |
| `pes27TimeMultiplier`                                            | `float` | Same meaning as root `TimeMultiplier`, scoped to this profile                                                         |

Its `Hobby<Name>` instances use a **different 12 names** than the root
profile: `Bravery`, `Caring`, `Charisma`, `Creative`, `Focus`,
`Innovation`, `Luck`, `Optimism`, `Peaceful`, `Responsible`,
`Tenderness`, `Trustworthy`.

## Open questions

These need to be confirmed against the game itself (or an authoritative
source) rather than assumed — see AGENTS.md's note on not guessing at
strings:

- Whether `C<N>D` timestamps really do represent "last message received"
  from a Phone Fling (needs a follow-up save to check if they advance),
  and the exact structure of the `C<N>P` blob.
- Which achievement ID (`ACH.<id>`) corresponds to which in-game
  achievement.
- The exact meaning of `dchk`, `ana.ev`, `ana.vid`, `UnlockedPFS`.
- Why `Job.Locked` appears on already-leveled jobs rather than untouched
  ones.
