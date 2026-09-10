---
name: investigate-save-field
description: Confirm what an unconfirmed CrushCrushSaveEdit save field means - diffing saves before/after a play session, decoding blob bitmasks, or diffing Phone Fling state. Use when a field in docs/SCHEMA.md, GIRLS.md, FLINGS.md, or EVENTS.md is marked unconfirmed and needs verifying against real save data.
---

Keep a `*.prev.sav`/`*.prev.json` snapshot from before a play session (`python3 tools/rotate_save.py` rotates), take a
new save after, and diff the two **flattened JSON path sets** - not a raw text/JSON diff (dict key order isn't
guaranteed stable and nesting hides which leaf actually changed). Use `scripts/diff_saves.py <prev.json> <cur.json>`
(or single-arg `scripts/diff_saves.py <file.json>` to just dump one file's flattened `dotted.path: value` pairs, e.g.
for grepping by `Jobs.<Name>`/`Girls.<Name>` prefix) rather than re-deriving the flattening inline.

For base64 `blob` fields that are bitmasks or pipe-delimited text (`GirlsUnlocked`, `GirlsPreviouslyUnlocked`,
`UnlockedPFS`, `BlayfapAwardedItems`), use `scripts/decode_blob.py` rather than re-deriving inline - `bits`/`text`
decode a single value, `diff-bits`/`diff-text` decode two and print what was added/removed (handles the bitmask growing
a byte between saves, as `GirlsUnlocked`/`UnlockedPFS` both do).

For a Phone Fling specifically, diff the `C<N>D`/`C<N>P` keys directly (e.g. `grep -oE '^C[0-9]+[DP]:.*'` over both
files) rather than grepping for a girl's name - the save has no name-keyed fling data, so a name search only confirms
the `Girl<Name>` block exists, not whether her fling changed. Use `tools/phone_fling.py decode` to break down a
`C<N>P` blob - it already handles the "never started" (empty blob) and "locked/gated" (sentinel countdown) states that a
naive parse will otherwise crash or get confused on.
