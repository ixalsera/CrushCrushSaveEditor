# Girls

Unlocking girls is not as simple as just toggling their `Hearts` value to non-zero, it seems to be controlled by two
fields:
`GirlsUnlocked` - The bitmask of girls unlocked in the current reset.

`GirlsPreviouslyUnlocked` - The seemingly more authoritative value that determines whether a girl has *ever* been
unlocked in this save file.

## Mapping

The below table lists the currently suspected mapping between bit index and girl as determined from save file analysis:

| Index | Girl                  |
|-------|-----------------------|
| 0     | Cassie                |
| 1     | Mio                   |
| 2     | Quill                 |
| 3     | Elle                  |
| 4     | Nutaku                |
| 5     | Iro                   |
| 6     | Bonnibel              |
| 7     | Ayeka                 |
| 8     | Fumi                  |
| 9     | Bearverly             |
| 10    | Nina                  |
| 11    | Alpha                 |
| 12    | Pamu                  |
| 20    | Jelle                 |
| 21    | Quillzone             |
| 22    | Bonchovy              |
| 23    | Spectrum              |
| 26    | Shibuki               |
| 30    | Peanut                |
| 45    | Mallory               |
| 68    | Ginger & Wasabi       |
| 71    | Mortha (Unconfirmed)  |
| 72    | Sephia  (Unconfirmed) |
| 73    | Liz (Unconfirmed)     |
| 82    | Lydia (Unconfirmed)   |
| 84    | Lumi                  |

These IDs are used to reference girls in `GirlsUnlocked`, `GirlsPreviouslyUnlocked` and `CurrentGirl`, at the very
least. It is likely that if a bitmask represents a girl, the bit index will match the above table.

## Event Girls

At the moment it is unclear whether event girls will unlock simply by flipping their bit in `GirlsUnlocked`. It seems
unlikely that this would work; the "entitlement" is essentially stored in the `BlayfapAwardedItems` field which is
fetched from the server on launch. I don't know whether this would be merged with the existing value but considering I
have seen the `july2017` event entitlement appear and disappear numerous times, it's probable there's some server
validation happening. I could be wrong.

## DLC Girls

It's also unclear whether paid DLC girls will unlock simply by flipping their bit in `GirlsUnlocked` either. I imagine
the game does a DLC ownership check on save load. Again, I could be wrong. At any rate, using these tools to unlock paid
DLC is not condoned by the project maintainer. If you want the girl, show the devs your appreciation for their hard work
and fork over the cost of a coffee for her.

## Outfits

Premium outfits are tracked per-Girl in their `LifeOutfits` field. This appears to be a bitmask of unlocked outfits with
each bit indicating which outfit is unlocked for that girl.

The table below shows bit mapping to outfit sets. Note that not all girls can get all outfits so some bits may be
ignored for a girl (i.e. if she does not have a `DX Wedding Dress`, she probably won't ever get that bit flipped and
flipping it will do nothing).

| ID | Outfit                                                                     |
|----|----------------------------------------------------------------------------|
| 1  | ?                                                                          |
| 2  | DX Wedding Dress (unconfirmed; this is at least true for Tessa and Amelia) |
| 18 | Holiday                                                                    |
| 19 | School Uniform                                                             |
| 20 | Bathing Suit                                                               |
| 21 | Quill's Fuzzy Festival Outfit                                              |
| 22 | Diamond Ring (unconfirmed)                                                 |
| 29 | Lingerie                                                                   |
| 30 | Birthday Suit                                                              |

Unlocking outfits (bathing suit etc.) does **not** automatically propagate that bit to every relevant Girl's
`LifeOutfits`. Instead, it seems like that bit is only added at the earliest when you next change their outfit and at
the latest when you switch to that specific one

### Equipped Outfits

Equipping an outfit for a girl will set a bit on her `Clothing` field. See the table above for the known outfit
mappings.
