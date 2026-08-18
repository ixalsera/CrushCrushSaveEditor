# Unlocks (Playfab / Blayfap)

This documents what's been confirmed about `BlayfapAwardedItems` and the
`Playfab` object's bitmask/list fields specifically - i.e. the two places in the save that track account-level
entitlements rather than in-save progression. For per-girl bit mappings (`GirlsUnlocked`, `Clothing`,
`LifeOutfits`), see [GIRLS.md](GIRLS.md) - this file only covers the Playfab/Blayfap side of things.

## Both are server/account-authoritative, not save-authoritative

Confirmed by loading a synthetic save with `BlayfapAwardedItems` emptied,
`Playfab.Inventory`/`Participation` zeroed, and `GameState.Ids` removed entirely: on next launch, the same account's
real entitlements came back in full - `Ids` was restored to its original value, `BlayfapAwardedItems` was repopulated
with the full historical bundle list, and `Playfab.Inventory`/
`Participation` were restored to their real (non-zero) values. None of this is derived from the local save file at all;
it's fetched fresh from the server keyed off the account each time the game launches. Blanking these fields locally does
not revoke or hide anything the account actually owns.

## `BlayfapAwardedItems`

- Shape: `blob` = base64 of a **plain pipe-delimited text list** (not a binary bitmask, despite `blob` covering both in
  the general schema)
- List items: Usually a premium bundle identifier or set of premium unlocks. Note that the DLC Kaiju are listed
  individually but the premium unlocks (Jelle, Bonchovy etc.) use their concatenated bundle name, i.e
  `jellequillzone` (`jelle`+`quillzone`) and `bonchovyspectrum` (`bonchovy`+`spectrum`)
- Associated field changes: when a new entry marks the unlocking of a new Girl/Girls, `GirlsUnlocked`/
  `GirlsPreviouslyUnlocked` flip their corresponding bits.
- `july2017` has been seen appearing and disappearing across different syncs of the *same* account with no corresponding
  local edit - the list the server returns isn't perfectly stable/deterministic run to run.

## `Playfab.Inventory`

- Shape: `int` bitmask
- This bitmask draws from the **same bit positions** used for the shared/global costume bits seen across multiple girls'
  `LifeOutfits`/`Clothing` (see GIRLS.md) - it isn't girl-specific, it's an account-wide "which shared costumes are
  owned" record.
- A single purchase updates `Playfab.Inventory` and every relevant girl's `LifeOutfits` together, atomically.

## `Playfab.Participation`

- Shape: `blob`, 7-byte bitmask
- Bit index equals the parallel event ID (`pes<N>`) - one bit set per parallel event ever started, permanently.

## `Playfab.FlingPurchases`

- Shape: `long`, bitmask
- Bits fill low-to-high, one per Core Girl fling purchased (see [FLINGS.md](FLINGS.md)), in fixed roster order.
- Distinct from `UnlockedPFS`, which tracks every fling ever unlocked (Core Girl or not) rather than just the premium
  Core Girl subset.

## Open questions

- Whether manually setting a `Playfab.Inventory` bit or adding a
  `BlayfapAwardedItems` entry for something the account doesn't actually own would work client-side or get silently
  clobbered by a server-side ownership check on next launch - untested (and, per `GIRLS.md`, not something this project
  condones trying for paid DLC either way).
- Full bit-index → costume-name mapping for `Playfab.Inventory` beyond 20/29/30.
- What `Playfab.Participation` actually tracks.
