#!/usr/bin/env python3
"""Generate a zero-progress, no-unlocks decoded JSON save.

Two modes:

- Template mode (a template JSON path is given): transforms a real decode
  into a zero-progress/no-unlocks one, keyed off the template's own key set.
- Bare mode (no template given): there's no roster to draw from, so this
  builds the smallest coherent blank instead - GameState/Settings/Skill/
  Player/Playfab populated from tools/save_schema.py's own field tables.

This is a best-effort reconstruction against the observed schema, NOT something verified
by actually loading it in-game. Fields the docs mark unconfirmed are
handled with the most conservative reading available; see the RULES tables
for the specific call made on each.

Usage:
    blank_save.py [--bare | template.json] [output.json]
    (bare mode with no output.json: decoded/crushcrush.blank.json)
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import crushcrush_save  # noqa: E402
import save_schema  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent

_KEEP = object()  # template mode: pass the field through unchanged; bare mode: generic per-kind zero
_DROP = None  # both modes: omit the field entirely


def _generic_zero(spec):
    if spec.kind == "flag":
        return False
    if spec.kind in ("int", "long"):
        return 0
    if spec.kind == "float":
        return 0.0
    if spec.kind == "string":
        return ""
    if spec.kind in ("bitmask_int", "bitmask_long", "bitmask_blob"):
        return {}
    if spec.kind == "timestamp":
        return save_schema.TS_NEVER
    raise ValueError(f"unhandled kind {spec.kind!r}")


def blank_fixed_object(table, rules, src, now, template_mode):
    """Zero a fixed-shape (non-roster) object's fields against `table` (its
    {suffix: FieldSpec} registry, straight from tools/save_schema.py) and
    `rules` ({suffix: literal | callable(now) | _KEEP | _DROP}, only for
    suffixes that need something other than the generic per-kind zero).

    Template mode: a suffix with no rule is kept exactly as `src` had it -
    old blank_save.py's actual behavior was a curated whitelist of
    "progress" fields reset to zero/dropped, everything else (identity/
    build fields, anything not reasoned about) passed through unchanged
    rather than guessed at, and this preserves that. A rule forces a
    suffix to appear even when `src` lacks it (e.g. Settings.DisableCloud
    is unconditionally set True regardless of the original value).

    Bare mode (no template at all): every non-Switch-only, non-sparse
    field in `table` is included, since those are on every real save
    regardless of platform/progress; `rules` still applies its overrides/
    drops on top. A field with no rule gets the generic per-kind zero for
    its own FieldSpec.kind - nothing here duplicates that decision."""
    src = src or {}
    force_keys = {k for k, v in rules.items() if v is not _KEEP}
    if template_mode:
        keys = set(src.keys()) | force_keys
    else:
        keys = {k for k, spec in table.items() if not spec.switch_only and not spec.sparse}
        keys = (keys | force_keys) - {k for k, v in rules.items() if v is _DROP}
    result = {}
    for suffix in keys:
        rule = rules.get(suffix, _KEEP)
        if rule is _DROP:
            continue
        if rule is _KEEP:
            if template_mode:
                if suffix in src:
                    result[suffix] = src[suffix]
            elif suffix in table:
                result[suffix] = _generic_zero(table[suffix])
            continue
        result[suffix] = rule(now) if callable(rule) else rule
    return result


# ---------------------------------------------------------------------------
# Per-object RULES: only fields that need something other than "keep as-is"
# (template mode) / "generic per-kind zero" (bare mode) are listed here.
# ---------------------------------------------------------------------------

GAMESTATE_RULES = {
    "Date": lambda now: now.isoformat(),
    "DateUTC": lambda now: now.isoformat(),
    "LoginDate": lambda now: now.isoformat(),
    "Ids": _DROP,  # player/machine cloud-sync ID - don't carry into a blank
    "NSFW": _DROP,  # default off
    "Timeline": _DROP,  # Time Warp PE-only in practice, not tagged switch_only so filter this explicitly
    "TimeCrystalCount": _DROP,  # same as Timeline above
}
# GAMESTATE_COUNT_FIELDS/GAMESTATE_MULTIPLIER_FIELDS in save_schema.py are
# keyed by the *raw* suffix (DateCount, PendingMultiplier, ...); rebuild by
# the stripped JSON-side key instead (each tuple's first element) to match
# how blank_out below actually indexes GameState.Counts/Multipliers.
GAMESTATE_COUNTS_TABLE = {json_key: spec for _raw, (json_key, spec) in save_schema.GAMESTATE_COUNT_FIELDS.items()}
GAMESTATE_COUNTS_RULES = {}  # generic zero for all four is exactly right
GAMESTATE_MULTIPLIERS_TABLE = {
    **{json_key: spec for _raw, (json_key, spec) in save_schema.GAMESTATE_MULTIPLIER_FIELDS.items()},
    "Time": save_schema.FieldSpec("float"),  # root TimeMultiplier / pes<N>TimeMultiplier, folded in here
}
GAMESTATE_MULTIPLIERS_RULES = {
    "Time": 1.0,  # no active boost/penalty
    # Purchased (lifetime IAP-purchased boost) has no rule: template mode
    # keeps the real value (it represents money actually spent, not
    # "progress" to reset), bare mode's generic zero (0.0) is correct too
    # (nothing purchased yet).
}

SETTINGS_RULES = {
    "Effects": 1.0,
    "Music": 1.0,
    "Voice": 1.0,
    "DisableCloud": True,  # don't let a blank test save sync over a real cloud save
}

SKILL_RULES = {str(n): 0 for n in range(12)}  # full replacement, not conditional on template presence

PLAYER_RULES = {"Gender": 0, "Hair": 0, "Hat": 0, "Plushy": 0}

PLAYFAB_RULES = {"Inventory": {}, "Participation": {}, "AwardedItems": []}

ROOT_SCALAR_RULES = {
    "AchievementCount": 0,
    "dchk": 0,
    "ana.ev": 0,
    "ana.vid": 0,
    "Tutorial": 0,
    "HasSeenFuzzyExternalPurchaseConfirmation": _DROP,
    "Prereg": _DROP,
    "TermsVersionAccepted": _DROP,
    "ticketboothSeen": _DROP,
}

COMPLETED_TABLE = {
    "2018": save_schema.FieldSpec("bitmask_long"),
    "2019": save_schema.FieldSpec("bitmask_long"),
    "2020": save_schema.FieldSpec("bitmask_long"),
    "LTE": save_schema.FieldSpec("bitmask_blob"),
}


def blank_girls(girls_src, template_mode, now):
    girls_src = girls_src or {}
    meta_rules = {"Unlocked": {}, "PreviouslyUnlocked": {}, "Current": 0}
    result = blank_fixed_object({}, meta_rules, girls_src, now, template_mode)
    for name in girls_src:
        if name not in meta_rules:
            result[name] = {"Hearts": 0}  # drop Love/Life/Clothing/Dates/GiftCount*/DateCount*/LoveHighMark
    return result


def blank_jobs(jobs_src, template_mode, now):
    jobs_src = jobs_src or {}
    meta_rules = {"Available": {}}
    result = blank_fixed_object({}, meta_rules, jobs_src, now, template_mode)
    for name in jobs_src:
        if name not in meta_rules:
            result[name] = {"Experience": 0, "Time": 0.0}  # drop Active/Gilded/Level/Locked
    return result


def blank_hobby(hobby_src):
    # No account-wide sibling scalars (unlike Girls/Jobs) - purely a
    # name-keyed roster, so an untouched template still yields {} here.
    return {name: {"Time": 0.0, "TimeL": 0} for name in (hobby_src or {})}  # drop Active/MultiplierCount


def blank_flings(flings_src, template_mode, now):
    flings_src = flings_src or {}
    meta_rules = {"Unlocked": {}, "Purchased": {}}
    result = blank_fixed_object({}, meta_rules, flings_src, now, template_mode)
    for fid in flings_src:
        if fid not in meta_rules:
            result[fid] = {"Date": save_schema.TS_NEVER, "Progress": None}
    return result


def blank_events(events_src, template_mode, now):
    # PE/LTE/Current are dropped entirely (no active/past event state in a
    # fresh account) - only Completed (lifetime weekly/LTE completion) has
    # a coherent "zero" reading independent of any roster.
    completed_src = (events_src or {}).get("Completed") if template_mode else None
    completed = blank_fixed_object(COMPLETED_TABLE, {}, completed_src, now, template_mode)
    return {"Completed": completed} if completed else {}


def blank_root_scalars(data, template_mode, now):
    src = {k: data[k] for k in save_schema.ROOT_SCALAR_FIELDS if k in data} if template_mode else {}
    return blank_fixed_object(save_schema.ROOT_SCALAR_FIELDS, ROOT_SCALAR_RULES, src, now, template_mode)


def blank_out(data, now):
    """`data` is the template dict in template mode, {} in bare mode (see
    module docstring) - a real decoded save is never actually empty, so
    "was a template given" is exactly `bool(data)`."""
    template_mode = bool(data)
    result = {}

    gs_src = data.get("GameState") if template_mode else None
    gs = blank_fixed_object(save_schema.GAMESTATE_FIELDS, GAMESTATE_RULES, gs_src, now, template_mode)
    counts = blank_fixed_object(
        GAMESTATE_COUNTS_TABLE, GAMESTATE_COUNTS_RULES, (gs_src or {}).get("Counts"), now, template_mode)
    if counts:
        gs["Counts"] = counts
    multipliers = blank_fixed_object(
        GAMESTATE_MULTIPLIERS_TABLE, GAMESTATE_MULTIPLIERS_RULES, (gs_src or {}).get("Multipliers"), now,
        template_mode)
    if multipliers:
        gs["Multipliers"] = multipliers
    if gs:
        result["GameState"] = gs

    settings = blank_fixed_object(save_schema.SETTINGS_FIELDS, SETTINGS_RULES, data.get("Settings"), now,
                                   template_mode)
    if settings:
        result["Settings"] = settings

    skill = blank_fixed_object(save_schema.SKILL_FIELDS, SKILL_RULES, data.get("Skill"), now, template_mode)
    if skill:
        result["Skill"] = skill

    player = blank_fixed_object(save_schema.PLAYER_FIELDS, PLAYER_RULES, data.get("Player"), now, template_mode)
    if player:
        result["Player"] = player

    playfab = blank_fixed_object({}, PLAYFAB_RULES, data.get("Playfab"), now, template_mode)
    if playfab:
        result["Playfab"] = playfab

    result["Girls"] = blank_girls(data.get("Girls"), template_mode, now)

    jobs = blank_jobs(data.get("Jobs"), template_mode, now)
    if jobs:
        result["Jobs"] = jobs

    hobby = blank_hobby(data.get("Hobby"))
    if hobby:
        result["Hobby"] = hobby

    flings = blank_flings(data.get("Flings"), template_mode, now)
    if flings:
        result["Flings"] = flings

    events = blank_events(data.get("Events"), template_mode, now)
    if events:
        result["Events"] = events

    result.update(blank_root_scalars(data, template_mode, now))

    if template_mode and "events.popupinfo" in data:
        result["events.popupinfo"] = {}
    if template_mode and "Unknown" in data:
        result["Unknown"] = data["Unknown"]

    # Achievement, Bonuses, and LastPesId<N> have no "zero" reading worth
    # keeping (no achievement entries, "let the game recreate the shop
    # tables on load", no recent-LTE history) - never emitted in either
    # mode. Anything else present in a template but not reasoned about
    # above (e.g. Albums) is kept unchanged rather than guessed at.
    handled = ({
        "GameState", "Settings", "Skill", "Player", "Playfab", "Girls", "Jobs", "Hobby", "Flings",
        "Achievement", "Events", "Bonuses", "events.popupinfo", "Unknown", "$schema",
    } | set(save_schema.ROOT_SCALAR_FIELDS) | set(save_schema.LAST_PES_ID_KEYS))
    if template_mode:
        for key, value in data.items():
            if key not in handled and key not in result:
                result[key] = value

    return result


def main():
    args = sys.argv[1:]
    if args and args[0] == "--bare":
        template_arg, args = None, args[1:]
    elif args:
        template_arg, args = args[0], args[1:]
    else:
        template_arg = None
    output_path = ROOT / (args[0] if args else "decoded/crushcrush.blank.json")

    now = datetime.now(timezone.utc).replace(tzinfo=None)

    if template_arg is not None:
        template_path = ROOT / template_arg
        data = json.loads(template_path.read_text())
        data.pop("$schema", None)
        source_desc = str(template_path)
    else:
        data = {}
        source_desc = "(bare -- generated from tools/save_schema.py's field tables)"

    blanked = blank_out(data, now)
    blanked["$schema"] = crushcrush_save.SCHEMA_URL

    output_path.parent.mkdir(parents=True, exist_ok=True)
    out_text = json.dumps(blanked, indent=2, sort_keys=True)
    output_path.write_text(out_text)
    print(f"{source_desc} -> {output_path} ({len(out_text)} bytes)")


if __name__ == "__main__":
    main()
