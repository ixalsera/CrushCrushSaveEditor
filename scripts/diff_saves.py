#!/usr/bin/env python3
"""Flatten a decoded save's structured JSON into "dotted.path: value" pairs
and either dump one file's pairs or diff two snapshots by path.

A plain `diff` on two decoded JSON files is noisy - dict key order isn't
guaranteed stable and nesting hides which specific leaf actually changed.
This flattens every nested object/array into a single-line path first (e.g.
`Girls.Cassie.Clothing.29`), so the diff reflects actual state changes, not
structural reshuffling.

CLI:
  python3 scripts/diff_saves.py <file.json>            dump flattened pairs, sorted
  python3 scripts/diff_saves.py <prev.json> <cur.json>  diff two snapshots (added/removed/changed)
"""
import json
import sys


def reconstruct(path):
    """Undo the *raw* save format's `::` prefix compression (see CLAUDE.md's
    "Plaintext save structure") into flat {key: raw_value_text} pairs, keyed
    by the save's own internal names (e.g. "GirlCassieHearts") - NOT the
    JSON schema below. Kept for scripts/parse_prefs.py, which cross-checks
    against Unity's `prefs` file; that file is written by the same raw
    key names as the save itself, so this needs to stay text-based rather
    than becoming JSON-flavored too. `path` is a flat decode as produced by
    `tools.crushcrush_save.decode_file`/`decode_bytes` (not this project's
    `crushcrush_save.py decode` CLI, which now writes JSON - see CLAUDE.md's
    "JSON schema" section for why the two diverged)."""
    entries = {}
    prefix = ""
    with open(path) as f:
        for line in f:
            line = line.rstrip("\n")
            if line.startswith("::"):
                prefix = line[2:]
                continue
            if not line:
                continue
            if ":" in line:
                key, val = line.split(":", 1)
            else:
                key, val = line, ""
            entries[prefix + key] = val
    return entries


def load_json(path):
    with open(path) as f:
        data = json.load(f)
    data.pop("$schema", None)  # editor IntelliSense hint, not save data
    return data


def flatten(obj, prefix=""):
    """Recursively flatten a JSON-compatible value into {path: leaf} pairs.
    Dict keys join with "."; list indices join with "[i]". An empty
    dict/list is kept as its own leaf (rather than vanishing silently) so a
    present-but-empty container (e.g. `Achievement: {}`) is still visible."""
    if isinstance(obj, dict):
        if not obj and prefix:
            return {prefix: obj}
        items = {}
        for key, value in obj.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            items.update(flatten(value, path))
        return items
    if isinstance(obj, list):
        if not obj and prefix:
            return {prefix: obj}
        items = {}
        for i, value in enumerate(obj):
            items.update(flatten(value, f"{prefix}[{i}]"))
        return items
    return {prefix: obj}


def dump(path):
    entries = flatten(load_json(path))
    for k in sorted(entries):
        print(f"{k}: {json.dumps(entries[k])}")


def diff(prev_path, cur_path):
    prev = flatten(load_json(prev_path))
    cur = flatten(load_json(cur_path))

    prev_keys = set(prev)
    cur_keys = set(cur)

    added = sorted(cur_keys - prev_keys)
    removed = sorted(prev_keys - cur_keys)
    common = prev_keys & cur_keys
    changed = sorted(k for k in common if prev[k] != cur[k])

    print(f"# Added ({len(added)})")
    for k in added:
        print(f"+ {k}: {json.dumps(cur[k])}")
    print()
    print(f"# Removed ({len(removed)})")
    for k in removed:
        print(f"- {k}: {json.dumps(prev[k])}")
    print()
    print(f"# Changed ({len(changed)})")
    for k in changed:
        print(f"~ {k}: {json.dumps(prev[k])} -> {json.dumps(cur[k])}")


def main():
    if len(sys.argv) == 2:
        dump(sys.argv[1])
    elif len(sys.argv) == 3:
        diff(sys.argv[1], sys.argv[2])
    else:
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
