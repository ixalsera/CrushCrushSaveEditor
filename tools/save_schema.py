#!/usr/bin/env python3
"""Typed JSON <-> flat `::`-text schema layer for Crush Crush saves.

Sits between `tools/crushcrush_save.py`'s container-format layer (which only
ever sees/produces the flat plaintext) and the CLI: `decode_save_text` turns
that flat text into a structured, human-editable dict ready for
`json.dumps`; `encode_save_text` reverses it, targeting either PC or Switch
(`nintendo=True`) regardless of which platform the JSON originated from.

Key design facts (see CLAUDE.md and the per-key docs for the underlying
reverse-engineering; this module assumes that background):

- `::` grouping in the flat text is cosmetic, not semantic -- the same
  field can appear inside a named `::Prefix` section in one save and as an
  individually-bare line in another (confirmed: `JobMECH` has all six of
  its fields bare in a real sample, in the same file where other jobs get a
  proper block). So encoding never tries to reconstruct original grouping;
  every field is rendered as its own independent `::` + line.
- PC and Switch differ in sparse-vs-dense serialization for *some* fields
  (PC omits at the zero/false default; Switch writes it explicitly) but not
  others (fixed-struct fields like GameState/Settings/Skill/Girl.Hearts are
  dense on both). `FieldSpec.sparse` marks which fields are ever eligible
  for omission; `dense=nintendo` decides whether omission actually happens.
- A field valued exactly 1 (for `int`-family kinds) renders as a bare key,
  same shape as a true flag -- confirmed on real data for `ACH.<id>`,
  `GirlAyanoDates`, `SkillGender`/`Hat`. `long`/`float` fields are always
  written explicitly (never bare, never omitted at 0).
- Bitmask blob byte-width is not a fixed constant in practice -- encode by
  shrink-to-fit (highest set bit) with a small per-field safety floor,
  never a hardcoded width.
"""
import base64
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "utils"))
import phone_fling  # noqa: E402
import timestamp  # noqa: E402

TS_NA = "N/A"
TS_NEVER = "never"


@dataclass(frozen=True)
class FieldSpec:
    kind: str  # flag|int|long|float|string|bitmask_int|bitmask_long|bitmask_blob|timestamp
    sparse: bool = False
    ts_kind: str | None = None  # local|utc|unspecified -- timestamp only
    # Documents that this field was only ever observed on Switch saves
    # (per docs/SWITCH.md and the one real Switch sample). Informational
    # only -- it does NOT drive encode behavior: real data shows fields
    # SWITCH.md calls Switch-only (e.g. GameState.Boost2EndTime) can also
    # appear in PC saves, and genuinely Switch-only fields aren't reliably
    # present in every real Switch save either (early-game saves lack
    # several). Dropping or fabricating fields based on this tag destroyed
    # same-platform round-trips in testing -- see emit_object/emit_gamestate.
    switch_only: bool = False
    blob_min_bytes: int = 1  # bitmask_blob only -- shrink-to-fit floor


# ---------------------------------------------------------------------------
# Low-level value codecs
# ---------------------------------------------------------------------------

def parse_numeric_token(raw):
    """raw is None for a bare key (=> 1), else the text after ':'."""
    if raw is None:
        return 1
    if raw == "":
        return 0
    if raw.endswith("i"):
        return int(raw[:-1])
    if raw.endswith("f"):
        return float(raw[:-1])
    return int(raw)


def bits_to_json(value):
    value = int(value)
    return {str(i): True for i in range(value.bit_length()) if value & (1 << i)}


def json_to_bits(obj):
    if not obj:
        return 0
    return sum(1 << int(k) for k, v in obj.items() if v)


def blob_bits_to_json(b64):
    """Decodes a bitmask blob. Some real samples store what SCHEMA.md
    documents as a base64 blob field as a plain int instead (observed:
    `GirlsUnlocked:19i` in one PC save) -- fall back to a raw-preserving
    wrapper rather than crashing, so round-trip stays lossless even for
    fields that don't match the documented shape in a given save."""
    if not b64:
        return {}
    try:
        data = base64.b64decode(b64, validate=True)
    except Exception:
        return {"_raw_fallback": decode_unknown(b64)}
    return bits_to_json(int.from_bytes(data, "little"))


def json_to_blob_bits(obj, min_bytes=1):
    if isinstance(obj, dict) and "_raw_fallback" in obj:
        return encode_unknown(obj["_raw_fallback"])
    n = json_to_bits(obj)
    width = max(min_bytes, (n.bit_length() + 7) // 8)
    return base64.b64encode(n.to_bytes(width, "little")).decode()


def blob_text_to_json(b64):
    if not b64:
        return []
    text = base64.b64decode(b64).decode("utf-8")
    return text.split("|") if text else []


def json_to_blob_text(items):
    if isinstance(items, dict) and "_raw_fallback" in items:
        return encode_unknown(items["_raw_fallback"])
    return base64.b64encode("|".join(items).encode("utf-8")).decode()


def decode_awarded_items(raw):
    """Defensive: some real samples have an AwardedItems value that isn't
    valid base64 (a Switch sample has PlayfabAwardedItems:0; a PC sample
    has PlayfabAwardedItems:135516928i) -- fall back to a raw-preserving
    wrapper (same pattern as blob_bits_to_json) rather than discarding it."""
    if not raw:
        return []
    try:
        text = base64.b64decode(raw, validate=True).decode("utf-8")
    except Exception:
        return {"_raw_fallback": decode_unknown(raw)}
    return text.split("|") if text else []


def timestamp_to_json(value):
    kind, dt = timestamp.decode(int(value))
    if kind in (TS_NA, TS_NEVER):
        return kind
    return dt.isoformat()


def json_to_timestamp(value, ts_kind):
    if value == TS_NA:
        return timestamp.MAX_SENTINEL
    if value == TS_NEVER:
        return 0
    from datetime import datetime
    return timestamp.encode(datetime.fromisoformat(value), ts_kind)


def fling_p_to_json(blob_b64):
    state = phone_fling.decode_conversation_state(blob_b64)
    if state is None:
        return None
    return {
        "message_counter": state["message_counter"],
        "unknown_1": state["unknown_1"],
        "next_message_countdown": state["next_message_countdown"],
        "trailing": state["trailing"].hex(),
    }


def json_to_fling_p(obj):
    if obj is None:
        return ""
    state = {
        "message_counter": int(obj["message_counter"]),
        "unknown_1": int(obj["unknown_1"]),
        "next_message_countdown": int(obj["next_message_countdown"]),
        "trailing": bytes.fromhex(obj["trailing"]),
    }
    return base64.b64encode(phone_fling.encode_conversation_state(state)).decode()


def decode_unknown(raw):
    """Forward-compatible wrapper for a key matching a known object prefix
    but an unregistered suffix -- preserves the exact original int/long/
    float/bare distinction so it survives round-trip even though it's not
    in the registry yet."""
    if raw is None:
        return {"value": True, "raw_suffix": None}
    if raw == "":
        return {"value": "", "raw_suffix": ""}
    if raw.endswith("i"):
        return {"value": int(raw[:-1]), "raw_suffix": "i"}
    if raw.endswith("f"):
        return {"value": float(raw[:-1]), "raw_suffix": "f"}
    try:
        return {"value": int(raw), "raw_suffix": ""}
    except ValueError:
        return {"value": raw, "raw_suffix": ""}


def encode_unknown(obj):
    suf = obj.get("raw_suffix")
    val = obj["value"]
    if suf is None:
        return ""
    if suf == "i":
        return f"{int(val)}i"
    if suf == "f":
        return f"{val}f"
    return str(val)


def set_field(container, key, spec, raw):
    if spec.kind == "flag":
        container[key] = raw is None or parse_numeric_token(raw) != 0
    elif spec.kind in ("int", "long"):
        container[key] = int(parse_numeric_token(raw))
    elif spec.kind == "float":
        container[key] = float(parse_numeric_token(raw))
    elif spec.kind == "string":
        container[key] = raw if raw is not None else ""
    elif spec.kind in ("bitmask_int", "bitmask_long"):
        container[key] = bits_to_json(int(parse_numeric_token(raw)))
    elif spec.kind == "bitmask_blob":
        container[key] = blob_bits_to_json(raw or "")
    elif spec.kind == "timestamp":
        container[key] = timestamp_to_json(int(parse_numeric_token(raw)))
    else:
        raise ValueError(f"unhandled kind {spec.kind!r}")


def render_value(spec, value, dense):
    if spec.kind == "flag":
        if value:
            return ""
        return None if (spec.sparse and not dense) else "0i"
    if spec.kind in ("int", "bitmask_int"):
        n = json_to_bits(value) if spec.kind == "bitmask_int" else int(value)
        if n == 1:
            return ""
        if n == 0:
            return None if (spec.sparse and not dense) else "0i"
        return f"{n}i"
    if spec.kind == "bitmask_long":
        return str(json_to_bits(value))
    if spec.kind == "long":
        return str(int(value))
    if spec.kind == "float":
        v = float(value)
        if v == int(v) and abs(v) < 1e15:
            return f"{int(v)}f"
        return f"{v}f"
    if spec.kind == "string":
        return value
    if spec.kind == "bitmask_blob":
        return json_to_blob_bits(value, min_bytes=spec.blob_min_bytes)
    if spec.kind == "timestamp":
        return str(json_to_timestamp(value, spec.ts_kind))
    raise ValueError(f"unhandled kind {spec.kind!r}")


# ---------------------------------------------------------------------------
# Per-object field tables
# ---------------------------------------------------------------------------

GAMESTATE_FIELDS = {
    "Build": FieldSpec("string"),
    "Date": FieldSpec("timestamp", ts_kind="local"),
    "DateUTC": FieldSpec("timestamp", ts_kind="utc"),
    "Diamonds": FieldSpec("long"),
    "Hobbies": FieldSpec("int"),
    "Ids": FieldSpec("string"),
    "LoginDate": FieldSpec("timestamp", ts_kind="utc"),
    "Money": FieldSpec("long"),
    "NSFW": FieldSpec("flag", sparse=True),
    "Seconds": FieldSpec("float"),
    "TotalIncome": FieldSpec("long"),
    "TotalTime": FieldSpec("int"),
    "Timeline": FieldSpec("string"),  # Time Warp PE-only in practice
    "TimeCrystalCount": FieldSpec("int"),  # Time Warp PE-only in practice
    "TimelineComplete": FieldSpec("flag", sparse=True),
    "Boost2EndTime": FieldSpec("long", switch_only=True),
    "TimeSkip2EndTime": FieldSpec("long", switch_only=True),
    "Created": FieldSpec("timestamp", ts_kind="utc", switch_only=True),
    "DateOffset": FieldSpec("int", switch_only=True),
    "Covid2020": FieldSpec("int", switch_only=True),
}

# GameState.Counts / GameState.Multipliers: raw suffix -> (stripped JSON key, spec).
# TimeMultiplier is handled separately (see try_gamestate/emit_gamestate) since its
# raw key never carries a GameState/pes<N>GameState prefix, unlike these two.
GAMESTATE_COUNT_FIELDS = {
    "DateCount": ("Date", FieldSpec("int")),
    "GiftCount": ("Gift", FieldSpec("int")),
    "HeartCount": ("Heart", FieldSpec("long")),
    "PokeCount": ("Poke", FieldSpec("int")),
}
GAMESTATE_MULTIPLIER_FIELDS = {
    "PendingMultiplier": ("Pending", FieldSpec("float")),
    "PurchasedMultiplier": ("Purchased", FieldSpec("float")),
}

SETTINGS_FIELDS = {
    "Alphabetic": FieldSpec("flag", sparse=True),
    "DisableCloud": FieldSpec("flag", sparse=True),
    "Effects": FieldSpec("float"),
    "Music": FieldSpec("float"),
    "Voice": FieldSpec("float"),
    "IntrosOff": FieldSpec("flag", sparse=True, switch_only=True),
    "ParticlesOff": FieldSpec("flag", sparse=True, switch_only=True),
    "PopupsOff": FieldSpec("flag", sparse=True, switch_only=True),
    "Language": FieldSpec("string", switch_only=True),
    "MusicMute": FieldSpec("flag", sparse=True, switch_only=True),
    "SoundMute": FieldSpec("flag", sparse=True, switch_only=True),
}

SKILL_FIELDS = {str(n): FieldSpec("int") for n in range(12)}

# Avatar/player-identity fields -- raw keys are Skill-prefixed (SkillGender
# etc) but conceptually belong to the player, not a per-hobby skill level,
# so they're pulled out into their own root Player object. Root-only: a
# hypothetical pes<N>SkillGender (never observed) stays inside that PE's
# Skill object via the generic unregistered-suffix fallback rather than
# being promoted, since there's no such thing as a per-event avatar.
PLAYER_FIELDS = {
    "Gender": FieldSpec("int"),
    "Hair": FieldSpec("int"),
    "Hat": FieldSpec("int"),
    "Plushy": FieldSpec("int"),
}

JOB_FIELDS = {
    "Active": FieldSpec("flag", sparse=True),
    "Experience": FieldSpec("long"),
    "Gilded": FieldSpec("flag", sparse=True),
    "Level": FieldSpec("int", sparse=True),
    "Locked": FieldSpec("flag", sparse=True),
    "Time": FieldSpec("float"),
}

HOBBY_FIELDS = {
    "Active": FieldSpec("flag", sparse=True),
    "MultiplierCount": FieldSpec("flag", sparse=True),
    "Time": FieldSpec("float"),
    "TimeL": FieldSpec("long"),
}

TASK_FIELDS = {
    "Start": FieldSpec("timestamp", ts_kind="unspecified"),
    "Complete": FieldSpec("flag", sparse=True),
    "Claimed": FieldSpec("flag", sparse=True),
}

PE_EXTRA_FIELDS = {
    "Goals": FieldSpec("bitmask_int"),
    "PurchasedTime": FieldSpec("int"),
    "Start": FieldSpec("timestamp", ts_kind="utc"),
}

ROOT_SCALAR_FIELDS = {
    "AchievementCount": FieldSpec("int"),
    "dchk": FieldSpec("int"),
    "ana.ev": FieldSpec("long"),
    "ana.vid": FieldSpec("long"),
    "Prereg": FieldSpec("flag", sparse=True),
    "SaveFileVersion": FieldSpec("flag", sparse=True),
    "TermsVersionAccepted": FieldSpec("flag", sparse=True),
    "ticketboothSeen": FieldSpec("flag", sparse=True),
    "Tutorial": FieldSpec("int"),
    "HasSeenFuzzyExternalPurchaseConfirmation": FieldSpec("flag", sparse=True),
    "CabinFeverSave": FieldSpec("int", switch_only=True),
    "PendingTimelord": FieldSpec("int", switch_only=True),
    "UserLteOffset": FieldSpec("int", switch_only=True),
    "AyanoChibi2017": FieldSpec("int", switch_only=True),
    "AyanoTimeBlock": FieldSpec("int", switch_only=True),
    "CurrentPanel": FieldSpec("string", switch_only=True),
    "NutakuItems2019": FieldSpec("int", switch_only=True),
    "ActiveTutorial": FieldSpec("int", switch_only=True),
    "TutorialStep": FieldSpec("int", switch_only=True),
    "TutorialAffection": FieldSpec("flag", sparse=True, switch_only=True),
    "PurchasedTime": FieldSpec("int"),  # also appears un-prefixed at root, not just per-PE
}

LAST_PES_ID_KEYS = [f"LastPesId{n}" for n in range(10)]

BONUS_CATEGORIES = {"timeblocks": "Time Blocks", "speedboost": "Speed Boost", "timeskip": "Time Skip"}
BONUS_SIZES = {"small": "Small", "medium": "Medium", "large": "Large"}
BONUS_FIELDS = {"pri": "Price", "qty": "Quantity"}

SHOP_TABLE_RE = re.compile(r"^\.(speedboost|timeblocks|timeskip)\.(large|medium|small)\.(pri|qty)$")
GIRL_BARE_RE = re.compile(
    r"^Girl([A-Za-z]+?)(Hearts|Love|LifeDates|LifeOutfits|LifeGifts|Clothing|GiftCount\d*|DateCount\d*|Dates)$"
)
JOB_BARE_RE = re.compile(r"^Job([A-Z][A-Z ]*)(Active|Experience|Gilded|Level|Locked|Time)$")
HOBBY_BARE_RE = re.compile(r"^Hobby([A-Za-z]+?)(Active|MultiplierCount|Time|TimeL)$")
FLING_RE = re.compile(r"^C(\d+)([DP])$")
ACH_BARE_RE = re.compile(r"^ACH(\d+)$")
TASK_BARE_RE = re.compile(r"^Task(\d+)(Start|Complete|Claimed)$")
TASK_NAMED_RE = re.compile(r"^(\d+)(Start|Complete|Claimed)$")
EVENT_TOKENS_RE = re.compile(r"^Event(\d+)Tokens$")
PES_RE = re.compile(r"^[Pp]es(\d+)(.*)$")
LOVE_HIGH_MARK_RE = re.compile(r"^Girl([a-z]+)LoveHighMark$")
ALBUM_RE = re.compile(r"^album(\d)$")

FIXED_PREFIX_TABLES = {
    "Settings": SETTINGS_FIELDS,
    "Skill": SKILL_FIELDS,
}


def album_value_to_json(value):
    """album<N> is a sparse two-level bitmask by user request: byte index ->
    bit index -> bool, little-endian, shrink-to-fit (same conventions as
    every other bitmask in this schema, just one level deeper)."""
    v = int(value) & 0xFFFFFFFFFFFFFFFF  # unsigned 64-bit, mirrors utils/timestamp.py
    result, byte_idx = {}, 0
    while v:
        byte = v & 0xFF
        if byte:
            result[str(byte_idx)] = {str(b): True for b in range(8) if byte & (1 << b)}
        v >>= 8
        byte_idx += 1
    return result


def json_to_album_value(obj):
    value = 0
    for byte_idx_str, bits in (obj or {}).items():
        value |= sum(1 << int(b) for b, on in bits.items() if on) << (int(byte_idx_str) * 8)
    return value


# ---------------------------------------------------------------------------
# Decode: flat text -> JSON-able dict
# ---------------------------------------------------------------------------

def parse_segments_lenient(text):
    """Like blank_save.parse_segments, but tolerant of a file that never
    uses `::` markers at all -- confirmed real: the Switch sample
    (saves/CrushSaveData1.sav) decodes with zero `::` lines anywhere, every
    key written in fully bare form one per line, unlike PC's convention of
    a bare `::` reset before every ungrouped key. Lines before the first
    `::` (or the whole file, if there is none) are treated as their own
    independent bare entries, same as lines under an explicit bare `::`."""
    segments = [["", []]]
    for line in text.split("\n"):
        if line == "::":
            segments.append(["", []])
        elif line.startswith("::"):
            segments.append([line[2:], []])
        else:
            segments[-1][1].append(line)
    return [s for s in segments if s[1]]


def flatten_segments(segments):
    """Yield (origin_prefix, origin_suffix, full_key, raw) per line.
    origin_prefix == "" means the line was a bare key (no named section) --
    full_key IS the whole key, origin_suffix is None. Otherwise
    origin_prefix is the exact `::Name` section text and origin_suffix is
    that line's own key text (the section header already isolated the
    name -- but see try_girl for why that alone isn't trustworthy for
    every field)."""
    out = []
    for prefix, lines in segments:
        for line in lines:
            if ":" in line:
                k, v = line.split(":", 1)
            else:
                k, v = line, None
            full_key = prefix + k
            if prefix:
                out.append((prefix, k, full_key, v))
            else:
                out.append(("", None, full_key, v))
    return out


def try_player(origin_prefix, origin_suffix, full_key, raw, data):
    if origin_prefix == "Skill":
        suffix = origin_suffix
    elif origin_prefix == "" and full_key.startswith("Skill"):
        suffix = full_key[len("Skill"):]
    else:
        return False
    if suffix not in PLAYER_FIELDS:
        return False
    set_field(data.setdefault("Player", {}), suffix, PLAYER_FIELDS[suffix], raw)
    return True


def try_fixed_prefix_object(origin_prefix, origin_suffix, full_key, raw, data):
    for prefix, table in FIXED_PREFIX_TABLES.items():
        if origin_prefix == prefix:
            suffix = origin_suffix
        elif origin_prefix == "" and full_key.startswith(prefix):
            suffix = full_key[len(prefix):]
        else:
            continue
        obj = data.setdefault(prefix, {})
        spec = table.get(suffix)
        if spec is not None:
            set_field(obj, suffix, spec, raw)
        else:
            obj[suffix] = decode_unknown(raw)
        return True
    return False


def try_playfab(origin_prefix, origin_suffix, full_key, raw, data):
    if origin_prefix == "Playfab":
        suffix = origin_suffix
    elif origin_prefix == "" and full_key.startswith("Playfab"):
        suffix = full_key[len("Playfab"):]
    else:
        return False
    if suffix == "FlingPurchases":
        data.setdefault("Flings", {})["Purchased"] = bits_to_json(int(parse_numeric_token(raw)))
    elif suffix == "Inventory":
        data.setdefault("Playfab", {})["Inventory"] = bits_to_json(int(parse_numeric_token(raw)))
    elif suffix == "Participation":
        data.setdefault("Playfab", {})["Participation"] = blob_bits_to_json(raw or "")
    elif suffix == "AwardedItems":
        data.setdefault("Playfab", {})["AwardedItems"] = decode_awarded_items(raw)
    else:
        data.setdefault("Playfab", {})[suffix] = decode_unknown(raw)
    return True


def try_completed(origin_prefix, origin_suffix, full_key, raw, data):
    if origin_prefix == "Completed":
        suffix = origin_suffix
    elif origin_prefix == "" and full_key.startswith("Completed"):
        suffix = full_key[len("Completed"):]
    else:
        return False
    completed = data.setdefault("Events", {}).setdefault("Completed", {})
    if suffix == "2018Events":
        completed["2018"] = bits_to_json(int(parse_numeric_token(raw)))
    elif suffix == "2019Events":
        completed["2019"] = bits_to_json(int(parse_numeric_token(raw)))
    elif suffix == "2020Events":
        completed["2020"] = bits_to_json(int(parse_numeric_token(raw)))
    elif suffix == "Events":
        completed["LTE"] = blob_bits_to_json(raw or "")
    else:
        completed[suffix] = decode_unknown(raw)
    return True


def try_ach(origin_prefix, origin_suffix, full_key, raw, data):
    if origin_prefix == "ACH":
        id_str = origin_suffix
    else:
        m = ACH_BARE_RE.match(full_key)
        if not m:
            return False
        id_str = m.group(1)
    data.setdefault("Achievement", {})[id_str] = bits_to_json(int(parse_numeric_token(raw)))
    return True


def try_task(origin_prefix, origin_suffix, full_key, raw, pending_tasks):
    if origin_prefix == "Task":
        m = TASK_NAMED_RE.match(origin_suffix or "")
        if not m:
            return False
        num, field = m.group(1), m.group(2)
    else:
        if origin_prefix != "":
            return False
        m = TASK_BARE_RE.match(full_key)
        if not m:
            return False
        num, field = m.group(1), m.group(2)
    entry = pending_tasks.setdefault(num, {})
    if field == "Start":
        entry["Start"] = timestamp_to_json(int(parse_numeric_token(raw)))
    else:
        entry[field] = raw is None or parse_numeric_token(raw) != 0
    return True


def try_fling(origin_prefix, full_key, raw, data):
    if origin_prefix != "":
        return False
    m = FLING_RE.match(full_key)
    if not m:
        return False
    fid, kind = m.group(1), m.group(2)
    flings = data.setdefault("Flings", {})
    entry = flings.setdefault(fid, {"Date": None, "Progress": None})
    if kind == "D":
        entry["Date"] = timestamp_to_json(int(parse_numeric_token(raw)))
    else:
        entry["Progress"] = fling_p_to_json(raw or "")
    return True


def try_gamestate(origin_prefix, origin_suffix, full_key, raw, data):
    if origin_prefix == "GameState":
        suffix = origin_suffix
    elif origin_prefix == "" and full_key.startswith("GameState"):
        suffix = full_key[len("GameState"):]
    else:
        return False
    gs = data.setdefault("GameState", {})
    if suffix in GAMESTATE_COUNT_FIELDS:
        json_key, spec = GAMESTATE_COUNT_FIELDS[suffix]
        set_field(gs.setdefault("Counts", {}), json_key, spec, raw)
    elif suffix in GAMESTATE_MULTIPLIER_FIELDS:
        json_key, spec = GAMESTATE_MULTIPLIER_FIELDS[suffix]
        set_field(gs.setdefault("Multipliers", {}), json_key, spec, raw)
    else:
        spec = GAMESTATE_FIELDS.get(suffix)
        if spec is not None:
            set_field(gs, suffix, spec, raw)
        else:
            gs[suffix] = decode_unknown(raw)
    return True


def try_job(origin_prefix, origin_suffix, full_key, raw, data):
    # Always split on the *reconstructed* full key, never trust the named
    # `::Prefix` section alone -- see try_girl's docstring for why.
    m = JOB_BARE_RE.match(full_key)
    if not m:
        return False
    name, suffix = m.group(1), m.group(2)
    job = data.setdefault("Jobs", {}).setdefault(name, {})
    spec = JOB_FIELDS.get(suffix)
    if spec:
        set_field(job, suffix, spec, raw)
    else:
        job[suffix] = decode_unknown(raw)
    return True


def try_girl(origin_prefix, origin_suffix, full_key, raw, data):
    # Always split on the *reconstructed* full key, never trust the named
    # `::Prefix` section alone: `GirlPamulzebub`/`GirlQuillzone` are
    # entirely separate girls that only visually nest under `::GirlPamu`/
    # `::GirlQuill` because their names share that prefix substring -- the
    # section header "GirlPamu" is NOT reliable evidence that every line
    # under it belongs to Pamu (confirmed: real saves have a `lzebubHearts`
    # suffix line under `::GirlPamu` that's actually Pamulzebub's Hearts).
    # Full-key regex matching resolves this correctly because "Hearts" only
    # matches the alternation once the whole "Pamulzebub" name is captured.
    m = GIRL_BARE_RE.match(full_key)
    if not m:
        return False
    name, suffix = m.group(1), m.group(2)
    girl = data.setdefault("Girls", {}).setdefault(name, {})
    if suffix in ("LifeDates", "LifeOutfits", "LifeGifts"):
        life = girl.setdefault("Life", {})
        life_key = {"LifeDates": "Dates", "LifeOutfits": "Outfits", "LifeGifts": "Gifts"}[suffix]
        life[life_key] = bits_to_json(int(parse_numeric_token(raw)))
    elif suffix in ("Clothing", "Dates"):
        girl[suffix] = bits_to_json(int(parse_numeric_token(raw)))
    elif suffix == "Hearts":
        girl["Hearts"] = int(parse_numeric_token(raw))
    elif suffix == "Love":
        girl["Love"] = int(parse_numeric_token(raw))
    elif suffix.startswith("GiftCount") or suffix.startswith("DateCount"):
        girl[suffix] = int(parse_numeric_token(raw))
    else:
        girl[suffix] = decode_unknown(raw)
    return True


def try_hobby(origin_prefix, origin_suffix, full_key, raw, data):
    # Always split on the *reconstructed* full key -- see try_girl.
    m = HOBBY_BARE_RE.match(full_key)
    if not m:
        return False
    name, suffix = m.group(1), m.group(2)
    hobby = data.setdefault("Hobby", {}).setdefault(name, {})
    spec = HOBBY_FIELDS.get(suffix)
    if spec:
        set_field(hobby, suffix, spec, raw)
    else:
        hobby[suffix] = decode_unknown(raw)
    return True


def try_root_specials(origin_prefix, full_key, raw, data):
    if origin_prefix != "":
        return False
    if full_key == "GirlsUnlocked":
        data.setdefault("Girls", {})["Unlocked"] = blob_bits_to_json(raw or "")
        return True
    if full_key == "GirlsPreviouslyUnlocked":
        data.setdefault("Girls", {})["PreviouslyUnlocked"] = blob_bits_to_json(raw or "")
        return True
    if full_key == "CurrentGirl":
        data.setdefault("Girls", {})["Current"] = int(parse_numeric_token(raw))
        return True
    if full_key == "UnlockedPFS":
        data.setdefault("Flings", {})["Unlocked"] = blob_bits_to_json(raw or "")
        return True
    if full_key == "AvailableJobs":
        data.setdefault("Jobs", {})["Available"] = bits_to_json(int(parse_numeric_token(raw)))
        return True
    if full_key in ("BlayfapAwardedItems", "PlayfabAwardedItems"):
        data.setdefault("Playfab", {})["AwardedItems"] = decode_awarded_items(raw)
        return True
    if full_key == "EventID":
        data.setdefault("Events", {})["Current"] = int(parse_numeric_token(raw))
        return True
    m = EVENT_TOKENS_RE.match(full_key)
    if m:
        lte = data.setdefault("Events", {}).setdefault("LTE", {}).setdefault(m.group(1), {})
        lte["Tokens"] = int(parse_numeric_token(raw))
        return True
    if full_key in LAST_PES_ID_KEYS:
        data[full_key] = raw if raw is not None else ""
        return True
    return False


def handle_pe_remainder(remainder, raw, pe):
    if try_gamestate("", None, remainder, raw, pe):
        return
    if remainder == "TimeMultiplier":
        pe.setdefault("GameState", {}).setdefault("Multipliers", {})["Time"] = float(parse_numeric_token(raw))
        return
    if try_fixed_prefix_object("", None, remainder, raw, pe):
        return
    m = LOVE_HIGH_MARK_RE.match(remainder)
    if m:
        name = m.group(1)[0].upper() + m.group(1)[1:]
        pe.setdefault("Girls", {}).setdefault(name, {})["LoveHighMark"] = int(parse_numeric_token(raw))
        return
    if try_job("", None, remainder, raw, pe):
        return
    if try_girl("", None, remainder, raw, pe):
        return
    if try_hobby("", None, remainder, raw, pe):
        return
    if remainder in PE_EXTRA_FIELDS:
        set_field(pe, remainder, PE_EXTRA_FIELDS[remainder], raw)
        return
    pe.setdefault("Unknown", {})[remainder] = decode_unknown(raw)


def try_pe(origin_prefix, origin_suffix, full_key, raw, data):
    if origin_prefix != "":
        return False
    m = PES_RE.match(full_key)
    if not m:
        return False
    pe_id, remainder = m.group(1), m.group(2)
    pe = data.setdefault("Events", {}).setdefault("PE", {}).setdefault(pe_id, {})
    handle_pe_remainder(remainder, raw, pe)
    return True


def decode_save_text(text):
    segments = parse_segments_lenient(text)
    entries = flatten_segments(segments)
    data = {}
    pending_tasks = {}
    unknown = {}
    for origin_prefix, origin_suffix, full_key, raw in entries:
        if full_key == "":
            continue  # artifact of a trailing/blank line, not real data
        if full_key in ROOT_SCALAR_FIELDS:
            set_field(data, full_key, ROOT_SCALAR_FIELDS[full_key], raw)
            continue
        if full_key == "events.popupinfo":
            data["events.popupinfo"] = json.loads(raw) if raw else {}
            continue
        if full_key == "TimeMultiplier":
            data.setdefault("GameState", {}).setdefault("Multipliers", {})["Time"] = float(parse_numeric_token(raw))
            continue
        m = ALBUM_RE.match(full_key)
        if m:
            data.setdefault("Albums", {})[m.group(1)] = album_value_to_json(parse_numeric_token(raw))
            continue
        m = SHOP_TABLE_RE.match(full_key)
        if m:
            cat, size, field = m.groups()
            data.setdefault("Bonuses", {}).setdefault(BONUS_CATEGORIES[cat], {}).setdefault(
                BONUS_SIZES[size], {})[BONUS_FIELDS[field]] = int(parse_numeric_token(raw))
            continue
        if try_pe(origin_prefix, origin_suffix, full_key, raw, data):
            continue
        if try_player(origin_prefix, origin_suffix, full_key, raw, data):
            continue
        if try_root_specials(origin_prefix, full_key, raw, data):
            continue
        if try_fling(origin_prefix, full_key, raw, data):
            continue
        if try_task(origin_prefix, origin_suffix, full_key, raw, pending_tasks):
            continue
        if try_ach(origin_prefix, origin_suffix, full_key, raw, data):
            continue
        if try_playfab(origin_prefix, origin_suffix, full_key, raw, data):
            continue
        if try_completed(origin_prefix, origin_suffix, full_key, raw, data):
            continue
        if try_gamestate(origin_prefix, origin_suffix, full_key, raw, data):
            continue
        if try_fixed_prefix_object(origin_prefix, origin_suffix, full_key, raw, data):
            continue
        if try_job(origin_prefix, origin_suffix, full_key, raw, data):
            continue
        if try_girl(origin_prefix, origin_suffix, full_key, raw, data):
            continue
        if try_hobby(origin_prefix, origin_suffix, full_key, raw, data):
            continue
        unknown[full_key] = decode_unknown(raw)
    if pending_tasks:
        current = data.get("Events", {}).get("Current")
        if current is not None:
            lte = data.setdefault("Events", {}).setdefault("LTE", {}).setdefault(str(current), {})
            lte["Tasks"] = pending_tasks
        else:
            unknown["Task"] = pending_tasks
    if unknown:
        data["Unknown"] = unknown
    return data


# ---------------------------------------------------------------------------
# Encode: JSON-able dict -> flat text
# ---------------------------------------------------------------------------

def emit_object(full_prefix, obj, table, emit, nintendo):
    # pc_only/switch_only are informational only, they never drive encode
    # behavior: fields SWITCH.md documents as Switch-only (e.g.
    # GameState.Boost2EndTime) also show up in real PC saves, and fields
    # that ARE genuinely Switch-only aren't reliably present in every real
    # Switch save either (early-game saves lack several of them). So: never
    # drop a field that's present, and never fabricate one that's absent --
    # the one deliberate exception is GameState.Created below, since a
    # PC->Switch conversion has no better source for it than DateUTC.
    obj = dict(obj) if obj else {}
    if full_prefix == "GameState" and nintendo and "Created" not in obj and "DateUTC" in obj:
        obj["Created"] = obj["DateUTC"]
    for suffix, spec in table.items():
        if suffix not in obj:
            continue
        emit(f"{full_prefix}{suffix}", render_value(spec, obj[suffix], nintendo))
    for suffix, value in obj.items():
        if suffix in table:
            continue
        if isinstance(value, dict) and "raw_suffix" in value:
            emit(f"{full_prefix}{suffix}", encode_unknown(value))


def emit_gamestate(full_prefix, gs, emit, nintendo, time_multiplier_key):
    gs = dict(gs) if gs else {}
    if full_prefix == "GameState" and nintendo and "Created" not in gs and "DateUTC" in gs:
        gs["Created"] = gs["DateUTC"]
    for suffix, spec in GAMESTATE_FIELDS.items():
        if suffix in gs:
            emit(f"{full_prefix}{suffix}", render_value(spec, gs[suffix], nintendo))
    counts = gs.get("Counts") or {}
    for raw_suffix, (json_key, spec) in GAMESTATE_COUNT_FIELDS.items():
        if json_key in counts:
            emit(f"{full_prefix}{raw_suffix}", render_value(spec, counts[json_key], nintendo))
    multipliers = gs.get("Multipliers") or {}
    for raw_suffix, (json_key, spec) in GAMESTATE_MULTIPLIER_FIELDS.items():
        if json_key in multipliers:
            emit(f"{full_prefix}{raw_suffix}", render_value(spec, multipliers[json_key], nintendo))
    if "Time" in multipliers:
        emit(time_multiplier_key, render_value(FieldSpec("float"), multipliers["Time"], nintendo))
    for suffix, value in gs.items():
        if suffix in GAMESTATE_FIELDS or suffix in ("Counts", "Multipliers"):
            continue
        if isinstance(value, dict) and "raw_suffix" in value:
            emit(f"{full_prefix}{suffix}", encode_unknown(value))


def encode_girl_entry(full_prefix, girl, emit, nintendo, skip_keys=frozenset()):
    int_spec = FieldSpec("bitmask_int")
    if "Hearts" in girl:
        emit(f"{full_prefix}Hearts", str(int(girl["Hearts"])))
    if "Love" in girl:
        emit(f"{full_prefix}Love", render_value(FieldSpec("int", sparse=True), girl["Love"], nintendo))
    if "Clothing" in girl:
        emit(f"{full_prefix}Clothing", render_value(int_spec, girl["Clothing"], nintendo))
    if "Dates" in girl:
        emit(f"{full_prefix}Dates", render_value(int_spec, girl["Dates"], nintendo))
    life = girl.get("Life") or {}
    if "Dates" in life:
        emit(f"{full_prefix}LifeDates", render_value(int_spec, life["Dates"], nintendo))
    if "Outfits" in life:
        emit(f"{full_prefix}LifeOutfits", render_value(int_spec, life["Outfits"], nintendo))
    if "Gifts" in life:
        emit(f"{full_prefix}LifeGifts", render_value(int_spec, life["Gifts"], nintendo))
    for key, value in girl.items():
        if key in ("Hearts", "Love", "Clothing", "Dates", "Life") or key in skip_keys:
            continue
        if key.startswith("GiftCount") or key.startswith("DateCount"):
            emit(f"{full_prefix}{key}", render_value(FieldSpec("int", sparse=True), value, nintendo))
        elif isinstance(value, dict) and "raw_suffix" in value:
            emit(f"{full_prefix}{key}", encode_unknown(value))


def encode_job_entry(full_prefix, job, emit, nintendo):
    for suffix, spec in JOB_FIELDS.items():
        if suffix in job:
            emit(f"{full_prefix}{suffix}", render_value(spec, job[suffix], nintendo))
    for suffix, value in job.items():
        if suffix in JOB_FIELDS:
            continue
        if isinstance(value, dict) and "raw_suffix" in value:
            emit(f"{full_prefix}{suffix}", encode_unknown(value))


def encode_pe(pe_id, pe, emit, nintendo):
    prefix = f"pes{pe_id}"
    if "GameState" in pe:
        emit_gamestate(f"{prefix}GameState", pe["GameState"], emit, nintendo,
                        time_multiplier_key=f"pes{pe_id}TimeMultiplier")
    if "Settings" in pe:
        emit_object(f"{prefix}Settings", pe["Settings"], SETTINGS_FIELDS, emit, nintendo)
    if "Skill" in pe:
        emit_object(f"{prefix}Skill", pe["Skill"], SKILL_FIELDS, emit, nintendo)
    for name, job in pe.get("Jobs", {}).items():
        encode_job_entry(f"{prefix}Job{name}", job, emit, nintendo)
    for name, girl in pe.get("Girls", {}).items():
        encode_girl_entry(f"{prefix}Girl{name}", girl, emit, nintendo, skip_keys={"LoveHighMark"})
        if "LoveHighMark" in girl:
            lname = name[0].lower() + name[1:] if name else name
            emit(f"{prefix}Girl{lname}LoveHighMark",
                 render_value(FieldSpec("int"), girl["LoveHighMark"], nintendo))
    for name, hobby in pe.get("Hobby", {}).items():
        emit_object(f"{prefix}Hobby{name}", hobby, HOBBY_FIELDS, emit, nintendo)
    for suffix, spec in PE_EXTRA_FIELDS.items():
        if suffix in pe:
            # "Start" is written with a capital-P "Pes<N>" prefix in real
            # saves, unlike every other pes<N>-prefixed key (lowercase) --
            # PES_RE matches both on decode, this just mirrors it back.
            key_prefix = f"Pes{pe_id}" if suffix == "Start" else prefix
            emit(f"{key_prefix}{suffix}", render_value(spec, pe[suffix], nintendo))
    for suffix, value in pe.get("Unknown", {}).items():
        emit(f"{prefix}{suffix}", encode_unknown(value))


def encode_save_text(data, nintendo=False):
    lines = []

    def emit(key, rendered):
        if rendered is None:
            return
        lines.append("::")
        lines.append(key if rendered == "" else f"{key}:{rendered}")

    if "GameState" in data:
        emit_gamestate("GameState", data["GameState"], emit, nintendo, time_multiplier_key="TimeMultiplier")
    if "Settings" in data:
        emit_object("Settings", data["Settings"], SETTINGS_FIELDS, emit, nintendo)
    if "Skill" in data:
        emit_object("Skill", data["Skill"], SKILL_FIELDS, emit, nintendo)

    player = data.get("Player", {})
    for suffix, spec in PLAYER_FIELDS.items():
        if suffix in player:
            emit(f"Skill{suffix}", render_value(spec, player[suffix], nintendo))
    for suffix, value in player.items():
        if suffix in PLAYER_FIELDS:
            continue
        if isinstance(value, dict) and "raw_suffix" in value:
            emit(f"Skill{suffix}", encode_unknown(value))

    playfab = data.get("Playfab", {})
    if "Inventory" in playfab:
        emit("PlayfabInventory", render_value(FieldSpec("bitmask_int"), playfab["Inventory"], nintendo))
    if "Participation" in playfab:
        emit("PlayfabParticipation",
             render_value(FieldSpec("bitmask_blob", blob_min_bytes=7), playfab["Participation"], nintendo))
    if "AwardedItems" in playfab:
        key = "PlayfabAwardedItems" if nintendo else "BlayfapAwardedItems"
        emit(key, json_to_blob_text(playfab["AwardedItems"]))
    for suffix, value in playfab.items():
        if suffix in ("Inventory", "Participation", "AwardedItems"):
            continue
        if isinstance(value, dict) and "raw_suffix" in value:
            emit(f"Playfab{suffix}", encode_unknown(value))

    girls = data.get("Girls", {})
    if "Unlocked" in girls:
        emit("GirlsUnlocked", json_to_blob_bits(girls["Unlocked"], min_bytes=11))
    if "PreviouslyUnlocked" in girls:
        emit("GirlsPreviouslyUnlocked", json_to_blob_bits(girls["PreviouslyUnlocked"], min_bytes=11))
    if "Current" in girls:
        emit("CurrentGirl", render_value(FieldSpec("int"), girls["Current"], nintendo))
    for name, girl in girls.items():
        if name in ("Unlocked", "PreviouslyUnlocked", "Current"):
            continue
        encode_girl_entry(f"Girl{name}", girl, emit, nintendo)

    jobs = data.get("Jobs", {})
    if "Available" in jobs:
        emit("AvailableJobs", render_value(FieldSpec("bitmask_int"), jobs["Available"], nintendo))
    for name, job in jobs.items():
        if name == "Available":
            continue
        encode_job_entry(f"Job{name}", job, emit, nintendo)

    for name, hobby in data.get("Hobby", {}).items():
        emit_object(f"Hobby{name}", hobby, HOBBY_FIELDS, emit, nintendo)

    flings = data.get("Flings", {})
    if "Unlocked" in flings:
        emit("UnlockedPFS", json_to_blob_bits(flings["Unlocked"], min_bytes=4))
    if "Purchased" in flings:
        emit("PlayfabFlingPurchases", render_value(FieldSpec("bitmask_long"), flings["Purchased"], nintendo))
    for fid, entry in flings.items():
        if fid in ("Unlocked", "Purchased"):
            continue
        d_val = entry.get("Date")
        if d_val is not None:
            emit(f"C{fid}D", str(json_to_timestamp(d_val, "utc")))
        emit(f"C{fid}P", json_to_fling_p(entry.get("Progress")))

    for aid, bits in data.get("Achievement", {}).items():
        emit(f"ACH{aid}", render_value(FieldSpec("bitmask_int"), bits, nintendo))

    events = data.get("Events", {})
    completed = events.get("Completed", {})
    if "2018" in completed:
        emit("Completed2018Events", render_value(FieldSpec("bitmask_long"), completed["2018"], nintendo))
    if "2019" in completed:
        emit("Completed2019Events", render_value(FieldSpec("bitmask_long"), completed["2019"], nintendo))
    if "2020" in completed:
        emit("Completed2020Events", render_value(FieldSpec("bitmask_long"), completed["2020"], nintendo))
    if "LTE" in completed:
        emit("CompletedEvents", render_value(FieldSpec("bitmask_blob"), completed["LTE"], nintendo))
    for suffix, value in completed.items():
        if suffix in ("2018", "2019", "2020", "LTE"):
            continue
        if isinstance(value, dict) and "raw_suffix" in value:
            emit(f"Completed{suffix}", encode_unknown(value))

    if "Current" in events:
        emit("EventID", render_value(FieldSpec("int"), events["Current"], nintendo))

    for lte_id, lte in events.get("LTE", {}).items():
        if "Tokens" in lte:
            emit(f"Event{lte_id}Tokens", render_value(FieldSpec("int"), lte["Tokens"], nintendo))
        for task_num, task in lte.get("Tasks", {}).items():
            for suffix, spec in TASK_FIELDS.items():
                if suffix in task:
                    emit(f"Task{task_num}{suffix}", render_value(spec, task[suffix], nintendo))

    for pe_id, pe in events.get("PE", {}).items():
        encode_pe(pe_id, pe, emit, nintendo)

    for key, spec in ROOT_SCALAR_FIELDS.items():
        if key in data:
            emit(key, render_value(spec, data[key], nintendo))

    rev_bonus_categories = {v: k for k, v in BONUS_CATEGORIES.items()}
    rev_bonus_sizes = {v: k for k, v in BONUS_SIZES.items()}
    rev_bonus_fields = {v: k for k, v in BONUS_FIELDS.items()}
    for cat_name, sizes in data.get("Bonuses", {}).items():
        cat = rev_bonus_categories.get(cat_name)
        if cat is None:
            continue
        for size_name, fields in sizes.items():
            size = rev_bonus_sizes.get(size_name)
            if size is None:
                continue
            for field_name, value in fields.items():
                field = rev_bonus_fields.get(field_name)
                if field is None:
                    continue
                emit(f".{cat}.{size}.{field}", f"{int(value)}i")

    for n, obj in data.get("Albums", {}).items():
        emit(f"album{n}", str(json_to_album_value(obj)))

    if "events.popupinfo" in data:
        emit("events.popupinfo", json.dumps(data["events.popupinfo"], separators=(",", ":")))

    for key in LAST_PES_ID_KEYS:
        if key in data:
            emit(key, data[key])

    for key, value in data.get("Unknown", {}).items():
        if key == "Task" and isinstance(value, dict):
            for task_num, task in value.items():
                for suffix in ("Start", "Complete", "Claimed"):
                    if suffix in task:
                        emit(f"Task{task_num}{suffix}", render_value(TASK_FIELDS[suffix], task[suffix], nintendo))
            continue
        if isinstance(value, dict) and "raw_suffix" in value:
            emit(key, encode_unknown(value))

    return "\n".join(lines)
