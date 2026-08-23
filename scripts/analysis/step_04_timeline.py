"""Step 04 — timeline: scenes -> story-time worldlines (who is where, when).

Algorithm follows docs/analysis/research/10_timeline_solving.md (TLEX partitioning +
story-day cascade + worldline assembly + alibi-query contradiction sweep). Deterministic
core; no LLM calls — every claim traces to extracted evidence.

04_01 partition   split into narrative TRACKS (main frame vs embedded flashback)
04_02 dayaxis     merge per-chapter story_day counters into a track-global day axis
04_03 worldlines  per character: observed / in-transit / presumed / unknown segments
04_04 contradict  bilocation + travel-feasibility sweep
04_05 emit        analysis/timeline.json  (the video's input)
"""

from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from pathlib import Path

from studio import db, paths, tracking

STEP_ID = "04"
NAME = "timeline"

RUN_UNTIL = "04_05"

# Travel feasibility: 1881 hansom cab ~8 mph; long-distance = train/ship, unbounded here.
CAB_MPH = 8.0
MAX_LOCAL_MILES = 40.0     # beyond this, assume rail/ship and skip the feasibility check


def _load(book_dir: Path, name: str):
    return json.loads((book_dir / "analysis" / name).read_text(encoding="utf-8"))


# --- 04_01 partition -------------------------------------------------------------


def partition(scenes: list[dict]) -> list[dict]:
    """Assign each scene a narrative track: 'main' (the telling frame) or
    'flashback' (embedded narration — TLEX subordinated timeline).

    Signals, in order: an explicit frame flag from extraction; else the region of
    the scene's location (a run of non-London scenes inside a London book is the
    embedded tale)."""
    for scene in scenes:
        frame = scene.get("frame")
        scene["track"] = "flashback" if frame else "main"
        scene["frame_type"] = (frame or {}).get("type") if frame else None
    return scenes


def apply_region_track(scenes: list[dict], locations: dict) -> list[dict]:
    """Track assignment at CHAPTER granularity — a book's embedded tale occupies whole
    chapters (Part II), while stray non-home locations inside a frame chapter are just
    backstory mentions (Watson's Afghanistan) and must NOT flip the chapter's track."""
    for scene in scenes:
        scene["region"] = locations.get(scene["location_id"], {}).get("region") or "other"
    regions = [s["region"] for s in scenes if s["region"] != "other"]
    home = max(set(regions), key=regions.count, default="london")

    away_share: dict[int, float] = {}
    for chapter in {s["chapter"] for s in scenes}:
        in_ch = [s for s in scenes if s["chapter"] == chapter]
        known = [s for s in in_ch if s["region"] != "other"]
        flagged = sum(1 for s in in_ch if s.get("frame"))
        away = sum(1 for s in known if s["region"] != home)
        away_share[chapter] = max(away / len(known) if known else 0.0,
                                  flagged / len(in_ch))
    for scene in scenes:
        scene["track"] = "flashback" if away_share[scene["chapter"]] > 0.5 else "main"
    return scenes


# --- 04_02 day axis --------------------------------------------------------------


def _new_day(prev: dict, scene: dict) -> bool:
    """Story-day cascade (film continuity + fan-chronology practice):
    explicit offset > NIGHT->DAY transition > per-chapter counter > continuity."""
    advancing = ("next morning", "next day", "following day", "following morning",
                 "days later", "day later", "weeks later", "week later", "years later",
                 "year later", "months later", "the morrow", "that night", "next evening",
                 "the following", "a fortnight", "some days", "few days")
    if any(w in (ev.get("text") or "").lower()
           for ev in scene.get("time_evidence", []) for w in advancing):
        return True
    if prev.get("time_of_day") == "NIGHT" and scene.get("time_of_day") == "DAY":
        return True
    if scene["chapter"] != prev["chapter"]:
        prev_day, day = prev.get("story_day"), scene.get("story_day")
        if day is not None and prev_day is not None and day != prev_day:
            return True
    elif scene.get("story_day") is not None and prev.get("story_day") is not None:
        return scene["story_day"] != prev["story_day"]
    return False


def build_day_axis(scenes: list[dict]) -> list[dict]:
    """Per-track global day numbers; every scene also gets a monotonic `t` position
    (day + fraction from time_of_day) — the video's clock."""
    day_by_track = defaultdict(lambda: 1)
    prev_by_track: dict[str, dict] = {}
    fraction = {"DAY": 0.45, "NIGHT": 0.85, "UNKNOWN": 0.6}
    for scene in scenes:
        track = scene["track"]
        prev = prev_by_track.get(track)
        if prev is not None and _new_day(prev, scene):
            day_by_track[track] += 1
        scene["day"] = day_by_track[track]
        scene["t"] = scene["day"] + fraction.get(scene.get("time_of_day"), 0.6)
        prev_by_track[track] = scene
    return scenes


# --- 04_03 worldlines ------------------------------------------------------------


def drop_narrator_contamination(scenes: list[dict]) -> list[dict]:
    """A frame narrator recounting an embedded tale is NOT present in it.

    Extraction tags the narrating "I" inside Part II, which would put Watson in Utah.
    Rule: if a character is overwhelmingly a creature of one track (>=5x the
    observations) and appears in only a small minority of the other track's scenes,
    their minority-track appearances are narration artifacts, not presence."""
    counts: dict[str, Counter] = defaultdict(Counter)
    for scene in scenes:
        for character in scene["characters"]:
            counts[character][scene["track"]] += 1
    track_sizes = Counter(scene["track"] for scene in scenes)
    contaminated = set()

    # (a) lopsided presence = a mention/narration artifact on the minority track
    for character, per_track in counts.items():
        for track, seen in per_track.items():
            other = sum(v for t, v in per_track.items() if t != track)
            share = seen / max(1, track_sizes[track])
            if other >= 5 * seen and share < 0.25:
                contaminated.add((character, track))

    # (b) the FRAME NARRATOR is never inside the tale told to them. The main track's
    # most-present character is the narrator ("I"); extraction tags that pronoun
    # inside embedded narration, which would put Watson in Utah.
    main_counts = Counter({c: t["main"] for c, t in counts.items() if t.get("main")})
    if main_counts:
        narrator, _ = main_counts.most_common(1)[0]
        for track in track_sizes:
            if track != "main" and counts[narrator].get(track):
                if counts[narrator][track] < counts[narrator]["main"]:
                    contaminated.add((narrator, track))
    if contaminated:
        for scene in scenes:
            scene["characters"] = [c for c in scene["characters"]
                                   if (c, scene["track"]) not in contaminated]
    return scenes


def build_worldlines(scenes: list[dict]) -> dict[str, list[dict]]:
    """Per character, ordered segments. Observed = the text put them there.
    Between observations: in-transit (location changed) or presumed (stayed)."""
    observed: dict[str, list[dict]] = defaultdict(list)
    for index, scene in enumerate(scenes):
        if not scene["location_id"]:
            continue
        for character in scene["characters"]:
            observed[character].append({
                "scene_index": index, "track": scene["track"], "t": scene["t"],
                "day": scene["day"], "location_id": scene["location_id"],
                "chapter": scene["chapter"], "scene": scene["scene"],
                "summary": scene["summary"],
            })
    worldlines = {}
    for character, points in observed.items():
        points.sort(key=lambda p: (p["track"] != "main", p["t"], p["scene_index"]))
        worldlines[character] = _segments(points)
    return worldlines


def _segments(points: list[dict]) -> list[dict]:
    segments = []
    for i, point in enumerate(points):
        segments.append({
            "kind": "observed", "track": point["track"],
            "t_start": point["t"], "t_end": point["t"] + 0.12,
            "location_id": point["location_id"], "day": point["day"],
            "chapter": point["chapter"], "scene": point["scene"],
            "evidence": point["summary"][:160], "confidence": "attested",
        })
        if i + 1 < len(points):
            nxt = points[i + 1]
            if nxt["track"] != point["track"]:
                continue
            gap_start, gap_end = point["t"] + 0.12, nxt["t"]
            if gap_end <= gap_start:
                continue
            moved = nxt["location_id"] != point["location_id"]
            segments.append({
                "kind": "in-transit" if moved else "presumed",
                "track": point["track"], "t_start": gap_start, "t_end": gap_end,
                "location_id": point["location_id"],
                "to_location_id": nxt["location_id"] if moved else None,
                "day": point["day"], "chapter": point["chapter"],
                "evidence": "", "confidence": "inferred" if moved else "presumed",
            })
    return segments


# --- 04_04 contradictions --------------------------------------------------------


def _miles(a: dict, b: dict) -> float:
    """Great-circle distance between two location records."""
    lat1, lon1, lat2, lon2 = map(math.radians, (a["lat"], a["lon"], b["lat"], b["lon"]))
    h = (math.sin((lat2 - lat1) / 2) ** 2
         + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2)
    return 3958.8 * 2 * math.asin(math.sqrt(h))


def find_contradictions(worldlines: dict, locations: dict) -> list[dict]:
    """Bilocation (same character, same time, two places) + travel feasibility
    (the alibi query: could they physically have made the trip?)."""
    problems = []
    for character, segments in worldlines.items():
        observed = [s for s in segments if s["kind"] == "observed"]
        for a, b in zip(observed, observed[1:]):
            if a["track"] != b["track"]:
                continue
            if a["location_id"] != b["location_id"] and b["t_start"] < a["t_end"]:
                problems.append({"type": "bilocation", "character": character,
                                 "a": _ref(a), "b": _ref(b),
                                 "note": "two locations at overlapping story time"})
                continue
            loc_a, loc_b = locations.get(a["location_id"]), locations.get(b["location_id"])
            if not (loc_a and loc_b) or a["location_id"] == b["location_id"]:
                continue
            miles = _miles(loc_a, loc_b)
            hours = max(0.0, (b["t_start"] - a["t_end"])) * 24
            if miles <= MAX_LOCAL_MILES and hours * CAB_MPH < miles:
                problems.append({
                    "type": "travel-infeasible", "character": character,
                    "a": _ref(a), "b": _ref(b),
                    "note": f"{miles:.1f} mi in {hours:.1f} h exceeds {CAB_MPH} mph"})
    return problems


def _ref(segment: dict) -> dict:
    return {k: segment[k] for k in ("chapter", "scene", "day", "location_id")}


# --- runner ----------------------------------------------------------------------


def solve(scenes: list[dict], registry: dict) -> dict:
    locations = {loc["id"]: loc for loc in registry["locations"]}
    scenes = apply_region_track(partition(scenes), locations)
    scenes = build_day_axis(scenes)
    scenes = drop_narrator_contamination(scenes)
    worldlines = build_worldlines(scenes)
    contradictions = find_contradictions(worldlines, locations)
    tracks = {}
    for track in {s["track"] for s in scenes}:
        in_track = [s for s in scenes if s["track"] == track]
        tracks[track] = {"days": max(s["day"] for s in in_track),
                         "scenes": len(in_track),
                         "chapters": sorted({s["chapter"] for s in in_track})}
    return {"tracks": tracks, "scenes": scenes, "worldlines": worldlines,
            "contradictions": contradictions,
            "locations": locations,
            "characters": {c["id"]: c for c in registry["characters"]}}


def run(codex_id: str) -> None:
    conn = db.get_connection()
    book_dir = paths.book_dir(codex_id)
    out_path = book_dir / "analysis" / "timeline.json"
    tracker = tracking.Tracker(conn, codex_id, "analysis")
    if out_path.exists():
        print(f"[{STEP_ID}] {NAME}: timeline.json exists — skipping (cached)")
        return

    scenes = _load(book_dir, "scenes.json")
    registry = _load(book_dir, "registry.json")
    print(f"[{STEP_ID}] {NAME}: {len(scenes)} scenes  run_id={tracker.run_id}")

    with tracker.step("04_01"), tracker.step("04_02"), tracker.step("04_03"), \
            tracker.step("04_04"), tracker.step("04_05"):
        timeline = solve(scenes, registry)
        out_path.write_text(json.dumps(timeline, ensure_ascii=False, indent=2),
                            encoding="utf-8")

    for track, info in sorted(timeline["tracks"].items()):
        print(f"  track {track:<10} {info['days']:>3} story days, "
              f"{info['scenes']:>3} scenes, chapters {info['chapters']}")
        tracker.log(f"track {track}: {info['days']} days, {info['scenes']} scenes",
                    step_id="04_02")
    movers = sorted(timeline["worldlines"].items(), key=lambda kv: -len(kv[1]))[:8]
    print(f"  worldlines: {len(timeline['worldlines'])} characters")
    for character, segments in movers:
        places = len({s["location_id"] for s in segments})
        print(f"         {character:<20} {len(segments):>3} segments across {places} places")
    print(f"  contradictions: {len(timeline['contradictions'])}")
    for problem in timeline["contradictions"][:5]:
        tracker.log(f"{problem['type']}: {problem['character']} {problem['note']}",
                    level="WARNING", step_id="04_04")
        print(f"         {problem['type']}: {problem['character']} — {problem['note']}")
