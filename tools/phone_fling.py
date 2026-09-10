#!/usr/bin/env python3
"""Decode a C<N>P Phone Fling conversation-state blob into its known and
still-unknown constituent parts (see FLINGS.md).

Byte layout:

    offset 0, u16  message_counter          the conversation/message counter
    offset 2, u16  unknown_1                unconfirmed; maybe a
                                             sent-only counter, needs more data
    offset 4, u32  next_message_countdown   ticks/seconds until the next
                                             message is shown
    offset 8, ...  trailing                 unparsed, variable length; possibly a
                                             conversation-choice bitmask
                                             and/or an unlocked photos indicator

Usage:
    phone_fling.py decode <base64> [<value>]

The blob/value arguments accept either the bare value or a full
"C<N>P:<blob>" / "C<N>D:<value>" line copy-pasted straight out of a
decoded save.
"""
import base64
import re
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "utils"))
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


def encode_conversation_state(state):
    """Inverse of decode_conversation_state: pack a state dict (same shape
    as decode_conversation_state's return value -- trailing as raw bytes,
    not hex) back into the raw C<N>P blob bytes. state=None -> b'' (empty
    blob, matching the never-started convention)."""
    if state is None:
        return b""
    return (
        struct.pack("<HH", state["message_counter"], state["unknown_1"])
        + struct.pack("<I", state["next_message_countdown"])
        + bytes(state["trailing"])
    )


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
