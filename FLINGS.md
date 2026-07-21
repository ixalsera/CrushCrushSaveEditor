# Phone Flings (WIP)

## Mapping
Phone Fling data are stored in the save file using an index instead of the Girl's name. The table below attempts to map the fling ID with the girl it represents:

| Fling ID | Name                         |
|----------|------------------------------|
| 5        | Sophia                       |
| 7        | Ruri                         |
| 8        | Sawyer (Partially confirmed) |
| 9        | Honey                        |
| 13       | Nova                         |

## Data

While `C<N>D` represents the time the last message was received, `C<N>P` likely represent the conversation state. The following has been observed:

- `C<N>P` changes with conversations regardless of whether a pic was received (thus `P` is unlikely to be about actual pics received as I initially suspected)
- Comparing across saves shows changes to three of the four fields:
  - a leading 16-bit value ticks up by a tiny amount; this is the conversation/message counter (whether it's specifically sent+received combined, vs. some other tally, is still just a one-data-point hypothesis)
  - the second 16-bit value also ticks up, independently of the first - seen +1 in a sample where the player sent exactly one message, suggesting a possible sent-only counter, but this is unconfirmed
  - the 32-bit value that follows those two counts down towards single digits; this is likely the `nextMessageDelay` determining the ticks/seconds until the next message is shown
- `C<N>P` is empty for flings that have not been started (pairs 1:1 with `C<N>D:0`)
- That 32-bit delay reads as exactly `4294967292` (`0xFFFFFFFC`, i.e. `-4` as a signed 32-bit int) on every fling whose `C<N>D` is the "needs an unlock requirement" sentinel (`int64.max`) - but also on a few flings with an otherwise ordinary `C<N>D`. Looks like an independent "conversation currently gated, no countdown running" flag on the `P` blob itself rather than just a mirror of `D`'s sentinel; unconfirmed why an active-looking fling would carry it

We can derive a blob structure for the data thus (pseudocode; confirmed against every fling in a real save, see `tools/phone_fling.py`):
```
struct PhoneFlingData {
  u16 MessageCounter
  u16 UnknownValue           // possibly a sent-message-only counter; unconfirmed
  u32 NextMessageCountdown   // 0xFFFFFFFC sentinel = locked/gated, not a literal countdown
  byte[] Trailing            // variable length (1-7 bytes seen); unparsed
}
```

What `UnknownValue` and `Trailing` are is currently unclear. Potentially `Trailing` is the player's conversational choices as a bitmask for replaying the conversation correctly as well as potentially some indication of seen photos.

Use `tools/phone_fling.py decode` to parse a `C<N>P` blob against this structure - it already handles the empty-blob and locked-sentinel states above instead of misparsing or crashing on them.