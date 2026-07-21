# CrushCrushSaveEdit

Tooling to decode, edit, and re-encode save files for the game **Crush Crush**
(Sad Panda Studios). This file documents the reverse-engineered save format and
the tools already built so that format discovery never has to be repeated.
For a detailed, per-key breakdown of what's inside the decoded plaintext
(every top-level key, nested object schemas like `Girl`/`Job`/`Hobby`, and
the per-LTE "Event Schemas"), see `SCHEMA.md`.

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
  (e.g. just a `Goals` field or a single `GameState.Date`). See
  `SCHEMA.md`'s "Event Schemas" section for the known prefix -> event name
  mapping and per-event key details. The top-level (unprefixed) keys remain
  "the" active save state - that's what the user's stated facts (3
  diamonds, Cassie/Mio Love:9) matched against, not any `pes<N>` block.

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
- `pes<N>` prefixes are understood to be per-LTE (limited-time event) data
  (see above and `SCHEMA.md`), but the full prefix -> event mapping is only
  confirmed for 3 events so far, and exact edit semantics for LTE-scoped
  `Girl`/`Job`/`Hobby` blocks (e.g. whether editing them affects anything
  visible once the event has ended) remain unconfirmed - still treat edits
  there as out of scope unless asked.
