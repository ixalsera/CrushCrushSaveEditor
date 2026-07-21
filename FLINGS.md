# Phone Flings (WIP)

## Mapping
Phone Fling data are stored in the save file using an index instead of the Girl's name. The table below attempts to map the fling ID with the girl it represents:

| Fling ID | Name                 |
|----------|----------------------|
| 5        | Sophia (Unconfirmed) |
| 7        | Honey (Unconfirmed)  |
| 9        |                      |
| 13       | Nova                 |

## Data

While `C<N>D` represents the time since last message, `C<N>P` likely represent the conversation state. The following has been observed:

- `C<N>P` changes with conversations regardless of whether a pic was received (thus `P` is unlikely to be about actual pics received as I initially suspected)
- Comparing across saves shows the same two changes for each key/value pair:
  - a small leading 16-bit value ticks up by a tiny amount; this is likely the message incrementor
  - a middle 32-bit value collapses from a "large" number down to single digits; this is likely the `nextMessageDelay` determining the ticks until the next message is shown