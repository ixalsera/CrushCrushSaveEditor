# File format

### PC/Steam

Named `crushcrush.sav` by default.

ASCII text, single line, **no trailing newline**:

```
base64( MAGIC + lzf_compress(plaintext_save_data) )
```

- `MAGIC` = fixed 3 bytes `97 37 dc` - a format/version marker, **not** a length field or checksum. Don't parse it as
  one.
- Base64 alphabet is standard (`+`, `/`, `=` padding) - nothing custom.

### Nintendo Switch

Named `CrushSaveData1` by default.

Plaintext/LZF payload in a different container:

```
<4-byte little-endian uint32, only value observed: 1><base64(MAGIC)><base64(lzf_compress(plaintext_save_data))>
```

- The leading 4 bytes are raw binary, not base64
- Unlike PC, `MAGIC` and the compressed body are base64-encoded **separately** and concatenated as text. `base64(MAGIC)`
  renders as the ASCII text `lzfc` (3 bytes divides evenly into base64's 4-char groups, so no padding)
- `decode_bytes`/`decode_file` in `tools/crushcrush_save.py` already handle Switch saves:
  `base64.b64decode()` silently drops the leading non-base64 header bytes, and decoding "lzfc" alone reproduces
  `MAGIC` exactly.
- `encode` needed a separate path, since PC's encode wraps everything in one base64 call and has no room for the leading
  header (`tools/crushcrush_save.py encode --nintendo`).

## LZF stream format (classic liblzf-compatible)

Control-byte encoding (literal run vs. back-reference) is documented in `utils/lzf.py`'s module docstring - read that
instead of re-deriving it here.

`utils/lzf.py`:

- `decompress(buf) -> bytes` - validated against actual game output, not just our own encoder's round-trip.
- `compress(data) -> bytes` - simple greedy LZ77 encoder; **not** byte-identical to the game's own encoder, but valid

## Plaintext save structure

This is the save's own internal representation, decompressed - `tools/save_schema.py` translates it to/from the
structured JSON described below, and the CLI never exposes it directly, but it's still the ground truth `save_schema.py`
works against. Decompressed, the save is a flat, newline-delimited key-value dump (no JSON/XML).

### PC-specific structure

For PC/Steam, the game applies prefix compression at the *application* layer (independent of LZF):

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

### Timestamp fields

`GameState.Date`, `DateUTC`, `LoginDate`, `Task<N>Start`, `C<N>D` (long, unsuffixed, timestamp-shaped) are .NET
`DateTime.ToBinary()` values. Use `utils/timestamp.py` instead of re-deriving inline - `decode` takes raw values
from a save/diff and prints `DateTimeKind` + ISO datetime (sentinels print as `N/A`/`never`); `encode` reverses it. Uses
exact integer tick arithmetic, not `timedelta.total_seconds()` (loses sub-second precision here via float rounding).

Investigating an unconfirmed field (diffing saves before/after a play session, decoding blob bitmasks, diffing Phone
Fling state) is its own workflow - see the `investigate-save-field` skill instead of repeating it here.
