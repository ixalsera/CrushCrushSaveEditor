#!/usr/bin/env python3
"""Decode/encode Crush Crush .sav files.

File format (reverse-engineered from saves/*.sav):
    ASCII text file (no trailing newline) containing:
        base64( MAGIC + lzf_compress(plaintext_save_data) )
    where MAGIC is the fixed 3-byte sequence 97 37 dc (identical across every
    save observed so far -- a format marker, not a length or checksum).

The plaintext_save_data is itself a flat, newline-delimited list of
"key:value" style entries, with bare "::" lines acting as section
separators/prefix resets (keys after a "::<Name>" line are logically
prefixed by <Name> until the next "::").

Usage:
    crushcrush_save.py decode <in.sav> [out.txt]
    crushcrush_save.py encode <in.txt> [out.sav]
"""
import sys
import base64
from pathlib import Path

import lzf

MAGIC = bytes.fromhex("9737dc")


def decode_bytes(raw_b64_text):
    decoded = base64.b64decode(raw_b64_text.strip())
    if decoded[:3] != MAGIC:
        raise ValueError(f"unexpected header {decoded[:3].hex()}, expected {MAGIC.hex()}")
    return lzf.decompress(decoded[3:])


def encode_bytes(plaintext_bytes):
    compressed = MAGIC + lzf.compress(plaintext_bytes)
    return base64.b64encode(compressed)


def decode_file(in_path, out_path=None):
    raw = Path(in_path).read_text()
    plain = decode_bytes(raw)
    text = plain.decode("utf-8")
    if out_path:
        Path(out_path).write_text(text)
    return text


def encode_file(in_path, out_path=None):
    text = Path(in_path).read_text()
    b64 = encode_bytes(text.encode("utf-8"))
    if out_path:
        Path(out_path).write_bytes(b64)
    return b64


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    mode, in_path = sys.argv[1], sys.argv[2]
    out_path = sys.argv[3] if len(sys.argv) > 3 else None
    if mode == "decode":
        text = decode_file(in_path, out_path)
        if not out_path:
            sys.stdout.write(text)
    elif mode == "encode":
        b64 = encode_file(in_path, out_path)
        if not out_path:
            sys.stdout.buffer.write(b64)
    else:
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
