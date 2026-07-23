#!/usr/bin/env python3
"""Generate a zero-progress, no-unlocks decoded save from a real save used
as a structural template. A save file has a *lot* of repeating, precisely-
shaped sections (84 Girls, 20 Jobs, 12 Hobbies, 12 Skills, 42 Tasks, 46
Phone Flings...) - reproducing that structure from the schema docs by hand
risks silently dropping or misnaming an entry. Transforming a real,
known-good decode preserves the exact key set and `::` prefix/suffix
structure (see AGENTS.md) while rewriting every value to its zero/locked
state.

This is a best-effort reconstruction against the documented+observed schema
(SCHEMA.md/FLINGS.md/EVENTS.md/AGENTS.md), NOT something verified by
actually loading it in-game. Fields SCHEMA.md marks unconfirmed are handled
with the most conservative reading available; see the module-level RULES
comments for the specific call made on each.

Usage:
    blank_save.py [template.txt] [output.txt]
    (defaults: decoded/crushcrush.prev.txt -> decoded/crushcrush.blank.txt)
"""
import base64
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "utils"))
import timestamp

ROOT = Path(__file__).resolve().parent.parent


def parse_segments(text):
    """Split the flat decoded text into (prefix, [lines]) segments exactly
    as the `::` rules describe - a bare `::` starts a prefix-less segment
    whose single following line is a self-contained key:value; a `::Name`
    starts a segment whose following lines are suffixes of Name."""
    segments = []
    prefix = None
    lines = text.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]
        if line == "::":
            prefix = ""
            segments.append([prefix, []])
        elif line.startswith("::"):
            prefix = line[2:]
            segments.append([prefix, []])
        else:
            if not segments:
                raise ValueError(f"content line before any :: header: {line!r}")
            segments[-1][1].append(line)
        i += 1
    return segments


def render_segments(segments):
    out = []
    for prefix, lines in segments:
        out.append(f"::{prefix}")
        out.extend(lines)
    return "\n".join(out)


def b64_zeros(n):
    return base64.b64encode(bytes(n)).decode()


def zero_flag_lines(lines, key_prefixes_to_zero, keys_to_drop):
    """For a Job/Hobby-style segment: keep only the listed numeric/keys at
    their zero value, drop flag-only lines entirely."""
    kept = []
    for line in lines:
        key = line.split(":", 1)[0]
        if key in keys_to_drop:
            continue
        kept.append(line)
    return kept


def blank_out(template_text, now):
    segments = parse_segments(template_text)

    now_utc = now.astimezone(timezone.utc).replace(tzinfo=None)
    date_val = timestamp.encode(now_utc, "local")
    dateutc_val = timestamp.encode(now_utc, "utc")

    result = []
    for prefix, lines in segments:
        if prefix == "ACH":
            continue  # AchievementCount:0 -> no achievement entries
        if prefix == "Task":
            # confirmed: a fresh account has NO Task entries at all until it
            # opens an LTE - tasks aren't a fixed 0-41 preallocation, they
            # only exist for events the player has actually entered
            continue
        if prefix == "Skill":
            new_lines = [f"{n}:0i" for n in range(12)]
            new_lines += ["Hair:0i", "Plushy:0i"]
            result.append([prefix, new_lines])
            continue
        if prefix == "Completed":
            new_lines = []
            for line in lines:
                key = line.split(":", 1)[0]
                if key == "Events":
                    new_lines.append(f"Events:{b64_zeros(15)}")
                elif key in ("2018Events", "2019Events", "2020Events"):
                    new_lines.append(f"{key}:0")
                else:
                    new_lines.append(line)
            result.append([prefix, new_lines])
            continue
        if prefix == "Playfab":
            new_lines = []
            for line in lines:
                key = line.split(":", 1)[0]
                if key == "FlingPurchases":
                    new_lines.append("FlingPurchases:0")
                elif key == "Inventory":
                    new_lines.append("Inventory:0i")
                elif key == "Participation":
                    new_lines.append(f"Participation:{b64_zeros(7)}")
                else:
                    new_lines.append(line)
            result.append([prefix, new_lines])
            continue
        if prefix == "Settings":
            new_lines = []
            for line in lines:
                key = line.split(":", 1)[0]
                if key == "DisableCloud":
                    continue  # re-added unconditionally below
                if key in ("Effects", "Music", "Voice"):
                    new_lines.append(f"{key}:1f")
                else:
                    new_lines.append(line)
            new_lines.insert(1 if new_lines else 0, "DisableCloud")
            result.append([prefix, new_lines])
            continue
        if prefix == "GameState":
            new_lines = []
            for line in lines:
                key = line.split(":", 1)[0]
                if key == "Date":
                    new_lines.append(f"Date:{date_val}")
                elif key == "DateUTC":
                    new_lines.append(f"DateUTC:{dateutc_val}")
                elif key == "LoginDate":
                    new_lines.append(f"LoginDate:{dateutc_val}")
                elif key == "DateCount":
                    new_lines.append("DateCount:0i")
                elif key == "Diamonds":
                    new_lines.append("Diamonds:0")
                elif key == "GiftCount":
                    new_lines.append("GiftCount:0i")
                elif key == "HeartCount":
                    new_lines.append("HeartCount:0")
                elif key == "Ids":
                    continue  # player/machine ID for cloud sync - drop, don't sync blanked state
                elif key == "Money":
                    new_lines.append("Money:0")
                elif key == "NSFW":
                    continue  # default off
                elif key == "PendingMultiplier":
                    new_lines.append("PendingMultiplier:0f")
                elif key == "PokeCount":
                    new_lines.append("PokeCount:0i")
                elif key == "Seconds":
                    new_lines.append("Seconds:0f")
                elif key == "TotalIncome":
                    new_lines.append("TotalIncome:0")
                elif key == "TotalTime":
                    new_lines.append("TotalTime:0i")
                else:
                    new_lines.append(line)  # Build, Hobbies, PurchasedMultiplier
            result.append([prefix, new_lines])
            continue
        if prefix.startswith("Girl"):
            # every girl resets to a bare Hearts:0, dropping Love/LifeDates/
            # LifeOutfits/Clothing/GiftCount<N>/DateCount<N>/Dates
            result.append([prefix, ["Hearts:0"]])
            continue
        if prefix.startswith("Hobby"):
            new_lines = ["Time:0f", "TimeL:0"]
            result.append([prefix, new_lines])
            continue
        if prefix.startswith("Job"):
            # JobMECH/JobUNKNOWN use bare root-level keys, not a block;
            # both forms funnel through here since prefix.startswith("Job")
            # covers "JobART" (block) as well as "" (bare, see below)
            new_lines = ["Experience:0", "Time:0f"]
            result.append([prefix, new_lines])
            continue
        if prefix == "":
            new_lines = []
            job_bare_experience = re.compile(r"^Job([A-Z]+)(Experience|Time)")
            girl_bare = re.compile(
                r"^Girl([A-Za-z]+?)(Hearts|Love|LifeDates|LifeOutfits|Clothing|GiftCount\d*|DateCount\d*|Dates)$"
            )
            for line in lines:
                key = line.split(":", 1)[0]
                if re.match(r"^[Pp]es\d", key):
                    continue  # no LTE ever opened (covers pes27Foo and Pes27Start alike)
                m = job_bare_experience.match(key)
                if m:
                    base, field = m.groups()
                    if field == "Experience":
                        new_lines.append(f"Job{base}Experience:0")
                    else:
                        new_lines.append(f"Job{base}Time:0f")
                    continue
                if re.match(r"^Job[A-Z]+(Active|Gilded|Level|Locked)$", key):
                    continue  # dropped: untouched job has no flags
                gm = girl_bare.match(key)
                if gm and key not in ("GirlsUnlocked", "GirlsPreviouslyUnlocked"):
                    if gm.group(2) == "Hearts":
                        new_lines.append(f"{key}:0")
                    # else: Love/LifeDates/LifeOutfits/Clothing/GiftCount<N>/
                    # DateCount<N>/Dates all dropped - locked girls carry
                    # only a bare Hearts:0, see SCHEMA.md's Girl schema notes
                    continue
                if re.match(r"^\.(speedboost|timeblocks|timeskip)\.", key):
                    continue  # shop tables - let the game recreate these on load
                elif key == "AvailableJobs":
                    new_lines.append("AvailableJobs:0i")
                elif key in ("AchievementCount",):
                    new_lines.append("AchievementCount:0i")
                elif key in ("ana.ev", "ana.vid", "dchk"):
                    new_lines.append(f"{key}:0")
                elif key == "BlayfapAwardedItems":
                    new_lines.append("BlayfapAwardedItems:")
                elif re.match(r"^C\d+D$", key):
                    new_lines.append(f"{key}:0")
                elif re.match(r"^C\d+P$", key):
                    new_lines.append(f"{key}:")
                elif key == "CurrentGirl":
                    new_lines.append("CurrentGirl:0i")
                elif key == "GirlsPreviouslyUnlocked":
                    new_lines.append(f"GirlsPreviouslyUnlocked:{b64_zeros(11)}")
                elif key == "GirlsUnlocked":
                    new_lines.append(f"GirlsUnlocked:{b64_zeros(11)}")
                elif key == "HasSeenFuzzyExternalPurchaseConfirmation":
                    continue
                elif re.match(r"^Event\d+Tokens$", key) or key == "EventID":
                    continue
                elif re.match(r"^LastPesId\d$", key):
                    continue
                elif key == "Prereg":
                    continue
                elif key == "ticketboothSeen":
                    continue
                elif key == "TermsVersionAccepted":
                    continue
                elif key == "TimeMultiplier":
                    new_lines.append("TimeMultiplier:1f")
                elif key == "Tutorial":
                    new_lines.append("Tutorial:0i")
                elif key == "UnlockedPFS":
                    new_lines.append(f"UnlockedPFS:{b64_zeros(3)}")
                elif key == "events.popupinfo":
                    new_lines.append("events.popupinfo:{}")
                else:
                    new_lines.append(line)  # SaveFileVersion: kept as-is, see docstring
            result.append([prefix, new_lines])
            continue
        # anything unrecognised: pass through unchanged rather than silently
        # dropping data we didn't anticipate
        result.append([prefix, lines])

    # A "::" or "::Name" header is only valid grammar if at least one
    # content line follows it (see AGENTS.md's `::` rules) - segments that
    # got filtered down to nothing above must be dropped entirely, not
    # rendered as a bare, content-less "::"
    result = [(p, l) for p, l in result if l]
    return render_segments(result)


def main():
    template_path = ROOT / (sys.argv[1] if len(sys.argv) > 1 else "decoded/crushcrush.prev.txt")
    output_path = ROOT / (sys.argv[2] if len(sys.argv) > 2 else "decoded/crushcrush.blank.txt")
    template_text = template_path.read_text()
    blanked = blank_out(template_text, datetime.now(timezone.utc))
    output_path.write_text(blanked)
    print(f"{template_path} -> {output_path} ({len(blanked)} bytes)")


if __name__ == "__main__":
    main()
