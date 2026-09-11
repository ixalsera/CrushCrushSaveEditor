# Girls

Unlocking girls is not as simple as just toggling their `Hearts` value to non-zero, it seems to be controlled by two
fields:
`GirlsUnlocked` - The bitmask of girls unlocked in the current reset.

`GirlsPreviouslyUnlocked` - The seemingly more authoritative value that determines whether a girl has *ever* been
unlocked in this save file.

## Mapping

The below table lists the currently suspected mapping between bit index and girl as determined from save file analysis:

| Index | Girl                      |
|-------|---------------------------|
| 0     | Cassie                    |
| 1     | Mio                       |
| 2     | Quill                     |
| 3     | Elle                      |
| 4     | Nutaku                    |
| 5     | Iro                       |
| 6     | Bonnibel                  |
| 7     | Ayeka/Ayano[^1]           |
| 8     | Fumi                      |
| 9     | Bearverly                 |
| 10    | Nina                      |
| 11    | Alpha                     |
| 12    | Pamu                      |
| 13    | Luna                      |
| 14    | Eva                       |
| 15    | Karma                     |
| 16    | Sutra                     |
| 17    | Dark One (Unconfirmed)    |
| 18    | Q-Piddy (Unconfirmed)     |
| 19    | ?????                     |
| 20    | Jelle                     |
| 21    | Quillzone                 |
| 22    | Bonchovy                  |
| 23    | Spectrum                  |
| 24    | ?????                     |
| 25    | ?????                     |
| 26    | Shibuki                   |
| 27    | Sirina                    |
| 28    | Catara                    |
| 29    | Vellatrix                 |
| 30    | Peanut                    |
| 31    | Roxxy                     |
| 32    | ?????                     |
| 33    | ?????                     |
| 34    | ?????                     |
| 35    | ?????                     |
| 36    | ?????                     |
| 37    | Ruri                      |
| 38    | Generica                  |
| 39    | ?????                     |
| 40    | Nova/Lustat (Unconfirmed) |
| 41    | Sawyer                    |
| 42    | ?????                     |
| 43    | ?????                     |
| 44    | ?????                     |
| 45    | Mallory                   |
| 46    | Lake                      |
| 47    | ?????                     |
| 48    | ?????                     |
| 49    | Lotus                     |
| 50    | ?????                     |
| 51    | ?????                     |
| 52    | Nova/Lustat (Unconfirmed) |
| 53    | ?????                     |
| 54    | ?????                     |
| 55    | ?????                     |
| 56    | ?????                     |
| 57    | ?????                     |
| 58    | ?????                     |
| 59    | ?????                     |
| 60    | ?????                     |
| 61    | ?????                     |
| 62    | ?????                     |
| 63    | ?????                     |
| 64    | Honey                     |
| 65    | ?????                     |
| 66    | ?????                     |
| 67    | ?????                     |
| 68    | Ginger & Wasabi           |
| 69    | ?????                     |
| 70    | ?????                     |
| 71    | Mortha                    |
| 72    | Sephia                    |
| 73    | Liz                       |
| 74    | Polly                     |
| 75    | ?????                     |
| 76    | ?????                     |
| 77    | ?????                     |
| 78    | ?????                     |
| 79    | ?????                     |
| 80    | ?????                     |
| 81    | ?????                     |
| 82    | Lydia (Unconfirmed)       |
| 83    | ?????                     |
| 84    | Lumi                      |
| 85    | Nixie                     |
| 86    | Ling Ling                 |

These IDs are used to reference girls in `GirlsUnlocked`, `GirlsPreviouslyUnlocked` and `CurrentGirl`, at the very
least. It is likely that if a bitmask represents a girl or girls, the bit index will match the above table. This can be
seen in the [parallel events](EVENTS.md) where the event-specific `GirlsUnlocked` bitmask uses these same indices.

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

#### Parallel Event Outfits

Interestingly, when playing a Parallel Event, Girls have their `Clothing` bitmask set to whatever outfit they are
supposed to wear for that event (such as "Bathing Suit" for the Beach Bash PE), but this is subsequently ignored by the
game. Setting this to any other outfit will not cause the Girl to don that outfit in the PE. Which makes me a Sad Panda.

## Dates

A Girl's `Dates` field holds a single bit marking the specific date currently required to progress to her next level
(see [SCHEMA.md](SCHEMA.md)). That same bit is added to her `LifeDates` bitmask once the date is completed.

| Bit | Date             |
|-----|------------------|
| 0   | Moonlight Stroll |
| 2   | Sightseeing      |
| 3   | Movie Theater    |
| 4   | Beach            |

[^1]: The PC save file still refers to Ayeka as Ayano (the Switch version still has her as Ayano). If editing or
adding fields for Ayeka, make sure they go under `GirlAyano`.