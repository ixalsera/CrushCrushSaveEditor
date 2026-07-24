# Unlocks (Playfab / Blayfap)

This documents what's been confirmed about `BlayfapAwardedItems` and the
`Playfab` object's bitmask/list fields specifically - i.e. the two places
in the save that track account-level entitlements rather than in-save
progression. For per-girl bit mappings (`GirlsUnlocked`, `Clothing`,
`LifeOutfits`), see [GIRLS.md](GIRLS.md) - this file only covers the
Playfab/Blayfap side of things.

## Both are server/account-authoritative, not save-authoritative

Confirmed by loading a synthetic save with `BlayfapAwardedItems` emptied,
`Playfab.Inventory`/`Participation` zeroed, and `GameState.Ids` removed
entirely: on next launch, the same account's real entitlements came back in
full - `Ids` was restored to its original value, `BlayfapAwardedItems` was
repopulated with the full historical bundle list, and `Playfab.Inventory`/
`Participation` were restored to their real (non-zero) values. None of this
is derived from the local save file at all; it's fetched fresh from the
server keyed off the account each time the game launches. Blanking these
fields locally does not revoke or hide anything the account actually owns.

## `BlayfapAwardedItems`

- Shape: `blob` = base64 of a **plain pipe-delimited text list** (not a
  binary bitmask, despite `blob` covering both in the general schema)
- Entries seen: single girl codenames (`shibuki`, `liz`, `lotus`, `lumi`,
  `lydia`, `mallory`, `mortha`, `sephia`), a non-girl LTE/store bundle
  marker (`pes27_storebundle`), a legacy item (`july2017`), and
  **concatenated two-girl bundle codenames with no separator**:
  `jellequillzone` (`jelle`+`quillzone`) and `bonchovyspectrum`
  (`bonchovy`+`spectrum`)
- Confirmed correlation: when a new entry has been observed appearing in a
  diff, it lined up exactly with new bits flipping in `GirlsUnlocked`/
  `GirlsPreviouslyUnlocked` - one compound two-name entry flips two bits at
  once. This has only been directly observed for `shibuki` (1 bit) and the
  two compound entries (2 bits each); the other single-name entries
  (`liz`/`lotus`/etc.) predate this session's observation window, so their
  bit correlation wasn't independently caught in the act, just inferred.
- `july2017` has been seen appearing and disappearing across different
  syncs of the *same* account with no corresponding local edit - the list
  the server returns isn't perfectly stable/deterministic run to run.

## `Playfab.Inventory`

- Shape: `int` bitmask
- Confirmed: this bitmask draws from the **same bit positions** used for
  the shared/global costume bits seen across multiple girls' `LifeOutfits`/
  `Clothing` (see GIRLS.md) - it isn't girl-specific, it's an account-wide
  "which shared costumes are owned" record.
- Bit meanings confirmed so far (cross-referenced against `Clothing`
  changes):
  - bit 20 = Bathing Suit
  - bit 29 = Lingerie
  - bit 30 = Birthday Suit (present on nearly every girl that has any
    `LifeOutfits` bits set at all - the closest thing to a "default")
- Observed changing exactly once this session: bits `29,30` → `20,29,30`,
  in the same diff as a 90-diamond spend and two girls' (`Cassie`, `Mio`)
  `LifeOutfits` gaining that identical new bit - strong evidence a single
  purchase updates `Playfab.Inventory` and every relevant girl's
  `LifeOutfits` together, atomically.

## `Playfab.Participation`

- Shape: `blob`, 7-byte bitmask
- Value has been **constant** (`AAAACAAAIA==`) across every save diffed
  this entire session, regardless of any unlock/purchase/progression
  activity tracked - no confirmed correlation with anything yet.
- `SCHEMA.md` speculates this might relate to "Ticket Booth"; still
  unconfirmed.

## `Playfab.FlingPurchases`

- Shape: `long` - **not** a bitmask, appears to be a simple counter
- Observed value: `1`, unchanged for the entire session. Included here only
  for completeness of the `Playfab` object; purpose still unconfirmed.

## Open questions

- Whether manually setting a `Playfab.Inventory` bit or adding a
  `BlayfapAwardedItems` entry for something the account doesn't actually
  own would work client-side or get silently clobbered by a server-side
  ownership check on next launch - untested (and, per `GIRLS.md`, not
  something this project condones trying for paid DLC either way).
- Full bit-index → costume-name mapping for `Playfab.Inventory` beyond
  20/29/30.
- What `Playfab.Participation` actually tracks.
