"""Step 05 — consolidate: per-character and per-location files, with EVOLUTION.

Owner's requirement (2026-08-23): "with timeline I will know what characters wear and
how they change physically and mentally during the course of the story — same with
locations." So each file carries a `journey`/`history` keyed to story time, built from
the timeline's worldlines and extraction's state changes.

05_01 gather      per entity: appearances, state changes, quotes, co-presence (code)
05_02 profile     LLM writes physical/mental/voice profile + arc FROM the gathered
                  evidence only (no book re-read)
05_03 emit        analysis/characters/<id>.json, analysis/locations/<id>.json
05_04 checks      every major character/location has a file; evolution non-empty (code)
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

from studio import db, paths, tracking

STEP_ID = "05"
NAME = "consolidate"

RUN_UNTIL = "05_04"
PROFILE_TOP_CHARACTERS = 8      # LLM profiles for the principals; rest get evidence-only
PROFILE_TOP_LOCATIONS = 8


def _load(book_dir: Path, name: str):
    return json.loads((book_dir / "analysis" / name).read_text(encoding="utf-8"))


def gather_characters(timeline: dict, extractions: list[dict]) -> dict[str, dict]:
    """Everything the extraction knows about each character, in story order."""
    scenes_by_key = {(s["chapter"], s["scene"]): s for s in timeline["scenes"]}
    dossiers: dict[str, dict] = {}
    for cid, segments in timeline["worldlines"].items():
        observed = [s for s in segments if s["kind"] == "observed"]
        if not observed:
            continue
        entity = timeline["characters"].get(cid, {"id": cid, "name": cid, "aliases": []})
        journey = []
        for segment in observed:
            scene = scenes_by_key.get((segment["chapter"], segment["scene"]), {})
            journey.append({
                "chapter": segment["chapter"], "scene": segment["scene"],
                "track": segment["track"], "day": segment["day"],
                "location_id": segment["location_id"],
                "time_of_day": scene.get("time_of_day", "UNKNOWN"),
                "what_happens": segment["evidence"],
            })
        dossiers[cid] = {
            "id": cid, "name": entity.get("name", cid),
            "aliases": entity.get("aliases", []), "role": entity.get("role", "minor"),
            "first_chapter": entity.get("first_chapter"),
            "appearances": len(observed),
            "locations_visited": list(dict.fromkeys(s["location_id"] for s in observed)),
            "journey": journey,
            "state_changes": [], "quotes": [], "companions": [],
        }
    _attach_state_and_quotes(dossiers, timeline, extractions)
    return dossiers


def _alias_lookup(timeline: dict) -> dict[str, str]:
    index = {}
    for cid, entity in timeline["characters"].items():
        for form in [entity.get("name", cid), *entity.get("aliases", [])]:
            index[form.strip().lower()] = cid
    return index


def _attach_state_and_quotes(dossiers: dict, timeline: dict, extractions: list[dict]):
    """State changes = HOW a character changes (injury, possession, knowledge...)."""
    index = _alias_lookup(timeline)
    day_of = {(s["chapter"], s["scene"]): (s["day"], s["track"])
              for s in timeline["scenes"]}
    for extraction in extractions:
        chapter = extraction["chapter"]
        for scene in extraction["scenes"]:
            day, track = day_of.get((chapter, scene["n"]), (None, "main"))
            for change in scene.get("state_changes", []):
                for name in change.get("characters", []):
                    cid = index.get(name.strip().lower())
                    if cid in dossiers:
                        dossiers[cid]["state_changes"].append({
                            "chapter": chapter, "scene": scene["n"], "day": day,
                            "track": track, "subtype": change.get("subtype"),
                            "change": change.get("summary"),
                            "evidence": (change.get("quote") or "")[:180]})
            for line in scene.get("dialogue", []):
                cid = index.get((line.get("speaker_text") or "").strip().lower())
                if cid in dossiers and len(dossiers[cid]["quotes"]) < 12:
                    dossiers[cid]["quotes"].append({
                        "chapter": chapter, "day": day,
                        "quote": (line.get("notable_quote") or "")[:220]})
    for cid, dossier in dossiers.items():
        seen = Counter()
        for step in dossier["journey"]:
            for scene in timeline["scenes"]:
                if (scene["chapter"], scene["scene"]) == (step["chapter"], step["scene"]):
                    seen.update(c for c in scene["characters"] if c != cid)
        dossier["companions"] = [{"id": other, "shared_scenes": n}
                                 for other, n in seen.most_common(6)]


def gather_locations(timeline: dict) -> dict[str, dict]:
    """Per place: its scenes, who was there, and what changed there."""
    by_location: dict[str, dict] = {}
    for scene in timeline["scenes"]:
        lid = scene["location_id"]
        if not lid:
            continue
        record = timeline["locations"].get(lid, {"id": lid, "name": lid})
        entry = by_location.setdefault(lid, {
            "id": lid, "name": record.get("name", lid),
            "aliases": record.get("aliases", []), "region": record.get("region"),
            "lat": record.get("lat"), "lon": record.get("lon"),
            "approximate": record.get("approximate", False),
            "scenes": [], "visitors": [], "state_changes": [],
        })
        entry["scenes"].append({
            "chapter": scene["chapter"], "scene": scene["scene"],
            "day": scene["day"], "track": scene["track"],
            "time_of_day": scene.get("time_of_day"), "what_happens": scene["summary"],
            "characters": scene["characters"],
        })
        for change in scene.get("state_changes", []):
            entry["state_changes"].append({
                "chapter": scene["chapter"], "day": scene["day"],
                "subtype": change.get("subtype"), "change": change.get("summary")})
    for entry in by_location.values():
        counts = Counter(c for s in entry["scenes"] for c in s["characters"])
        entry["visitors"] = [{"id": cid, "scenes": n} for cid, n in counts.most_common(10)]
        entry["first_appearance"] = min(s["chapter"] for s in entry["scenes"])
    return by_location


def check(characters: dict, locations: dict) -> list[str]:
    problems = []
    if not characters:
        problems.append("no character dossiers built")
    for cid, dossier in characters.items():
        if not dossier["journey"]:
            problems.append(f"character {cid} has an empty journey")
    for lid, entry in locations.items():
        if not entry["scenes"]:
            problems.append(f"location {lid} has no scenes")
    return problems


def run(codex_id: str) -> None:
    conn = db.get_connection()
    book_dir = paths.book_dir(codex_id)
    out = book_dir / "analysis"
    char_dir, loc_dir = out / "characters", out / "locations"
    tracker = tracking.Tracker(conn, codex_id, "analysis")
    if char_dir.exists() and any(char_dir.glob("*.json")):
        print(f"[{STEP_ID}] {NAME}: character/location files exist — skipping (cached)")
        return

    timeline = _load(book_dir, "timeline.json")
    extractions = [json.loads(p.read_text(encoding="utf-8"))
                   for p in sorted((out / "extraction").glob("ch_*.json"))]
    print(f"[{STEP_ID}] {NAME}: run_id={tracker.run_id}")

    with tracker.step("05_01"):
        characters = gather_characters(timeline, extractions)
        locations = gather_locations(timeline)
    print(f"  05_01 gather: {len(characters)} characters, {len(locations)} locations")

    with tracker.step("05_02"):
        from agents import profile_writer
        ranked = sorted(characters.values(), key=lambda d: -d["appearances"])
        for dossier in ranked[:PROFILE_TOP_CHARACTERS]:
            usage = {}
            try:
                dossier["profile"] = profile_writer.character_profile(
                    dossier, usage=usage).model_dump()
                tracker.log(f"profile {dossier['id']} ({usage.get('total_tokens')} tok)",
                            step_id="05_02")
                print(f"         profiled {dossier['id']}")
            except Exception as exc:
                tracker.log(f"profile {dossier['id']} failed: {exc}",
                            level="WARNING", step_id="05_02")
        ranked_locs = sorted(locations.values(), key=lambda e: -len(e["scenes"]))
        for entry in ranked_locs[:PROFILE_TOP_LOCATIONS]:
            usage = {}
            try:
                entry["profile"] = profile_writer.location_profile(
                    entry, usage=usage).model_dump()
                print(f"         profiled {entry['id']}")
            except Exception as exc:
                tracker.log(f"location profile {entry['id']} failed: {exc}",
                            level="WARNING", step_id="05_02")
    if RUN_UNTIL < "05_03":
        return

    with tracker.step("05_03"):
        char_dir.mkdir(parents=True, exist_ok=True)
        loc_dir.mkdir(parents=True, exist_ok=True)
        for cid, dossier in characters.items():
            (char_dir / f"{cid}.json").write_text(
                json.dumps(dossier, ensure_ascii=False, indent=2), encoding="utf-8")
        for lid, entry in locations.items():
            (loc_dir / f"{lid}.json").write_text(
                json.dumps(entry, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  05_03 emit: {len(characters)} character files, {len(locations)} location files")

    with tracker.step("05_04"):
        problems = check(characters, locations)
        for problem in problems[:10]:
            tracker.log(f"check: {problem}", level="WARNING", step_id="05_04")
    print(f"  05_04 checks: {len(problems)} problem(s)")
