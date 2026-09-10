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

The Nintendo Switch version uses a different container for the same
plaintext/compression: a raw 4-byte little-endian header (only value observed
so far: 1, meaning unconfirmed) followed by MAGIC and the lzf-compressed body
base64-encoded *separately* rather than as one combined blob -- MAGIC's own
base64 encoding happens to render as the ASCII text "lzfc" (3 bytes divides
evenly into base64's 4-char groups, so no padding). decode_bytes already
handles Switch saves as-is: base64.b64decode() silently drops the leading
non-base64 header bytes, and decoding "lzfc" alone reproduces MAGIC exactly.
Only encode needs a separate path (--nintendo), since PC's encode wraps
everything in one base64 call and has no room for that leading header.

decode/encode's CLI produces/consumes structured JSON (see tools/save_schema.py)
rather than the raw flat plaintext -- timestamps, bitmasks, and blobs are all
converted to human-editable JSON shapes, and Girl/Job/Hobby/Fling/Achievement/
Event data is grouped into dedicated objects. encode(nintendo=...) picks the
target platform independently of where the JSON originated, dropping/defaulting
platform-specific fields as needed. decode_bytes/encode_bytes/decode_file/
encode_file below remain a lower-level flat-text API (used by tools/blank_save.py,
scripts/diff_saves.py, and verification tooling), unaffected by any of this.

Usage:
    crushcrush_save.py decode <in.sav> [out.json]
    crushcrush_save.py encode <in.json> [out.sav] [--nintendo]
"""
import json
import struct
import sys
import base64
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "utils"))
import lzf

sys.path.insert(0, str(Path(__file__).resolve().parent))
import save_schema

MAGIC = bytes.fromhex("9737dc")
NINTENDO_HEADER = struct.pack("<I", 1)
NINTENDO_MAGIC = base64.b64encode(MAGIC)

# Published alongside crushed.schema.json at the repo root -- raw.githubusercontent.com
# serves the actual JSON content (github.com's own URL is an HTML page, not usable as
# a $schema value). Points at `main`, not a pinned commit, so it tracks schema edits.
SCHEMA_URL = "https://raw.githubusercontent.com/ixalsera/CrushCrushSaveEditor/main/crushed.schema.json"


def decode_bytes(raw_b64_text):
    decoded = base64.b64decode(raw_b64_text.strip())
    if decoded[:3] != MAGIC:
        raise ValueError(f"unexpected header {decoded[:3].hex()}, expected {MAGIC.hex()}")
    return lzf.decompress(decoded[3:])


def encode_bytes(plaintext_bytes, nintendo=False):
    compressed = lzf.compress(plaintext_bytes)
    if nintendo:
        return NINTENDO_HEADER + NINTENDO_MAGIC + base64.b64encode(compressed)
    return base64.b64encode(MAGIC + compressed)


def decode_file(in_path, out_path=None):
    raw = Path(in_path).read_text()
    plain = decode_bytes(raw)
    text = plain.decode("utf-8")
    if out_path:
        Path(out_path).write_text(text)
    return text


def encode_file(in_path, out_path=None, nintendo=False):
    text = Path(in_path).read_text()
    b64 = encode_bytes(text.encode("utf-8"), nintendo=nintendo)
    if out_path:
        Path(out_path).write_bytes(b64)
    return b64


def main():
    args = sys.argv[1:]
    nintendo = "--nintendo" in args
    if nintendo:
        args = [a for a in args if a != "--nintendo"]
    if len(args) < 2:
        print(__doc__)
        sys.exit(1)
    mode, in_path = args[0], args[1]
    out_path = args[2] if len(args) > 2 else None
    if mode == "decode":
        text = decode_bytes(Path(in_path).read_text()).decode("utf-8")
        data = save_schema.decode_save_text(text)
        if out_path:
            # Editor IntelliSense hint, not save data -- crushed.schema.json
            # explicitly allows this key and encode_save_text ignores it.
            data["$schema"] = SCHEMA_URL
        out = json.dumps(data, indent=2, sort_keys=True)
        if out_path:
            Path(out_path).write_text(out)
        else:
            sys.stdout.write(out)
    elif mode == "encode":
        data = json.loads(Path(in_path).read_text())
        text = save_schema.encode_save_text(data, nintendo=nintendo)
        b64 = encode_bytes(text.encode("utf-8"), nintendo=nintendo)
        if out_path:
            Path(out_path).write_bytes(b64)
        else:
            sys.stdout.buffer.write(b64)
    else:
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
