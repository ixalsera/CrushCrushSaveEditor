#!/usr/bin/env python3
"""Generate a blank (zero-progress, no-unlocks) decoded JSON save from a template.

Usage:
    blank_save.py <steam|nutaku|switch> [output.json]
    (default output: decoded/crushcrush.<platform>.blank.json)
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLATFORMS = ("steam", "nutaku", "switch")

# Every JSON field name crushed.schema.json ever types as `$ref: timestamp`,
# not just the ones currently null in the templates,
# so a template later hand-edited to null out e.g. LoginDate is still
# handled without touching this file again.
TIMESTAMP_KEYS = {"Date", "DateUTC", "LoginDate", "Created", "Start"}


def patch_timestamps(node, now_iso):
    """Recursively replace any {key in TIMESTAMP_KEYS: null} with now_iso,
    in place. Everything else (including non-null timestamp-named values
    like Flings.<id>.Date == "never", and Flings.<id>.Progress == null,
    which is not a timestamp field at all) passes through untouched."""
    if isinstance(node, dict):
        for key, value in node.items():
            if key in TIMESTAMP_KEYS and value is None:
                node[key] = now_iso
            else:
                patch_timestamps(value, now_iso)
    elif isinstance(node, list):
        for item in node:
            patch_timestamps(item, now_iso)


def main():
    args = sys.argv[1:]
    if not args or args[0] not in PLATFORMS:
        print(__doc__)
        sys.exit(1)
    platform, rest = args[0], args[1:]
    output_path = ROOT / (rest[0] if rest else f"decoded/crushcrush.{platform}.blank.json")

    template_path = ROOT / "templates" / f"{platform}.json"
    data = json.loads(template_path.read_text())

    now_iso = datetime.now(timezone.utc).replace(tzinfo=None).isoformat()
    patch_timestamps(data, now_iso)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    out_text = json.dumps(data, indent=2, sort_keys=True)
    output_path.write_text(out_text)
    print(f"{template_path} -> {output_path} ({len(out_text)} bytes)")


if __name__ == "__main__":
    main()
