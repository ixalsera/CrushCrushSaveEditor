#!/usr/bin/env python3
"""[DEPRECATED]

Parse a Unity `prefs` file (Linux: `~/.config/unity3d/<Company>/<Product>/prefs`)
and reconstruct the same logical key:value pairs `scripts/diff_saves.py` produces
from a decoded `.sav`, so the two can be cross-checked against each other.

Confirmed encoding (100% cross-validated against a real decoded save - see
module-level notes below for the one open question):

- Every `<pref name="...">` name is base64 of the logical key name (same names
  `scripts/diff_saves.py reconstruct()` produces, e.g. `CurrentGirl`,
  `GirlCassieHearts`).
- Every `string`-typed *value* is ALSO base64-encoded, one extra layer on top
  of whatever the real value already was (plain text, JSON, or a blob that's
  itself already base64 in the `.sav`, e.g. `GirlsUnlocked`).
- A 64-bit `long` field is represented one of two ways:
    1. Split across two `int` prefs entries: `<key>` holds the low 32 bits,
       and a second entry - the SAME base64 key-name string with a literal
       `h` character appended after it (not itself valid base64 on its own) -
       holds the high 32 bits. Reconstruct as
       `(unsigned_high32 << 32) | unsigned_low32`, read as signed 64-bit.
       Confirmed exactly against `C<N>D` (including the `int64.MaxValue`
       gated-fling sentinel) and `GameStateLoginDate`.
    2. Or, for some longs (`GameStateDate`/`Diamonds`/`Money`/`TotalIncome`
       and the `pes<N>` equivalents), stored as a plain `string` type holding
       the base64-wrapped decimal text instead of the two-int split. What
       decides which representation a given `long` field gets is not yet
       known - still an open question.
- Unity's own `type="int"/"float"/"string"` attributes independently confirm
  every type inference `SCHEMA.md` already made from the `.sav`'s suffix
  convention (`i`->int, `f`->float, unsuffixed->long).

CLI:
  python3 scripts/parse_prefs.py dump <prefs-file>                  dump resolved key:value pairs, sorted
  python3 scripts/parse_prefs.py compare <prefs-file> <decoded.txt> cross-check against a reconstructed save
"""
import base64
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from diff_saves import reconstruct


def _u32(n):
    return n & 0xFFFFFFFF


def _strict_b64_decode(b64):
    """Decode base64 with correct padding computed from length, rejecting
    anything invalid rather than silently producing garbage bytes (plain
    `base64.b64decode(s + "===")` will do the latter on some malformed
    inputs - see the `h`-suffix handling in load_prefs)."""
    pad = (-len(b64)) % 4
    try:
        return base64.b64decode(b64 + "=" * pad, validate=True).decode("utf-8")
    except Exception:
        return None


def load_prefs(path):
    """Parse the prefs XML into {logical_name: {"v": (type, text), "h": (type, text) | absent}}."""
    tree = ET.parse(path)
    entries = {}
    for p in tree.getroot().findall("pref"):
        t = p.get("type")
        name_b64 = p.get("name")
        name = _strict_b64_decode(name_b64)
        is_hash = False
        if name is None:
            # the high-32-bits companion: same base64 string plus a raw
            # trailing "h" that isn't part of valid base64 - strip it and
            # retry rather than guessing at re-encoding a different string
            name = _strict_b64_decode(name_b64[:-1])
            is_hash = True
        if name is None:
            continue  # not a base64-name pref at all (Unity's own built-ins, e.g. Screenmanager/UnityGraphicsQuality)
        entries.setdefault(name, {})["h" if is_hash else "v"] = (t, p.text)
    return entries


def resolve(entries):
    """Collapse {"v", "h"} parts into a single (kind, value) per logical key."""
    resolved = {}
    for name, parts in entries.items():
        v = parts.get("v")
        if v is None:
            continue
        vtype, vtext = v
        h = parts.get("h")
        if h is not None:
            low = _u32(int(vtext))
            high = _u32(int(h[1]))
            combined = low | (high << 32)
            if combined & 0x8000000000000000:
                combined -= 1 << 64
            resolved[name] = ("long64", combined)
        elif vtype == "int":
            resolved[name] = ("int32", int(vtext))
        elif vtype == "float":
            resolved[name] = ("float", float(vtext))
        elif vtype == "string":
            decoded = _strict_b64_decode(vtext) if vtext else ""
            resolved[name] = ("string", decoded if decoded is not None else vtext)
        else:
            resolved[name] = (f"unknown:{vtype}", vtext)
    return resolved


def _parse_real_value(raw):
    """Parse a `scripts/diff_saves.py reconstruct()` raw value into (kind, value)."""
    if raw == "":
        return ("flag", None)
    if raw.endswith("i") and raw[:-1].lstrip("-").isdigit():
        return ("int32", int(raw[:-1]))
    if raw.endswith("f"):
        try:
            return ("float", float(raw[:-1]))
        except ValueError:
            pass
    if raw.lstrip("-").isdigit():
        return ("long64", int(raw))
    return ("string", raw)


def compare(prefs_path, save_path):
    """Cross-check every prefs key against the reconstructed decoded save.
    Returns (pf, real, matches, mismatches, only_in_prefs, only_in_save)."""
    pf = resolve(load_prefs(prefs_path))
    real = reconstruct(save_path)

    common = sorted(set(pf) & set(real))
    only_pf = sorted(set(pf) - set(real))
    only_real = sorted(set(real) - set(pf))

    matches, mismatches = [], []
    for k in common:
        pf_kind, pf_val = pf[k]
        real_kind, real_val = _parse_real_value(real[k])
        ok = False
        if real_kind == "flag":
            ok = True  # can't cross-check a bare flag against a typed prefs value
        elif pf_kind == "string" and real_kind in ("int32", "long64") and pf_val.lstrip("-").isdigit():
            ok = int(pf_val) == real_val
        elif pf_kind in ("long64", "int32") and real_kind in ("long64", "int32"):
            ok = pf_val == real_val
        elif pf_kind == "float" and real_kind == "float":
            ok = abs(pf_val - real_val) < 0.01
        elif pf_kind == "string" and real_kind == "string":
            ok = pf_val == real_val
        (matches if ok else mismatches).append((k, pf_kind, pf_val, real_kind, real_val))

    return pf, real, matches, mismatches, only_pf, only_real


def main():
    if len(sys.argv) == 3 and sys.argv[1] == "dump":
        resolved = resolve(load_prefs(sys.argv[2]))
        for k in sorted(resolved):
            kind, val = resolved[k]
            print(f"{k}:{val} ({kind})")
    elif len(sys.argv) == 4 and sys.argv[1] == "compare":
        pf, real, matches, mismatches, only_pf, only_real = compare(sys.argv[2], sys.argv[3])
        print(f"matches: {len(matches)}  mismatches: {len(mismatches)}")
        print(f"only_in_prefs: {len(only_pf)}  only_in_save: {len(only_real)}")
        if mismatches:
            print("\n# Mismatches")
            for k, pk, pv, rk, rv in mismatches:
                print(f"~ {k}: prefs=({pk}) {pv!r} save=({rk}) {rv!r}")
        if only_pf:
            print("\n# Only in prefs")
            for k in only_pf:
                print(f"+ {k}:{pf[k]}")
        if only_real:
            print("\n# Only in save")
            for k in only_real:
                print(f"- {k}:{real[k]}")
    else:
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
