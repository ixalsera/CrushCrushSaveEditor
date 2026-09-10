#!/usr/bin/env python3
"""Decodes a base64 `blob` in to a bitmask or pipe-delimited text, or
compares two blobs against one another.

Usage:
  python3 decode_blob.py bits <base64>                decoded bit indices set, and count
  python3 decode_blob.py text <base64>                decoded pipe-delimited text
  python3 decode_blob.py diff-bits <base64_a> <base64_b>   bits added/removed, a -> b
  python3 decode_blob.py diff-text <base64_a> <base64_b>   pipe items added/removed, a -> b
"""
import base64
import sys


def bits(b64):
    data = base64.b64decode(b64) if b64 else b""
    n = int.from_bytes(data, "little")
    return sorted(i for i in range(n.bit_length()) if n & (1 << i))


def text(b64):
    return base64.b64decode(b64).decode() if b64 else ""


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    mode = sys.argv[1]
    args = sys.argv[2:]

    if mode == "bits":
        b = bits(args[0])
        print("bits set:", b)
        print("count:", len(b))
    elif mode == "text":
        print(text(args[0]))
    elif mode == "diff-bits":
        a, b = set(bits(args[0])), set(bits(args[1]))
        print("added:", sorted(b - a))
        print("removed:", sorted(a - b))
    elif mode == "diff-text":
        a = set(text(args[0]).split("|"))
        b = set(text(args[1]).split("|"))
        print("added:", sorted(b - a))
        print("removed:", sorted(a - b))
    else:
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
