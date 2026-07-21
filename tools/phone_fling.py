#!/usr/bin/env python3
"""Decode a C<N>P Phone Fling conversation-state blob into its known and
still-unknown constituent parts (see FLINGS.md).

Byte layout, established by diffing C<N>P blobs before/after a play session
across two different flings (see AGENTS.md's fling-diffing note):

    offset 0, u16  message_counter          the conversation/message counter
                                             confirmed by FLINGS.md; whether
                                             it's specifically sent+received
                                             combined is a one-data-point
                                             hypothesis, NOT yet confirmed
    offset 2, u16  unknown_1                unconfirmed; moved +1 in the one
                                             sample seen with exactly 1
                                             player-sent message -- maybe a
                                             sent-only counter, needs more data
    offset 4, u32  next_message_countdown   ticks/seconds until the next
                                             message is shown (FLINGS.md:
                                             "likely"); observed counting
                                             down towards single digits
    offset 8, ...  trailing                 unparsed, variable length (2
                                             bytes on one fling, 3 on
                                             another) -- FLINGS.md guesses a
                                             conversation-choice bitmask
                                             and/or a seen-photos indicator

This field order matches the `PhoneFlingData` pseudocode in FLINGS.md
(updated to agree with this module after an earlier version of FLINGS.md
placed the u32 immediately after the counter with no second u16 in
between -- that order made next_message_countdown a large 6-digit number
that never collapsed to single digits, and its fixed 10-byte size couldn't
fit the 11-byte blob observed on fling 7 at all).

Two more things fell out of running this over every C<N>P in a real save
(not just the two flings manually diffed so far), included here so nobody
has to rediscover them:

  - A C<N>P blob is simply empty/absent whenever the paired C<N>D is the
    "never started" sentinel (0). Treated here as its own state rather
    than an 8-byte-minimum parse error.
  - next_message_countdown reads as exactly 4294967292 (0xFFFFFFFC, i.e.
    -4 as a signed i32) on every fling whose C<N>D is the "needs an
    unlock requirement" sentinel (int64.max) -- but *also* on several
    flings with a perfectly ordinary, real C<N>D. So this looks like an
    independent "conversation currently gated / no countdown running"
    flag living on the P blob itself, not merely a mirror of D's
    sentinel. Unconfirmed why an active-looking fling would carry it -
    flag for a human, don't silently treat those flings as "locked".

Usage:
    phone_fling.py decode <C<N>P-blob-base64> [<C<N>D-value>]

The blob/value arguments accept either the bare value or a full
"C<N>P:<blob>" / "C<N>D:<value>" line copy-pasted straight out of a
decoded save.
"""
import base64
import re
import struct
import sys

import timestamp

_KEY_PREFIX_RE = re.compile(r"^C\d+[DP]:")
COUNTDOWN_LOCKED_SENTINEL = 0xFFFFFFFC  # 4294967292 / -4 as signed i32


def _strip_key_prefix(value):
    return _KEY_PREFIX_RE.sub("", value.strip())


def decode_conversation_state(blob_b64):
    """Decode a C<N>P blob. Returns every field, known or not, as a dict,
    or None if the blob is empty (fling never started -- pair this with a
    C<N>D of 0 to confirm)."""
    raw = base64.b64decode(_strip_key_prefix(blob_b64))
    if len(raw) == 0:
        return None
    if len(raw) < 8:
        raise ValueError(f"blob too short ({len(raw)} bytes), expected at least 8")
    message_counter, unknown_1 = struct.unpack_from("<HH", raw, 0)
    next_message_countdown = struct.unpack_from("<I", raw, 4)[0]
    return {
        "message_counter": message_counter,
        "unknown_1": unknown_1,
        "next_message_countdown": next_message_countdown,
        "trailing": raw[8:],
    }


def format_state(state, cd_value=None):
    lines = []
    if cd_value is not None:
        kind, dt = timestamp.decode(int(_strip_key_prefix(cd_value)))
        last_msg = kind if dt is None else f"{kind}: {dt.isoformat()}"
        lines.append(f"last_message_time (C<N>D):      {last_msg}")
    if state is None:
        lines.append("blob is empty -- fling not yet started")
        return "\n".join(lines)
    countdown = state["next_message_countdown"]
    countdown_str = str(countdown)
    if countdown == COUNTDOWN_LOCKED_SENTINEL:
        countdown_str += " (locked/gated sentinel, not a real countdown)"
    lines += [
        f"message_counter (u16 @0):        {state['message_counter']}",
        f"unknown_1 (u16 @2):              {state['unknown_1']}",
        f"next_message_countdown (u32 @4): {countdown_str}",
        f"trailing (unparsed, {len(state['trailing'])} bytes):  {state['trailing'].hex()}",
    ]
    return "\n".join(lines)


def main():
    if len(sys.argv) < 3 or sys.argv[1] != "decode":
        print(__doc__)
        sys.exit(1)
    blob = sys.argv[2]
    cd_value = sys.argv[3] if len(sys.argv) > 3 else None
    state = decode_conversation_state(blob)
    print(format_state(state, cd_value))


if __name__ == "__main__":
    main()
