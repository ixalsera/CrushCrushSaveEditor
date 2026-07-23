# CrushCrushSaveEdit

Decode/edit/re-encode save files for **Crush Crush** (Sad Panda Studios). Reverse-engineered format + tools below, so
format discovery isn't repeated.

Per-key docs - check before re-deriving what a field means:

| File         | Covers                                                                                                                                                                                                        |
|--------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `SCHEMA.md`  | Every top-level key + nested object schemas (`Girl`, `Job`, `Hobby`, `Task`, `ACH`, Phone Fling, etc).                                                                                                        |
| `EVENTS.md`  | `pes<N>` parallel-event prefix→event mapping + event-scoped schemas, plus LTE IDs.                                                                                                                            |
| `FLINGS.md`  | Phone Fling (`C<N>D`/`C<N>P`): fling-ID→girl mapping + `C<N>P` blob decoding. The save stores only the numeric fling index - never a girl's name - and a fling need not correspond to any `Girl<Name>` block. |
| `GIRLS.md`   | `GirlsUnlocked`/`GirlsPreviouslyUnlocked` bit-index→girl mapping, plus per-girl `Clothing`/`LifeOutfits` outfit-bit findings.                                                                                 |
| `UNLOCKS.md` | Same bitmask/list analysis as `GIRLS.md`, but for account-level `Playfab`/`BlayfapAwardedItems` - both are server-synced on launch, not derived from the local save.                                          |

## Directory layout

```
saves/     Real save files, exactly as copied from the game. Never hand-edit
           these directly - decode, edit the plaintext, re-encode.
decoded/   Human-readable plaintext dumps produced by tools/crushcrush_save.py.
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

### LZF stream format (classic liblzf-compatible)

Implemented in `utils/lzf.py`. Per control byte `ctrl`:

- `ctrl < 32`: literal run, `ctrl + 1` raw bytes follow.
- `ctrl >= 32`: back-reference.
    - `length_field = ctrl >> 5` (0-7)
    - if `length_field == 7`: an extra length byte follows; `length = 7 + extra_byte + 2`
    - else: `length = length_field + 2`
    - `offset = ((ctrl & 0x1f) << 8) + next_byte + 1` (1..8192 bytes back from current output position)
    - copy `length` bytes from `output[-offset:]`, byte-by-byte (overlapping copies for run-length-style repeats are
      valid and expected).

`utils/lzf.py`:

- `decompress(buf) -> bytes` - validated against actual game output, not just our own encoder's round-trip.
- `compress(data) -> bytes` - simple greedy LZ77 encoder; **not** byte-identical to the game's own encoder, but valid
  since `decompress(compress(x)) == x` (LZF decompression doesn't care how the compressor chose to encode things).

## Plaintext save structure

Decompressed, the save is a flat, newline-delimited key-value dump (no JSON/XML) with prefix compression at the
*application* layer (independent of LZF):

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
  `GameState`/`Job`/`Hobby`/`Girl` blocks with their own hobby names; others just a stray field). See `EVENTS.md` for
  prefix→event mapping. Unprefixed keys remain "the" active save state.
- `C<N>D`/`C<N>P` numbered pairs are the **Phone Fling** feature (see `SCHEMA.md`/`FLINGS.md`). `C<N>D` = `DateTime` of
  last message received, or `int64.MaxValue` if the next message needs an extra unlock requirement. Flings are
  identified purely by `<N>` index - no girl-name-keyed variant exists, and the index isn't guaranteed to map to a girl
  present in this save's roster.

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

### Investigating an unconfirmed field

Keep a `*.prev.sav`/`*.prev.txt` snapshot from before a play session (`python3 tools/rotate_save.py` rotates), take a
new save after, and diff the two **reconstructed key sets** - not a raw line diff (`::` prefix-compression reshuffles
line order, so plain `diff` is noisy). Use `scripts/diff_saves.py <prev.txt> <cur.txt>` (or single-arg
`scripts/diff_saves.py <file.txt>` to just dump one file's reconstructed pairs, e.g. for grepping by
`Job<Name>`/`Girl<Name>` prefix) rather than re-deriving the reconstruction inline.

For base64 `blob` fields that are bitmasks or pipe-delimited text (`GirlsUnlocked`, `GirlsPreviouslyUnlocked`,
`UnlockedPFS`, `BlayfapAwardedItems`), use `scripts/decode_blob.py` rather than re-deriving inline - `bits`/`text`
decode a single value, `diff-bits`/`diff-text` decode two and print what was added/removed (handles the bitmask
growing a byte between saves, as `GirlsUnlocked`/`UnlockedPFS` both do).

For a Phone Fling specifically, diff the `C<N>D`/`C<N>P` keys directly (e.g. `grep -oE '^C[0-9]+[DP]:.*'` over both
files) rather than grepping for a girl's name - the save has no name-keyed fling data, so a name search only confirms
the `Girl<Name>` block exists, not whether her fling changed. Use `tools/phone_fling.py decode` to break down a
`C<N>P` blob - it already handles the "never started" (empty blob) and "locked/gated" (sentinel countdown) states
that a naive parse will otherwise crash or get confused on.

## Utils (`utils/`, Python 3, no third-party deps)

```
utils/lzf.py               compress(data: bytes) -> bytes
                            decompress(buf: bytes) -> bytes

utils/timestamp.py         decode(value: int) -> (kind: str, dt: datetime | None)
                            encode(dt: datetime, kind: str = "utc") -> int

CLI:
  python3 utils/timestamp.py decode <value> [value ...]
  python3 utils/timestamp.py encode <iso-datetime> [local|utc|unspecified]
```

## Tools (`tools/`, Python 3, no third-party deps)

```
tools/crushcrush_save.py   MAGIC = bytes.fromhex("9737dc")
                            decode_bytes(raw_b64_text: str) -> bytes   # plaintext
                            encode_bytes(plaintext_bytes: bytes) -> bytes  # b64 text
                            decode_file(in_path, out_path=None) -> str
                            encode_file(in_path, out_path=None) -> bytes

CLI:
  python3 tools/crushcrush_save.py decode <in.sav> [out.txt]
  python3 tools/crushcrush_save.py encode <in.txt> [out.sav]

tools/phone_fling.py       decode_conversation_state(blob_b64: str) -> dict | None
                            (a C<N>P blob's known/unknown fields, or None if
                            the blob is empty - see the module docstring for
                            the byte layout and two sentinel values found by
                            sweeping every fling in a real save)

CLI:
  python3 tools/phone_fling.py decode <C<N>P-blob> [<C<N>D-value>]

tools/rotate_save.py       rotate(name: str = "crushcrush") -> list[(src, dst)]
                            (moves saves/<name>.sav -> saves/<name>.prev.sav
                            and decoded/<name>.txt -> decoded/<name>.prev.txt,
                            overwriting any existing .prev. files; refuses to
                            rotate either file if the other's source is
                            missing, so a rotation never happens half-done)

CLI:
  python3 tools/rotate_save.py [name]   (default: crushcrush)

tools/blank_save.py        blank_out(template_text: str, now: datetime) -> str
                            (transforms a real decoded save into a
                            zero-progress/no-unlocks one, keyed off the
                            template's own key set rather than a hardcoded
                            schema copy - see the module docstring for the
                            call made on each unconfirmed field)

CLI:
  python3 tools/blank_save.py [template.txt] [output.txt]
    (default: decoded/crushcrush.prev.txt -> decoded/crushcrush.blank.txt)
```

## Scripts (`scripts/`, Python 3, no third-party deps)

```
scripts/diff_saves.py      reconstruct(path) -> dict[str, str]
                            (undoes the `::` prefix-compression into flat
                            key:value pairs - see "Plaintext save structure"
                            above)

CLI:
  python3 scripts/diff_saves.py <file.txt>              dump reconstructed pairs, sorted
  python3 scripts/diff_saves.py <prev.txt> <cur.txt>     diff two snapshots (added/removed/changed)

scripts/decode_blob.py     bits(b64) -> list[int]        (bitmask -> set bit indices)
                            text(b64) -> str              (base64-of-ASCII -> decoded text)

CLI:
  python3 scripts/decode_blob.py bits <base64>                    decoded bit indices set, and count
  python3 scripts/decode_blob.py text <base64>                    decoded pipe-delimited text
  python3 scripts/decode_blob.py diff-bits <base64_a> <base64_b>  bits added/removed, a -> b
  python3 scripts/decode_blob.py diff-text <base64_a> <base64_b>  pipe items added/removed, a -> b
```

## Standard edit workflow

1. Decode: `python3 tools/crushcrush_save.py decode "saves/<save_game_filename>.sav" "decoded/<save_game_filename>.txt"`
2. Edit `decoded/<save_game_filename>.txt` as plain text (respect the `::` prefix-section rules above - don't break
   the prefix/suffix pairing).
3. Encode back:
   `python3 tools/crushcrush_save.py encode "decoded/<save_game_filename>.txt" "saves/<save_game_filename>.edited.sav"`
4. **Always verify before overwriting a real save**: decode the newly encoded file again and diff its plaintext
   against the edited text (byte for byte). Validated to round-trip exactly for both sample files - if it doesn't
   match, the edit broke something (e.g. a broken `::` section), not the tooling.
5. Only after the diff is clean, replace `saves/<save_game_filename>.sav` (back it up first as
   `<save_game_filename>.backup.sav`).

## Open items / not yet done

- No value-specific validation (e.g. `Love` 0-9, `Diamonds` non-negative) is enforced - edits are freeform text.
  Building an actual editor UI/CLI for specific fields is new work, not started.
- `pes<N>` → event name mapping (`EVENTS.md`) confirmed for 2 prefixes only; edit semantics for LTE-scoped
  `Girl`/`Job`/`Hobby` blocks (e.g. whether editing them affects anything once the event ends) are unconfirmed - treat
  edits there as out of scope unless asked.
- `FLINGS.md`'s fling-ID → girl mapping is WIP (most IDs unmapped/unconfirmed) - don't treat it as complete.
- See `SCHEMA.md`'s "Open questions" section for unidentified fields (`dchk`, `ana.ev`/`ana.vid`, achievement ID
  mapping) rather than duplicating here.
