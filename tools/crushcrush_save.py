#!/usr/bin/env python3
"""Decode/encode Crush Crush .sav files.

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
