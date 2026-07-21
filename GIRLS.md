# Girls

Unlocking girls is not as simple as just toggling their `Hearts` value to non-zero, it seems to be controlled by two fields:
`GirlsUnlocked` - The bitmask of girls unlocked in the current reset.

`GirlsPreviouslyUnlocked` - The seemingly more authoritative value that determines whether a girl has *ever* been unlocked in this save file.

## Mapping

The below table lists the currently suspected mapping between bit index and girl as determined from save file analysis:

| Index | Girl      |
|-------|-----------|
| 0     | Cassie    |
| 20    | Jelle     |
| 21    | Quillzone |
| 22    | Bonchovy  |
| 23    | Spectrum  |
| 26    | Shibuki   |
| 30    | Peanut    |
| 84    | Lumi      |

## Event Girls


## DLC Girls

At the moment it is unclear whether paid DLC girls will unlock simply by flipping their bit in `GirlsUnlocked`. It seems unlikely that this would work; I imagine the game does a DLC ownership check on save load. I could be wrong. At any rate, using these tools to unlock paid DLC is not condoned by the project maintainer. If you want the girl, show the devs your appreciation for their hard work.

## Outfits

### Shibuki
Shibuki's premium outfit (unlocked on purchase) adds `LifeOutfits:1616642048i` to her data.