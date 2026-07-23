# Phone Flings

Phone flings are simple text and photo conversations in the style of MMS messaging between the player and certain girls.
For the most part, these flings do not relate to an actual Core Girl but some of them may have unlockable Event Girls for
the primary game system. Conversely, once a Core Girl has been leveled up to Lover level, the player can unlock her Phone
Fling for 10 diamonds.

## Mapping

Phone Fling data are stored in the save file using an ID instead of the Girl's name. The ID of a phone fling girl has no
bearing on her bit index for `GirlsUnlocked` (in the event she does have an unlockable date) and vice versa, i.e. Cassie
has the `GirlsUnlocked` index of `0` but the Phone Fling ID `23` and Peanut has the Phone Fling ID of `1` but the
`GirlsUnlocked` index of `30`.

The table below attempts to map the fling ID with the girl it represents:

| Fling ID | Name                |
|----------|---------------------|
| 0        | Unused              |
| 1        | Peanut              |
| 2        | Wendy               |
| 3        | Generica            |
| 4        | Lotus               |
| 5        | Sophia              |
| 6        | Caitlin             |
| 7        | Ruri                |
| 8        | Miss Desiree        |
| 9        | Honey               |
| 10       | Sawyer              |
| 11       | Lake                |
| 12       | Willow              |
| 13       | Nova                |
| 14       | Blanche (Suspected) |
| 16       | Renee               |
| 19       | Amelia (Suspected)  |
| 20       | Dr Fumi (Suspected) |
| 23       | Cassie (Suspected)  |
| 24       | Mio                 |
| 25       | Quill (Suspected)   |
| 26       | Elle (Suspected)    |
| 27       | Iro (Suspected)     |

## Data

`C<N>D` represents the time the conversation was last viewed. If a Fling has been unlocked - i.e. its bit is flipped on
in `UnlockedPFS` - but has never been opened, this will remain `0`. `C<N>P`, on the other hand, represents the
conversation state.

The following has been observed:

- `C<N>P` changes with conversations regardless of whether a pic was received (thus `P` is unlikely to be about actual
  pics received as I initially suspected)
- Comparing across saves shows changes to three of the four fields:
    - a leading 16-bit value ticks up by a tiny amount; this is the conversation/message counter (whether it's
      specifically sent+received combined, vs. some other tally, is still just a one-data-point hypothesis)
    - the second 16-bit value also ticks up, independently of the first - seen +1 in a sample where the player sent
      exactly one message, suggesting a possible sent-only counter, but this is unconfirmed
    - the 32-bit value that follows those two counts down towards single digits; this is likely the `nextMessageDelay`
      determining the ticks/seconds until the next message is shown
- `C<N>P` is empty for flings that have not been started (pairs 1:1 with `C<N>D:0`)
- That 32-bit delay reads as exactly `4294967292` (`0xFFFFFFFC`, i.e. `-4` as a signed 32-bit int) on every fling whose
  `C<N>D` is the "needs an unlock requirement" sentinel (`int64.max`) - but also on a few flings with an otherwise
  ordinary `C<N>D`. Looks like an independent "conversation currently gated, no countdown running" flag on the `P` blob
  itself rather than just a mirror of `D`'s sentinel; unconfirmed why an active-looking fling would carry it
- Conversations awaiting a player choice have the delay/countdown set to `0`

We can derive a blob structure for the data thus (pseudocode; confirmed against every fling in a real save, see
`tools/phone_fling.py`):

```
struct PhoneFlingData {
  u16 TotalMessageCounter    // Fling message count + player message count
  u16 PlayerMessageCounter   // suspected but still not enough data
  u32 NextMessageCountdown   // 0xFFFFFFFC sentinel = locked/gated, not a literal countdown
  byte[] Trailing            // variable length (1-7 bytes seen); unparsed
}
```

What `Trailing` is, is currently unclear. Potentially `Trailing` is the player's conversational choices as a bitmask for
replaying the conversation correctly.

Use `tools/phone_fling.py decode` to parse a `C<N>P` blob against this structure - it already handles the empty-blob and
locked-sentinel states above instead of misparsing or crashing on them.