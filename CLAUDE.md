# CrushCrushSaveEdit

Decode/edit/re-encode save files for **Crush Crush** (Sad Panda Studios). Reverse-engineered format + tools below, so
format discovery isn't repeated.

Per-key docs - check before re-deriving what a field means:

| File                     | Covers                                                                                                                                                                    |
|--------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `docs/SCHEMA.md`         | Every top-level key + nested object schemas (`Girl`, `Job`, `Hobby`, `Task`, `ACH`, Phone Fling, etc) from a raw save (not parsed JSON).                                  |
| `docs/EVENTS.md`         | `pes<N>` parallel-event prefix→event mapping + event-scoped schemas, plus LTE IDs.                                                                                        |
| `docs/FLINGS.md`         | Phone Fling (`C<N>D`/`C<N>P`): fling-ID→girl mapping + `C<N>P` blob decoding. A fling does not correspond to any `Girl<Name>` block.                                      |
| `docs/GIRLS.md`          | `GirlsUnlocked`/`GirlsPreviouslyUnlocked` bit-index→girl mapping, plus per-girl `Clothing`/`LifeOutfits` outfit-bit findings.                                             |
| `docs/UNLOCKS.md`        | Same bitmask/list analysis as `docs/GIRLS.md`, but for account-level `Playfab`/`BlayfapAwardedItems` - both are server-synced on launch, not derived from the local save. |
| `docs/ACHIEVEMENTS.md`   | `ACH.<id>` bitmask-per-tier mechanism + achievement ID→name mapping.                                                                                                      |
| `docs/SWITCH.md`         | Keys present in a Switch save that are absent from the sampled PC saves (root `GameState`/`Settings` gaps, etc.).                                                         |
| `docs/NUTAKU.md`         | Nutaku/BlayFap web build: where the save actually lives (server-side, not browser storage) and the fetch/update API that replaces a physical save file.                   |
| `docs/structure/RAW.md`  | Describes the **raw** structure of a decoded save file (before parsing to JSON).                                                                                          |
| `docs/structure/JSON.md` | Describes the JSON representation of a decoded save file and how it is derived.                                                                                           |

## Directory layout

```
saves/     Real save files, exactly as copied from the game, may have any name. Never hand-edit
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

## Standard live save locations

These locations contain live save files for pulling in. Never touch them except to copy in to a working directory like
`saves/`.

- Steam: User's Steam directory (dependent on platform) -> `userdata/<steamID>/459820/remote/crushcrush.sav`
- PC (non-Steam): User config directory (`~/.config` or `AppData/LocalLow`) ->
  `unity3d/Sad Panda Studios/Crush Crush/OfflineSaves/crushcrush.sav`
- Switch: Not directly accessible; ask for location
- Web/Nutaku: Not directly accessible; ask for blob

## Standard edit workflow

1. Rotate: `uv run tools/rotate_save.py <save_game_filename>`
2. Decode: `uv run tools/crushcrush_save.py decode "saves/<save_game_filename>.sav" "decoded/<save_game_filename>.json"`
3. Edit: `decoded/<save_game_filename>.json` per `docs/structure/JSON.md`.
4. Encode: (add `--nintendo` to output a Switch save):
   `uv run tools/crushcrush_save.py encode "decoded/<save_game_filename>.json" "saves/<save_game_filename>.edited.sav"`
5. **Always verify before overwriting a real save**. Decode the newly encoded file again and diff it against the edited
   JSON: `uv run scripts/diff_saves.py <prev.json> <cur.json>`.
6. Only after the diff is clean, replace `saves/<save_game_filename>.sav` (back it up first as
   `<save_game_filename>.backup.sav`).

## Known caveats

- `docs/FLINGS.md`'s fling-ID → girl mapping is WIP (most IDs unmapped/unconfirmed) - don't treat it as complete.
- `dchk`, `ana.ev`/`ana.vid` appear to be irrelevant or analytics; ignore them.
- Edits to `pes<N>`-scoped `Girl`/`Job`/`Hobby` blocks are out of scope unless asked.

## Open items / not yet done

- No value-specific validation (e.g. `Love` 0-9, `Diamonds` non-negative) is enforced - edits are freeform JSON.
  Building an actual editor UI/CLI for specific fields is new work, not started.
- A future editor could push/pull saves directly against Nutaku's BlayFap backend (see `docs/NUTAKU.md`) instead of
  only local `.sav` files - fetch/edit/save round-trip against the live API is confirmed working, not just decode.
