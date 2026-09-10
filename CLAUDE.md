# CrushCrushSaveEdit

Decode/edit/re-encode save files for **Crush Crush** (Sad Panda Studios). Reverse-engineered format + tools below, so
format discovery isn't repeated.

Per-key docs - check before re-deriving what a field means:

| File                   | Covers                                                                                                                                                                                                        |
|------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `docs/SCHEMA.md`       | Every top-level key + nested object schemas (`Girl`, `Job`, `Hobby`, `Task`, `ACH`, Phone Fling, etc).                                                                                                        |
| `docs/EVENTS.md`       | `pes<N>` parallel-event prefix→event mapping + event-scoped schemas, plus LTE IDs.                                                                                                                            |
| `docs/FLINGS.md`       | Phone Fling (`C<N>D`/`C<N>P`): fling-ID→girl mapping + `C<N>P` blob decoding. The save stores only the numeric fling index - never a girl's name - and a fling need not correspond to any `Girl<Name>` block. |
| `docs/GIRLS.md`        | `GirlsUnlocked`/`GirlsPreviouslyUnlocked` bit-index→girl mapping, plus per-girl `Clothing`/`LifeOutfits` outfit-bit findings.                                                                                 |
| `docs/UNLOCKS.md`      | Same bitmask/list analysis as `docs/GIRLS.md`, but for account-level `Playfab`/`BlayfapAwardedItems` - both are server-synced on launch, not derived from the local save.                                     |
| `docs/ACHIEVEMENTS.md` | `ACH.<id>` bitmask-per-tier mechanism + achievement ID→name mapping.                                                                                                                                          |

## Directory layout

```
saves/     Real save files, exactly as copied from the game. Never hand-edit
           these directly - decode, edit the plaintext, re-encode.
decoded/   Human-readable JSON dumps produced by tools/crushcrush_save.py.
           Regenerate freely; not authoritative once saves/ changes.
tools/     The decode/encode implementation (Python 3, stdlib only).
utils/     Generic, Crush-Crush-agnostic codecs that tools/ depends on (LZF
           compression, .NET DateTime.ToBinary() timestamps) - reusable on
           any project that happens to hit the same generic formats.
scripts/   Investigation/analysis helpers used while reverse-engineering the
           format (not needed to just edit a save - see `tools/` for that).
```

Save files may have any name; the game's own default is `crushcrush.sav`.

## File format (reverse-engineered, confirmed by full round-trip)

A `.sav` file is ASCII text, single line, **no trailing newline**:

```
base64( MAGIC + lzf_compress(plaintext_save_data) )
```

- `MAGIC` = fixed 3 bytes `97 37 dc`, identical across every save observed regardless of content/length - a
  format/version marker, **not** a length field or checksum. Don't parse it as one.
- Base64 alphabet is standard (`+`, `/`, `=` padding) - nothing custom.

### Nintendo Switch container variant

The Switch build stores the same plaintext/LZF payload in a different container - confirmed by full round-trip
against a real Switch save (`saves/CrushSaveData1.sav`):

```
<4-byte little-endian uint32, only value observed: 1><base64(MAGIC)><base64(lzf_compress(plaintext_save_data))>
```

- The leading 4 bytes are raw binary, not base64 - meaning unconfirmed (only one save sampled).
- Unlike PC, `MAGIC` and the compressed body are base64-encoded **separately** and concatenated as text, not combined
  into one base64 blob. `base64(MAGIC)` happens to render as the ASCII text `lzfc` (3 bytes divides evenly into
  base64's 4-char groups, so no padding) - which is why this looks like a distinct "lzfc" marker rather than the same
  MAGIC bytes.
- `decode_bytes`/`decode_file` in `tools/crushcrush_save.py` already handle Switch saves with no changes needed:
  `base64.b64decode()` silently drops the leading non-base64 header bytes, and decoding "lzfc" alone reproduces
  `MAGIC` exactly. Only `encode` needed a separate path, since PC's encode wraps everything in one base64 call and
  has no room for the leading header (`tools/crushcrush_save.py encode --nintendo`).

### LZF stream format (classic liblzf-compatible)

Control-byte encoding (literal run vs. back-reference) is documented in `utils/lzf.py`'s module docstring - read that
instead of re-deriving it here.

`utils/lzf.py`:

- `decompress(buf) -> bytes` - validated against actual game output, not just our own encoder's round-trip.
- `compress(data) -> bytes` - simple greedy LZ77 encoder; **not** byte-identical to the game's own encoder, but valid
  since `decompress(compress(x)) == x` (LZF decompression doesn't care how the compressor chose to encode things).

## Plaintext save structure

This is the save's own internal representation, decompressed - `tools/save_schema.py` translates it to/from the
structured JSON described below, and the CLI never exposes it directly, but it's still the ground truth `save_schema.py`
works against. Decompressed, the save is a flat, newline-delimited key-value dump (no JSON/XML) with prefix compression
at the *application* layer (independent of LZF):

- Bare line `::` resets to "no active prefix"; next line is a self-contained `key:value` entry.
- `::SomeName` starts a section; subsequent lines until the next `::` are **suffixes** concatenated onto that prefix,
  e.g.:
  ```
  ::GirlCassie
  Clothing:1073741824i
  Hearts:204188
  LifeDates:17i
  LifeOutfits:1610612736i
  Love:9i
  ```
  means `GirlCassieClothing:1073741824i`, `GirlCassieHearts:204188`, ..., `GirlCassieLove:9i`.
- Value suffixes: `i` = int, `f` = float, no suffix = plain int/long or empty/flag value (bare key with no `:value` at
  all = boolean-ish flag, e.g. `Locked`, `Active`, `Gilded`).
- `pes<N>` keys (e.g. `pes27GameStateDate`, `pes27GirlQuillHearts`) are **not** a second save slot - they're per-
  **parallel event** data, mirroring whatever part of the root schema that event needs (some near-complete: own
  `GameState`/`Job`/`Hobby`/`Girl` blocks with their own hobby names; others just a stray field). See `docs/EVENTS.md`
  for prefix→event mapping. Unprefixed keys remain "the" active save state.
- `C<N>D`/`C<N>P` numbered pairs are the **Phone Fling** feature (see `docs/SCHEMA.md`/`docs/FLINGS.md`). `C<N>D` =
  `DateTime` of last message received, or `int64.MaxValue` if the next message needs an extra unlock requirement. Flings
  are identified purely by `<N>` index - no girl-name-keyed variant exists, and the index isn't guaranteed to map to a
  girl present in this save's roster.

### Timestamp fields

`GameState.Date`, `DateUTC`, `LoginDate`, `Task<N>Start`, `C<N>D` (long, unsuffixed, timestamp-shaped) are .NET
`DateTime.ToBinary()` values - confirmed by decode + cross-check against known play dates:

```
unsigned = value & 0xFFFFFFFFFFFFFFFF
if unsigned & 0x8000000000000000:      # bit 63 set -> Local kind
    ticks = unsigned - 0x8000000000000000   # UTC-equivalent (offset unknown)
elif unsigned & 0x4000000000000000:    # bit 62 set -> Utc kind
    ticks = unsigned - 0x4000000000000000
else:                                   # Unspecified kind (e.g. Task*Start)
    ticks = unsigned                    # raw ticks, no tag bits
# ticks = 100ns units since 0001-01-01; sentinel int64.MaxValue = "N/A"; 0 = "never"
datetime(1,1,1) + timedelta(seconds=ticks//10_000_000, microseconds=(ticks%10_000_000)//10)
```

Use `utils/timestamp.py` instead of re-deriving this inline - `decode` takes raw values from a save/diff and prints
`DateTimeKind` + ISO datetime (sentinels print as `N/A`/`never`); `encode` reverses it. Uses exact integer tick
arithmetic, not `timedelta.total_seconds()` (loses sub-second precision here via float rounding).

Investigating an unconfirmed field (diffing saves before/after a play session, decoding blob bitmasks, diffing Phone
Fling state) is its own workflow - see the `investigate-save-field` skill instead of repeating it here.

## JSON schema (`tools/crushcrush_save.py` decode/encode, translated by `tools/save_schema.py`)

`decode` produces structured, human-editable JSON instead of the raw flat text above; `encode` consumes that JSON back
into either PC or Switch format via `--nintendo`, **regardless of which platform the JSON was originally decoded
from** - fields the target platform doesn't have are just never written, fields it does have but the JSON lacks are
left absent too (nothing is fabricated except `GameState.Created`, defaulted from `DateUTC` when missing, since a
PC→Switch conversion has no better source for it).

`crushed.schema.json` (project root) is a JSON Schema for this exact shape, kept in sync by hand with
`tools/save_schema.py`'s field tables - update it alongside any schema change. `decode` stamps a `"$schema"` key into
every file it writes (a relative path back to it, editor-IntelliSense-only, ignored on `encode` and not itself part
of the save data) so editors with JSON Schema support (VS Code out of the box; JetBrains IDEs via Preferences →
Languages & Frameworks → Schemas and DTDs → JSON Schema Mappings, if not auto-detected) get autocomplete/validation
with no extra config for the common case (`decoded/<name>.json`, one level under the project root).

General per-field transform, applied recursively:

- Timestamps → ISO-8601 strings, or the literal string `"N/A"` / `"never"` for the two sentinels. **Lossy below
  microsecond precision** - the raw format is 100ns ticks but Python's `datetime`/ISO-8601 only resolves to
  microseconds, so the last one or two digits of a tick value are truncated on decode. Round-trips are stable from
  that point on (decoding the same JSON twice gives identical results), it's only the *first* raw→JSON conversion
  that loses sub-microsecond precision - accepted as inherent to human-readable timestamps, not a bug.
- Bitmasks (int or blob) → object, bit index as a string key, `true` only for set bits (sparse - an absent key is an
  unset bit).
- Pipe-delimited text blobs (`AwardedItems`) → array of strings.
- Bare/flag keys → JSON boolean.

Top-level shape (grouped beyond the raw format's own prefixes - see `tools/save_schema.py`'s field tables for the
exhaustive per-key list, this is the shape of the grouping itself):

- `Girls`/`Jobs`/`Flings` (deliberately **plural**, unlike `Hobby`) each bundle their per-entity data (keyed by exact
  internal save name, e.g. `"Pamulzebub"`/`"Ayano"` - never translated to a display name) alongside the
  account-level bitmasks/pointers that conceptually belong with them (`Girls.Unlocked`/`PreviouslyUnlocked`/`Current`,
  `Jobs.Available`, `Flings.Unlocked`/`Purchased`).
- A girl's `LifeDates`/`LifeOutfits` nest under `Life.{Dates,Outfits}`, separate from her current `Dates`/`Clothing`.
  `Job`/`Hobby` entries are unified into one shape per name regardless of whether the raw save happened to group that
  entity's fields under a `::` section or leave them as bare individual lines (confirmed: this is a purely cosmetic
  choice the game's own serializer makes inconsistently, e.g. `JobMECH` has all six fields bare in one real save where
  every other job gets a proper block - the JSON never tries to preserve or infer which form the source used).
- `Achievement` is keyed by achievement ID; each value is still a bitmask (bit = tier), per `docs/ACHIEVEMENTS.md`'s
  bitmask-per-tier mechanism.
- `Flings.<id>.P` is fully decoded via `tools/phone_fling.py` into `{message_counter, unknown_1,
  next_message_countdown, trailing: "<hex>"}`, or `null` when the blob is empty (`D` == `"never"`).
- `Playfab.AwardedItems` is the normalized name for PC's `BlayfapAwardedItems` / Switch's `PlayfabAwardedItems` -
  encode picks the right key per `--nintendo` target.
- `Events` holds everything event-related: `Events.Completed.{2018,2019,2020,LTE}` (the last renamed from the raw
  format's own `Completed.Events` to avoid an `Events.Completed.Events` repeat), `Events.PE.<id>` (a parallel event's
  mirrored `GameState`/`Jobs`/`Hobby`/`Girls` blocks, keyed the same way as root), `Events.LTE.<id>` (`Tokens` always,
  `Tasks` only for whichever id matches `Events.Current`), and `Events.Current` (was root `EventID` - moved here as a
  judgment call for consistency, not something the raw format itself groups).

Forward/backward compatibility: a key matching a known object prefix but an unregistered suffix round-trips losslessly
as `{"value": ..., "raw_suffix": "i"|"f"|""}` rather than being dropped (e.g. `Girl<Name>LifeGifts`, seen in real
saves but not in any doc above - not yet understood, so left as-is rather than guessed at). A field the docs describe
as bitmask/blob-shaped but that doesn't actually decode as one in a given save (observed: `GirlsUnlocked:19i` as a
plain int in one PC save, `PlayfabAwardedItems:135516928i` in another) falls back to the same raw-preserving wrapper
under a `_raw_fallback` key instead of crashing.

## Standard edit workflow

1. Decode: `uv run tools/crushcrush_save.py decode "saves/<save_game_filename>.sav" "decoded/<save_game_filename>.json"`
2. Edit `decoded/<save_game_filename>.json` per the JSON schema above.
3. Encode back (add `--nintendo` to target a Switch save regardless of where the JSON came from):
   `uv run tools/crushcrush_save.py encode "decoded/<save_game_filename>.json" "saves/<save_game_filename>.edited.sav"`
4. **Always verify before overwriting a real save**: decode the newly encoded file again and diff it against the
   edited JSON (`python3 -c "import json,sys; a=json.load(open(sys.argv[1])); b=json.load(open(sys.argv[2])); print(a==b)"`
   or just `diff`, since both are `json.dumps(..., indent=2, sort_keys=True)`). Validated to round-trip identically
   (at the JSON level - see the timestamp precision note above for the one expected exception) for every sample file
   in `saves/`, PC and Switch alike - if it doesn't match, the edit broke something, not the tooling.
5. Only after the diff is clean, replace `saves/<save_game_filename>.sav` (back it up first as
   `<save_game_filename>.backup.sav`).

`decode_bytes`/`encode_bytes`/`decode_file`/`encode_file` in `tools/crushcrush_save.py` remain a lower-level flat-text
API (unchanged, still what `tools/blank_save.py` and `scripts/diff_saves.py` operate on) - only the CLI's `decode`/
`encode` modes route through the JSON layer.

## Open items / not yet done

- No value-specific validation (e.g. `Love` 0-9, `Diamonds` non-negative) is enforced - edits are freeform JSON.
  Building an actual editor UI/CLI for specific fields is new work, not started.
- `pes<N>` → event name mapping (`docs/EVENTS.md`) confirmed for 2 prefixes only; edit semantics for LTE-scoped
  `Girl`/`Job`/`Hobby` blocks (e.g. whether editing them affects anything once the event ends) are unconfirmed - treat
  edits there as out of scope unless asked.
- `docs/FLINGS.md`'s fling-ID → girl mapping is WIP (most IDs unmapped/unconfirmed) - don't treat it as complete.
- `dchk`, `ana.ev`/`ana.vid` appear to be irrelevant or analytics; ignore them.
- `Girl<Name>LifeGifts` (seen in real saves, both PC and Switch) isn't in any doc above and isn't in
  `tools/save_schema.py`'s registry - round-trips losslessly via the unrecognized-suffix fallback, but its meaning is
  unconfirmed. A good `investigate-save-field` candidate.
- `tools/blank_save.py` still targets the old flat-text format, not the new JSON - porting it (zeroing would become
  direct dict mutation instead of regex text surgery) is a reasonable follow-up, not done here.
