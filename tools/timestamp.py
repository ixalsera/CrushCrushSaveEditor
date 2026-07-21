#!/usr/bin/env python3
"""Decode/encode the .NET DateTime.ToBinary() timestamps used throughout
Crush Crush saves (GameState.Date, DateUTC, LoginDate, Task<N>Start, C<N>D,
etc. -- see AGENTS.md's "Timestamp fields" section for the format).

Given the raw 64-bit value stored in the save:
    bit 63 set -> DateTimeKind.Local
    bit 62 set -> DateTimeKind.Utc
    neither    -> DateTimeKind.Unspecified (e.g. Task<N>Start)
    ticks (with the kind tag bit masked off) are 100ns units since 0001-01-01
    int64.MaxValue (9223372036854775807) is the "N/A"/unset sentinel
    0 means "never"

Usage:
    timestamp.py decode <value> [value ...]
    timestamp.py encode <iso-datetime> [local|utc|unspecified]   (default: utc)
"""
import sys
from datetime import datetime, timedelta

EPOCH = datetime(1, 1, 1)
LOCAL_BIT = 0x8000000000000000
UTC_BIT = 0x4000000000000000
MASK64 = 0xFFFFFFFFFFFFFFFF
MAX_SENTINEL = 9223372036854775807


def decode(value):
    """Return (kind, datetime | None) for a raw save timestamp value.

    kind is "N/A" or "never" (with datetime None) for the two sentinel
    values instead of one of the three real DateTimeKind names.
    """
    unsigned = value & MASK64
    if unsigned == MAX_SENTINEL:
        return "N/A", None
    if unsigned == 0:
        return "never", None
    if unsigned & LOCAL_BIT:
        ticks = unsigned - LOCAL_BIT
        kind = "Local"
    elif unsigned & UTC_BIT:
        ticks = unsigned - UTC_BIT
        kind = "Utc"
    else:
        ticks = unsigned
        kind = "Unspecified"
    dt = EPOCH + timedelta(seconds=ticks // 10_000_000, microseconds=(ticks % 10_000_000) // 10)
    return kind, dt


def encode(dt, kind="utc"):
    """Return the signed int64 save value for a datetime tagged with kind."""
    delta = dt - EPOCH
    # exact integer tick count -- delta.total_seconds() is a float and loses
    # sub-second precision at this magnitude (~6e17 ticks since year 1)
    ticks = delta.days * 86400 * 10_000_000 + delta.seconds * 10_000_000 + delta.microseconds * 10
    kind = kind.lower()
    if kind == "local":
        value = ticks + LOCAL_BIT
    elif kind == "utc":
        value = ticks + UTC_BIT
    elif kind == "unspecified":
        value = ticks
    else:
        raise ValueError(f"unknown kind {kind!r}, expected local/utc/unspecified")
    if value >= 0x8000000000000000:
        value -= 0x10000000000000000
    return value


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    mode = sys.argv[1]
    if mode == "decode":
        for raw in sys.argv[2:]:
            kind, dt = decode(int(raw))
            print(f"{raw} -> {kind}" if dt is None else f"{raw} -> {kind}: {dt.isoformat()}")
    elif mode == "encode":
        dt = datetime.fromisoformat(sys.argv[2])
        kind = sys.argv[3] if len(sys.argv) > 3 else "utc"
        print(encode(dt, kind))
    else:
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
