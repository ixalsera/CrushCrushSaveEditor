#!/usr/bin/env python3
"""Rotates a save file

Moves:
    saves/<name>.sav    -> saves/<name>.prev.sav
    decoded/<name>.json -> decoded/<name>.prev.json

Refuses to rotate at all (rather than rotating one file and not the other)
if either source file is missing.

Usage:
    rotate_save.py [name]   (default: crushcrush)
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def rotate(name="crushcrush"):
    """Rotate saves/<name>.sav and decoded/<name>.json to their .prev.
    counterparts, overwriting any existing .prev. files. Returns the list
    of (src, dst) pairs actually moved, or None if either source file is
    missing (nothing is rotated in that case)."""
    pairs = [
        (ROOT / "saves" / f"{name}.sav", ROOT / "saves" / f"{name}.prev.sav"),
        (ROOT / "decoded" / f"{name}.json", ROOT / "decoded" / f"{name}.prev.json"),
    ]
    if any(not src.exists() for src, _ in pairs):
        return None
    for src, dst in pairs:
        src.replace(dst)
    return pairs


def main():
    name = sys.argv[1] if len(sys.argv) > 1 else "crushcrush"
    result = rotate(name)
    if result is None:
        print(f"No save/decoded save available to rotate for {name!r} - nothing done.")
        return
    for src, dst in result:
        print(f"{src} -> {dst}")


if __name__ == "__main__":
    main()
