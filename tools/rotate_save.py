#!/usr/bin/env python3
"""Rotate the current save + its decoded dump into *.prev.* before a new
play session, so the next decode can be diffed against what's "prev" now
(see AGENTS.md's "Investigating an unconfirmed field" note).

Moves:
    saves/<name>.sav   -> saves/<name>.prev.sav
    decoded/<name>.txt -> decoded/<name>.prev.txt

Refuses to rotate at all (rather than rotating one file and not the other)
if either source file is missing.

Usage:
    rotate_save.py [name]   (default: crushcrush)
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def rotate(name="crushcrush"):
    """Rotate saves/<name>.sav and decoded/<name>.txt to their .prev.
    counterparts, overwriting any existing .prev. files. Returns the list
    of (src, dst) pairs actually moved."""
    pairs = [
        (ROOT / "saves" / f"{name}.sav", ROOT / "saves" / f"{name}.prev.sav"),
        (ROOT / "decoded" / f"{name}.txt", ROOT / "decoded" / f"{name}.prev.txt"),
    ]
    missing = [str(src) for src, _ in pairs if not src.exists()]
    if missing:
        raise FileNotFoundError(f"missing, nothing rotated: {', '.join(missing)}")
    for src, dst in pairs:
        src.replace(dst)
    return pairs


def main():
    name = sys.argv[1] if len(sys.argv) > 1 else "crushcrush"
    for src, dst in rotate(name):
        print(f"{src} -> {dst}")


if __name__ == "__main__":
    main()
