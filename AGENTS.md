# CrushCrushSaveEdit

Tooling to decode, edit, and re-encode save files for the game **Crush Crush**
(Sad Panda Studios). This file documents the reverse-engineered save format and
the tools already built so that format discovery never has to be repeated.

Per-key documentation lives in three files - check these before re-deriving
what a field means:
- `SCHEMA.md` - every top-level key, and nested object schemas (`Girl`,
  `Job`, `Hobby`, `Task`, `ACH`, Phone Fling, etc).
- `EVENTS.md` - the `pes<N>` limited-time-event prefixes: which event each
  number maps to, and their event-scoped schemas.
- `FLINGS.md` - the Phone Fling feature (`C<N>D`/`C<N>P`): fling-ID-to-girl
  mapping (WIP, mostly unconfirmed) and what's been decoded of the `C<N>P`
  blob so far. The save only ever stores the numeric fling index (`C<N>`) -
  it never stores a girl's name against a fling, and a fling doesn't
  necessarily correspond to any `Girl<Name>` block in the roster (the
  ID-to-girl mapping is a separate, unconfirmed lookup table maintained in
  `FLINGS.md`, not something recoverable from the save itself).

## Directory layout

```
saves/     Real save files, exactly as copied from the game. Never hand-edit
           these directly - decode, edit the plaintext, re-encode.
decoded/   Human-readable plaintext dumps produced by tools/crushcrush_save.py.
           Regenerate freely; not authoritative once saves/ changes.
tools/     The decode/encode implementation (Python 3, stdlib only).
```

Save files may have any name but the default as used by the game itself is simply `crushcrush.sav`

## File format (reverse-engineered, confirmed by full round-trip)

A `.sav` file is ASCII text, single line, **no trailing newline**:

```
base64( MAGIC + lzf_compress(plaintext_save_data) )
```

- `MAGIC` = fixed 3 bytes `97 37 dc`. Identical across every save observed
  (different content, different plaintext length) - it is a format/version
  marker, **not** a length field or checksum. Do not try to parse it as one.
- After base64-decoding, the LZF-compressed data starts immediately after
  those 3 bytes.
- Base64 alphabet is standard (`+`, `/`, `=` padding) - nothing custom. 

### LZF stream format (classic liblzf-compatible)

Implemented in `tools/lzf.py`. Per control byte `ctrl`:

- `ctrl < 32`: literal run, `ctrl + 1` raw bytes follow.
- `ctrl >= 32`: back-reference.
  - `length_field = ctrl >> 5` (0-7)
  - if `length_field == 7`: an extra length byte follows; `length = 7 + extra_byte + 2`
  - else: `length = length_field + 2`
  - `offset = ((ctrl & 0x1f) << 8) + next_byte + 1` (1..8192 bytes back from
    current output position)
  - copy `length` bytes from `output[-offset:]`, byte-by-byte (overlapping
    copies for run-length-style repeats are valid and expected).

`tools/lzf.py` provides:
- `decompress(buf) -> bytes` - implements the above exactly; used to read
  real game saves, so it is validated against actual game output (not just
  round-trip against our own encoder).
- `compress(data) -> bytes` - a simple greedy LZ77 encoder that emits valid
  LZF tokens. It is **not** byte-identical to whatever encoder the game
  itself uses (ours is smaller, even), but validity only requires that
  `decompress(compress(x)) == x`, which is verified below - LZF decompression
  doesn't care how the compressor decided to encode things.

## Plaintext save structure

Once decompressed, the save is a flat, newline-delimited list of entries.
There is no top-level JSON/XML - it's closer to a flattened key-value dump
with prefix compression at the *application* layer (independent of LZF):

- A bare line `::` resets to "no active prefix"; the next line is a
  self-contained `key:value` entry.
- A line `::SomeName` starts a section/prefix named `SomeName`; subsequent
  lines until the next `::` are **suffixes** that should be concatenated
  onto that prefix to get the real key, e.g.:
  ```
  ::GirlCassie
  Clothing:1073741824i
  Hearts:204188
  LifeDates:17i
  LifeOutfits:1610612736i
  Love:9i
  ```
  means `GirlCassieClothing:1073741824i`, `GirlCassieHearts:204188`, ...,
  `GirlCassieLove:9i`.
- Value type suffixes seen: `i` = integer, `f` = float, no suffix = plain
  integer/long or an empty/flag value (bare key with no `:value` at all is
  a boolean-ish flag, e.g. `Locked`, `Active`, `Gilded`).
- Keys prefixed with `pes<N>` (e.g. `pes27GameStateDate`,
  `pes27GirlQuillHearts`) are **not** a second save slot/profile - they're
  per-**Limited-Time-Event (LTE)** data. Each event mirrors whatever part of
  the root schema it needs: some (`pes27`) bundle a near-complete copy
  (their own `GameState`, `Job`, `Hobby`, `Girl` blocks, with their own
  hobby-name set), others (`pes53`, `pes54`) are much smaller fragments
  (e.g. just a `Goals` field or a single `GameState.Date`). See `EVENTS.md`
  for the confirmed prefix -> event name mapping (`pes27`=Fuzzy Festival,
  `pes53`/`pes54`=Roxxy) and per-event key details. The top-level
  (unprefixed) keys remain "the" active save state - that's what the user's
  stated facts (3 diamonds, Cassie/Mio Love:9) matched against, not any
  `pes<N>` block.
- The `C<N>D`/`C<N>P` numbered pairs are the **Phone Fling** feature
  (confirmed - see `SCHEMA.md`/`FLINGS.md`). `C<N>D` is a `DateTime` value
  (see below) for the last message received, or `int64.MaxValue` if the
  next message needs an extra unlock requirement met first. Flings are
  identified purely by their `<N>` index in the key name - there is no
  girl-name-keyed variant to search for, and no guarantee the index maps to
  a girl present in this save's roster at all.

### Timestamp fields

Long, unsuffixed fields that look like timestamps (e.g. `GameState.Date`,
`DateUTC`, `LoginDate`, `Task<N>Start`, `C<N>D`) are .NET `DateTime.ToBinary()`
values - confirmed by decoding and cross-checking against known play dates.
Given the raw 64-bit `value`:

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

Use `tools/timestamp.py` instead of re-deriving this inline - `decode` takes
one or more raw values straight from a decoded save/diff and prints the
`DateTimeKind` + ISO datetime for each (sentinels print as `N/A`/`never`);
`encode` does the reverse for writing an edited timestamp back into a save.
It uses exact integer tick arithmetic (not `timedelta.total_seconds()`,
which loses sub-second precision at this magnitude via float rounding).

### Investigating an unconfirmed field

The most reliable way to pin down what a field does: keep a `*.prev.sav` /
`*.prev.txt` snapshot from before a play session, take a new save after,
and diff the two **reconstructed key sets** (not a raw line diff - the `::`
prefix-compression reshuffles line order between saves, so a plain `diff`
on the raw decoded text is noisy). This is how the Phone Fling feature, the
per-level reset behavior of `Girl.Hearts`/`DateCount<N>`/`GiftCount<N>`, and
several bitmask/counter fields got confirmed - by pairing "what changed"
with what actually happened in the session (e.g. `decoded/crushcrush.prev.txt`
vs `decoded/crushcrush.txt` in this repo).

When the thing you're checking is specifically a Phone Fling, diff the
`C<N>D`/`C<N>P` keys directly (e.g. `grep -oE '^C[0-9]+[DP]:.*'` over both
files) - don't bother grepping for a girl's name first. The save has no
name-keyed fling data to find, so a name search only tells you whether that
girl's own `Girl<Name>` block exists, not whether her fling (if any) changed.
Use `tools/phone_fling.py decode` to break a `C<N>P` blob down instead of
re-deriving the byte layout inline - it also already knows about the
"never started" (empty blob) and "locked/gated" (sentinel countdown) states
that a naive parse of a fresh fling will otherwise crash or get confused on.

## Tools (`tools/`, Python 3, no third-party deps)

```
tools/lzf.py               compress(data: bytes) -> bytes
                            decompress(buf: bytes) -> bytes

tools/crushcrush_save.py   MAGIC = bytes.fromhex("9737dc")
                            decode_bytes(raw_b64_text: str) -> bytes   # plaintext
                            encode_bytes(plaintext_bytes: bytes) -> bytes  # b64 text
                            decode_file(in_path, out_path=None) -> str
                            encode_file(in_path, out_path=None) -> bytes

CLI:
  python3 tools/crushcrush_save.py decode <in.sav> [out.txt]
  python3 tools/crushcrush_save.py encode <in.txt> [out.sav]

tools/timestamp.py         decode(value: int) -> (kind: str, dt: datetime | None)
                            encode(dt: datetime, kind: str = "utc") -> int

CLI:
  python3 tools/timestamp.py decode <value> [value ...]
  python3 tools/timestamp.py encode <iso-datetime> [local|utc|unspecified]

tools/phone_fling.py       decode_conversation_state(blob_b64: str) -> dict | None
                            (a C<N>P blob's known/unknown fields, or None if
                            the blob is empty - see the module docstring for
                            the byte layout and two sentinel values found by
                            sweeping every fling in a real save)

CLI:
  python3 tools/phone_fling.py decode <C<N>P-blob> [<C<N>D-value>]
```

## Standard edit workflow

1. Decode: `python3 tools/crushcrush_save.py decode "saves/<save_game_filename>.sav" "decoded/<save_game_filename>.txt"`
2. Edit `decoded/<save_game_filename>.txt` as plain text (respecting the `::`
   prefix-section rules above - don't break the prefix/suffix pairing).
3. Encode back: `python3 tools/crushcrush_save.py encode "decoded/<save_game_filename>.txt" "saves/<save_game_filename>.edited.sav"`
4. **Always verify before overwriting a real save**: decode the newly
   encoded file again and diff its plaintext against the edited text (byte
   for byte). This has been validated to round-trip exactly for both sample
   files - if it ever doesn't match, something is wrong with the edit (e.g.
   a broken `::` section) rather than the tooling.
5. Only after the diff is clean, replace `saves/<save_game_filename>.sav` (make a
   backup copy first, `<save_game_filename>.backup.sav`).

## Open items / not yet done

- No value-specific validation (e.g. plausible ranges for `Love` 0-9,
  `Diamonds` non-negative) is enforced by the tools - edits are freeform
  text edits. If asked to build an actual editor UI/CLI for specific
  fields, that's new work, not yet started.
- `pes<N>` -> event name mapping (`EVENTS.md`) is confirmed for 3 prefixes
  only; exact edit semantics for LTE-scoped `Girl`/`Job`/`Hobby` blocks
  (e.g. whether editing them affects anything visible once the event has
  ended) remain unconfirmed - still treat edits there as out of scope
  unless asked.
- `FLINGS.md`'s fling-ID -> girl mapping is a work in progress (most IDs
  unmapped or unconfirmed) - don't treat it as complete.
- See `SCHEMA.md`'s own "Open questions" section for the current list of
  unidentified fields (`dchk`, `ana.ev`/`ana.vid`, achievement ID mapping,
  etc.) rather than duplicating it here.
