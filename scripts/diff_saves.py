#!/usr/bin/env python3
"""Reconstruct full key:value pairs from the prefix-compressed decoded save
text (undoing the `::` section compression - see AGENTS.md) and either dump
one file's reconstructed pairs or diff two snapshots as key sets.

A plain `diff` on the raw decoded text is noisy because the `::`
prefix-compression reshuffles line order between saves - this reconstructs
the logical `key:value` pairs first, so the diff reflects actual state
changes rather than reordering.

CLI:
  python3 scripts/diff_saves.py <file.txt>              dump reconstructed pairs, sorted
  python3 scripts/diff_saves.py <prev.txt> <cur.txt>     diff two snapshots (added/removed/changed)
"""
import sys


def reconstruct(path):
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


def dump(path):
    entries = reconstruct(path)
    for k in sorted(entries):
        print(f"{k}:{entries[k]}")


def diff(prev_path, cur_path):
    prev = reconstruct(prev_path)
    cur = reconstruct(cur_path)

    prev_keys = set(prev)
    cur_keys = set(cur)

    added = sorted(cur_keys - prev_keys)
    removed = sorted(prev_keys - cur_keys)
    common = prev_keys & cur_keys
    changed = sorted(k for k in common if prev[k] != cur[k])

    print(f"# Added ({len(added)})")
    for k in added:
        print(f"+ {k}:{cur[k]}")
    print()
    print(f"# Removed ({len(removed)})")
    for k in removed:
        print(f"- {k}:{prev[k]}")
    print()
    print(f"# Changed ({len(changed)})")
    for k in changed:
        print(f"~ {k}: {prev[k]} -> {cur[k]}")


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
