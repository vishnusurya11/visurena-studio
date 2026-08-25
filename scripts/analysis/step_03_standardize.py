"""Step 03 — standardize: extracted surface forms -> canonical entities.

03_01 collect     gather every character/location surface form from extraction (code)
03_02 resolve     LLM merge-judge -> canonical entities + aliases + COORDINATES
03_03 remap       tag every scene with canonical ids (code)
03_04 checks      every scene resolved; no orphan ids; coords present (code)

Never re-reads the book — operates on extraction output only (owner's design).
Output: analysis/registry.json (+ per-scene canonical ids in analysis/scenes.json)
"""

from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path

from studio import db, paths, screenformat, tracking

STEP_ID = "03"
NAME = "standardize"

RUN_UNTIL = "03_04"
MAX_FORMS = 220          # cap surface forms sent to the resolver (cost guard)

_WS = re.compile(r"[^a-z0-9 ]+")


def _norm(text: str) -> str:
    return _WS.sub("", (text or "").lower()).strip()


def load_extractions(book_dir: Path) -> list[dict]:
    path = book_dir / "analysis" / "extraction"
    return [json.loads(p.read_text(encoding="utf-8"))
            for p in sorted(path.glob("ch_*.json"))]


def collect_forms(extractions: list[dict]) -> tuple[list[dict], list[dict]]:
    """Surface forms with the chapters they appear in and a sample context."""
    chars: dict[str, dict] = defaultdict(lambda: {"chapters": set(), "sample": "", "count": 0})
    locs: dict[str, dict] = defaultdict(lambda: {"chapters": set(), "sample": "", "count": 0})
    for ex in extractions:
        ch = ex["chapter"]
        for scene in ex["scenes"]:
            loc = scene.get("location_text") or ""
            if loc:
                entry = locs[loc]
                entry["chapters"].add(ch)
                entry["count"] += 1
                entry["sample"] = entry["sample"] or scene.get("summary", "")[:120]
            for person in scene.get("characters", []):
                name = person.get("name_text") or ""
                if not name:
                    continue
                entry = chars[name]
                entry["chapters"].add(ch)
                entry["count"] += 1
                entry["sample"] = entry["sample"] or scene.get("summary", "")[:120]
    return _rank(chars, "name_text"), _rank(locs, "location_text")


def _rank(forms: dict, key: str) -> list[dict]:
    """Most-mentioned first, capped — cost guard for the resolver prompt."""
    items = sorted(forms.items(), key=lambda kv: -kv[1]["count"])[:MAX_FORMS]
    return [{key: text, "chapters": sorted(v["chapters"]), "mentions": v["count"],
             "sample": v["sample"]} for text, v in items]


def build_alias_index(registry: dict) -> tuple[dict, dict]:
    """Normalized surface form -> canonical id, for characters and locations."""
    char_index, loc_index = {}, {}
    for entity in registry["characters"]:
        for form in [entity["name"], *entity["aliases"]]:
            char_index[_norm(form)] = entity["id"]
    for entity in registry["locations"]:
        for form in [entity["name"], *entity["aliases"]]:
            loc_index[_norm(form)] = entity["id"]
    return char_index, loc_index


def _run_starts_at(words: list[str], tokens: list[str]) -> bool:
    """Do `tokens` appear as a contiguous run of whole words inside `words`?"""
    span = len(tokens)
    return any(words[i:i + span] == tokens for i in range(len(words) - span + 1))


def _match(text: str, index: dict) -> str | None:
    """Exact normalized match, else the longest alias present as WHOLE WORDS.

    Two rules, both learned the hard way in the 2026-08-23 audit:

    1. **Words, not letters.** This did raw substring containment, so "me" matched
       inside "medical", "men" inside "regiment" and "government", and the narrator's
       one-letter alias "i" matched any form containing the letter i. 298 of the book's
       902 character references — a third — were silently assigned to the wrong person.
    2. **A one-word alias only ever matches exactly.** Whole-word matching alone still
       lets "Young" claim "a young girl" and "men" claim "the two men". A single word
       carries too little identity to be recognised inside a phrase it did not write; if
       the form is not the alias, it is somebody else.

    An unmatched form returns None, and that gap is the honest answer — a walk-on
    ("a railway porter") has no canonical identity to find."""
    key = _norm(text)
    if not key:
        return None
    if key in index:
        return index[key]
    words = key.split()
    best = None
    for alias, entity in index.items():
        tokens = alias.split()
        if len(tokens) < 2 or not _run_starts_at(words, tokens):
            continue
        if best is None or len(tokens) > best[0]:
            best = (len(tokens), entity)
    return best[1] if best else None


def remap_scenes(extractions: list[dict], registry: dict) -> list[dict]:
    """Flat scene list tagged with canonical ids — the timeline's input."""
    char_index, loc_index = build_alias_index(registry)
    scenes = []
    for ex in extractions:
        for scene in ex["scenes"]:
            present = []
            for person in scene.get("characters", []):
                if person.get("presence") != "present":
                    continue
                cid = _match(person.get("name_text", ""), char_index)
                if cid and cid not in present:
                    present.append(cid)
            scenes.append({
                "chapter": ex["chapter"],
                "scene": scene["n"],
                "type": scene.get("type", "scene"),
                "location_id": _match(scene.get("location_text", ""), loc_index),
                "location_text": scene.get("location_text", ""),
                "int_ext": screenformat.normalize_int_ext(scene.get("int_ext")),
                "characters": present,
                "story_day": scene.get("story_day"),
                "time_of_day": scene.get("time_of_day", "UNKNOWN"),
                "frame": scene.get("frame"),
                "summary": scene.get("summary", ""),
                "time_evidence": scene.get("time_evidence", []),
                "state_changes": scene.get("state_changes", []),
                "para_start": scene.get("para_start"),
                "para_end": scene.get("para_end"),
            })
    return scenes


def check(registry: dict, scenes: list[dict]) -> list[str]:
    problems = []
    ids = {loc["id"] for loc in registry["locations"]}
    if not registry["characters"]:
        problems.append("no canonical characters resolved")
    for loc in registry["locations"]:
        if loc["lat"] == 0 and loc["lon"] == 0:
            problems.append(f"location {loc['id']} has no coordinates")
    unresolved = [s for s in scenes if s["location_id"] is None]
    if len(unresolved) > len(scenes) * 0.35:
        problems.append(f"{len(unresolved)}/{len(scenes)} scenes have no location id")
    for scene in scenes:
        if scene["location_id"] and scene["location_id"] not in ids:
            problems.append(f"orphan location id {scene['location_id']}")
    return problems


def run(codex_id: str) -> None:
    conn = db.get_connection()
    book_dir = paths.book_dir(codex_id)
    out_dir = book_dir / "analysis"
    registry_path = out_dir / "registry.json"
    scenes_path = out_dir / "scenes.json"
    tracker = tracking.Tracker(conn, codex_id, "analysis")

    if registry_path.exists() and scenes_path.exists():
        print(f"[{STEP_ID}] {NAME}: registry.json + scenes.json exist — skipping (cached)")
        return

    extractions = load_extractions(book_dir)
    print(f"[{STEP_ID}] {NAME}: {len(extractions)} chapters  run_id={tracker.run_id}")

    with tracker.step("03_01"):
        char_forms, loc_forms = collect_forms(extractions)
    print(f"  03_01 collect: {len(char_forms)} character forms, {len(loc_forms)} location forms")

    with tracker.step("03_02"):
        from agents import entity_resolver
        usage = {}
        chars = entity_resolver.resolve_characters(char_forms, usage=usage)
        tracker.log(f"characters resolved: {len(chars.characters)} "
                    f"({usage.get('total_tokens')} tokens)", step_id="03_02")
        usage2 = {}
        locs = entity_resolver.resolve_locations(loc_forms, usage=usage2)
        tracker.log(f"locations resolved: {len(locs.locations)} "
                    f"({usage2.get('total_tokens')} tokens)", step_id="03_02")
        registry = {"characters": [c.model_dump() for c in chars.characters],
                    "locations": [loc.model_dump() for loc in locs.locations]}
    print(f"  03_02 resolve: {len(registry['characters'])} characters, "
          f"{len(registry['locations'])} locations "
          f"({usage.get('total_tokens', 0) + usage2.get('total_tokens', 0)} tokens)")
    for c in registry["characters"][:8]:
        print(f"         {c['id']:<20} {c['role']:<12} aliases={len(c['aliases'])}")
    if RUN_UNTIL < "03_03":
        return

    with tracker.step("03_03"):
        scenes = remap_scenes(extractions, registry)
        registry_path.write_text(json.dumps(registry, ensure_ascii=False, indent=2),
                                 encoding="utf-8")
        scenes_path.write_text(json.dumps(scenes, ensure_ascii=False, indent=2),
                               encoding="utf-8")
    resolved = sum(1 for s in scenes if s["location_id"])
    print(f"  03_03 remap: {len(scenes)} scenes, {resolved} with canonical location")
    if RUN_UNTIL < "03_04":
        return

    with tracker.step("03_04"):
        problems = check(registry, scenes)
        for problem in problems:
            tracker.log(f"check: {problem}", level="WARNING", step_id="03_04")
    print(f"  03_04 checks: {len(problems)} problem(s)" +
          ("" if not problems else f" — {problems[:3]}"))
