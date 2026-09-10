## JSON schema (`tools/crushcrush_save.py` decode/encode, translated by `tools/save_schema.py`)

`decode` produces structured, human-editable JSON instead of the raw flat text above; `encode` consumes that JSON back
into either PC or Switch format via `--nintendo`, **regardless of which platform the JSON was originally decoded
from** - fields the target platform doesn't have are just never written, fields it does have but the JSON lacks are left
absent too (nothing is fabricated except `GameState.Created`, defaulted from `DateUTC` when missing, since a PC→Switch
conversion has no better source for it).

`crushed.schema.json` (project root) is a JSON Schema for this exact shape, kept in sync by hand with
`tools/save_schema.py`'s field tables - update it alongside any schema change. `decode` stamps a `"$schema"` key into
every file it writes (a relative path back to it, editor-IntelliSense-only, ignored on `encode` and not itself part of
the save data) so editors with JSON Schema support (VS Code out of the box; JetBrains IDEs via Preferences → Languages &
Frameworks → Schemas and DTDs → JSON Schema Mappings, if not auto-detected) get autocomplete/validation with no extra
config for the common case (`decoded/<name>.json`, one level under the project root).

General per-field transform, applied recursively:

- Timestamps → ISO-8601 strings, or the literal string `"N/A"` / `"never"` for the two sentinels. **Lossy below
  microsecond precision** - the raw format is 100ns ticks but Python's `datetime`/ISO-8601 only resolves to
  microseconds, so the last one or two digits of a tick value are truncated on decode. Round-trips are stable from that
  point on (decoding the same JSON twice gives identical results), it's only the *first* raw→JSON conversion that loses
  sub-microsecond precision - accepted as inherent to human-readable timestamps, not a bug.
- Bitmasks (int or blob) → object, bit index as a string key, `true` only for set bits (sparse - an absent key is an
  unset bit).
- Pipe-delimited text blobs (`AwardedItems`) → array of strings.
- Bare/flag keys → JSON boolean.

Top-level shape (grouped beyond the raw format's own prefixes - see `tools/save_schema.py`'s field tables for the
exhaustive per-key list, this is the shape of the grouping itself):

- `Girls`/`Jobs`/`Flings` (deliberately **plural**, unlike `Hobby`) each bundle their per-entity data (keyed by exact
  internal save name, e.g. `"Pamulzebub"`/`"Ayano"` - never translated to a display name) alongside the account-level
  bitmasks/pointers that conceptually belong with them (`Girls.Unlocked`/`PreviouslyUnlocked`/`Current`,
  `Jobs.Available`, `Flings.Unlocked`/`Purchased`).
- A girl's `LifeDates`/`LifeOutfits`/`LifeGifts` nest under `Life.{Dates,Outfits,Gifts}`, separate from her current
  `Dates`/`Clothing`. `Job`/`Hobby` entries are unified into one shape per name regardless of whether the raw save
  happened to group that entity's fields under a `::` section or leave them as bare individual lines (confirmed: this is
  a purely cosmetic choice the game's own serializer makes inconsistently, e.g. `JobMECH` has all six fields bare in one
  real save where every other job gets a proper block - the JSON never tries to preserve or infer which form the source
  used).
- `GameState.Counts`/`GameState.Multipliers` pull the raw format's `-Count`/`-Multiplier`-suffixed keys (`DateCount`/
  `GiftCount`/`HeartCount`/`PokeCount`, `PendingMultiplier`/`PurchasedMultiplier`) off `GameState` itself into two
  sub-objects, stripped of the redundant suffix (`GameState.Counts.Date`, `GameState.Multipliers.Pending`, etc). Root
  `TimeMultiplier` (and each PE's own `pes<N>TimeMultiplier`) is an exception folded in as
  `GameState.Multipliers.Time` despite not sharing that suffix convention.
- `Bonuses` replaces the raw format's `.speedboost.*`/`.timeblocks.*`/`.timeskip.*` dotted keys with
  `Bonuses["Time Blocks"|"Speed Boost"|"Time Skip"]["Small"|"Medium"|"Large"]["Quantity"|"Price"]` - pure structural
  regrouping, values passed through unchanged.
- `Albums` replaces root `album0`-`album5` with an object keyed by album index, each value a sparse two-level object
  (byte index → bit index → `true`) rather than a flat bitmask, since these are wider than the other bitmask fields.
- `Player` holds the avatar-identity fields (`Gender`, `Hair`, `Hat`, `Plushy`) split out of the raw format's `Skill`
  block, since they represent the player's own identity rather than a skill level.
- `Achievement` is keyed by achievement ID; each value is still a bitmask (bit = tier), per `docs/ACHIEVEMENTS.md`'s
  bitmask-per-tier mechanism.
- `Flings.<id>.Progress` (raw `C<N>P`) is fully decoded via `tools/phone_fling.py` into `{message_counter, unknown_1,
  next_message_countdown, trailing: "<hex>"}`, or `null` when the blob is empty (`Flings.<id>.Date`, raw `C<N>D`, ==
  `"never"`).
- `Playfab.AwardedItems` is the normalized name for PC's `BlayfapAwardedItems` / Switch's `PlayfabAwardedItems` - encode
  picks the right key per `--nintendo` target.
- `Events` holds everything event-related: `Events.Completed.{2018,2019,2020,LTE}` (the last renamed from the raw
  format's own `Completed.Events` to avoid an `Events.Completed.Events` repeat), `Events.PE.<id>` (a parallel event's
  mirrored state - see below), `Events.LTE.<id>` (`Tokens` always, `Tasks` only for whichever id matches
  `Events.Current`), and `Events.Current` (was root `EventID` - moved here as a judgment call for consistency, not
  something the raw format itself groups).

`Events.PE.<id>` is produced by recursively feeding that PE's own `pes<N>`-stripped keys back through the *same*
per-entry dispatcher root uses (`tools/save_schema.py`'s `dispatch_entry`), not a separate hand-maintained copy - so
anything with a coherent per-PE reading (`GameState`, `Skill`, `Girls` including its
`Unlocked`/`PreviouslyUnlocked`/`Current`, `Jobs` including `Available`, `Hobby`, `Bonuses`) is handled identically
inside a PE, confirmed real for `Bonuses`/`GirlsUnlocked`/`GirlsPreviouslyUnlocked`/`CurrentGirl`/`AvailableJobs`
inside the Time Warp PE (id 55). `Skill` mirrors per-PE too, paired with that PE's own `Hobby` name vocabulary. Several
checks are root-only by design:

- `Achievement`, `Events.Completed`, LTE `Task`/`Event<N>Tokens` accumulation, `EventID`, `LastPesId<N>` - save-wide
  singleton concepts ("which LTE is active" has no coherent "one per PE" reading, and LTEs/PEs are mutually exclusive
  event systems per `docs/EVENTS.md`).
- `Settings`, `Player`, `Playfab`, `Flings`, `Albums`, `events.popupinfo` - account-wide state (a player preference,
  avatar identity, IAP entitlement tracking, its own separate mini-game, the global Memory Album) that never occurs
  inside a Parallel Event at all, unlike `Skill` above.

If one of these ever *does* turn up `pes<N>`-prefixed in a real save, it safely and losslessly falls into that PE's own
`Unknown` bucket rather than corrupting `Events.PE.<id>` or crashing - it just isn't structurally elevated the way
root's copy is.

Forward/backward compatibility: a key matching a known object prefix but an unregistered suffix round-trips losslessly
as `{"value": ..., "raw_suffix": "i"|"f"|""}` rather than being dropped (e.g. the undocumented Switch-only
`SettingsMusicMute`/`SettingsSoundMute` - not yet understood, so left as-is rather than guessed at). A field the docs
describe as bitmask/blob-shaped but that doesn't actually decode as one in a given save (observed: `GirlsUnlocked:19i`
as a plain int in one PC save, `PlayfabAwardedItems:135516928i` in another) falls back to the same raw-preserving
wrapper under a `_raw_fallback` key instead of crashing.