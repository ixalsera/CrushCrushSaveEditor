# Girls

Unlocking girls is not as simple as just toggling their `Hearts` value to non-zero, it seems to be controlled by two
fields:
`GirlsUnlocked` - The bitmask of girls unlocked in the current reset.

`GirlsPreviouslyUnlocked` - The seemingly more authoritative value that determines whether a girl has *ever* been
unlocked in this save file.

## Mapping

The below table lists the currently suspected mapping between bit index and girl as determined from save file analysis:

| Index | Girl      |
|-------|-----------|
| 0     | Cassie    |
| 1     | Mio       |
| 2     | Quill     |
| 3     | Elle      |
| 4     | Nutaku    |
| 5     | Iro       |
| 6     | Bonnibel  |
| 7     | Ayeka     |
| 8     | Fumi      |
| 9     | Bearverly |
| 10    | Nina      |
| 11    | Alpha     |
| 12    | Pamu      |
| 20    | Jelle     |
| 21    | Quillzone |
| 22    | Bonchovy  |
| 23    | Spectrum  |
| 26    | Shibuki   |
| 30    | Peanut    |
| 84    | Lumi      |

These IDs are used to reference girls in `GirlsUnlocked`, `GirlsPreviouslyUnlocked` and `CurrentGirl`, at the very
least. It is likely that if a bitmask represents a girl, the bit index will match the above table.

## Event Girls

## DLC Girls

At the moment it is unclear whether paid DLC girls will unlock simply by flipping their bit in `GirlsUnlocked`. It seems
unlikely that this would work; I imagine the game does a DLC ownership check on save load. I could be wrong. At any
rate, using these tools to unlock paid DLC is not condoned by the project maintainer. If you want the girl, show the
devs your appreciation for their hard work.

Related, confirmed data point: loading a save with a blanked/local `Ids`, `GirlsUnlocked`, and `BlayfapAwardedItems`
back into the game on an account that legitimately owns several DLC/bundle girls (Jelle, Quillzone, Bonchovy, Spectrum,
Shibuki, Lumi) caused the game to restore `Ids` to its original value and re-flip every one of those girls' bits,
alongside re-populating `BlayfapAwardedItems` and `Playfab.Inventory`/`Participation` - all from server/account state,
independent of what was in the local save. So DLC ownership is authoritative server/account-side, not derived from the
local save's bits at all; this doesn't yet say anything about the reverse case (flipping a bit for DLC the account does
*not* own).

## Outfits

Premium outfits are tracked per-Girl in their `LifeOutfits` field. This appears to be a bitmask of unlocked outfits with
each bit indicated which outfit is unlocked for that girl.

The table below shows bit mapping to outfit sets. Note that not all girls can get all outfits so some bits may be
ignored for a girl (i.e. if she does not have a `DX Wedding Dress`, she probably won't ever get that bit flipped and
flipping it will do nothing).

| ID | Outfit                                                                     |
|----|----------------------------------------------------------------------------|
| 1  | ?                                                                          |
| 2  | DX Wedding Dress (unconfirmed; this is at least true for Tessa and Amelia) |
| 18 | Diamond Ring/School Uniform/Holiday (unconfirmed)                          |
| 19 | Diamond Ring/School Uniform/Holiday (unconfirmed)                          |
| 20 | Bathing Suit                                                               |
| 21 | Quill's Fuzzy Festival Outfit                                              |
| 22 | Diamond Ring/School Uniform/Holiday (unconfirmed)                          |
| 29 | Lingerie                                                                   |
| 30 | Birthday Suit                                                              |

Unlocking outfits (bathing suit etc.) does **not** automatically propagate that bit to every relevant Girl's
`LifeOutfits`. Instead, it seems like that bit is only added at the earliest when you next change their outfit and at
the latest when you switch to that specific one

### Equipped Outfits

Equipping an outfit for a girl will set a bit on her `Clothing` field. See the table above for the known outfit mappings.
