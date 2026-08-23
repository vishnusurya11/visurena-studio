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
import re
from datetime import date, timedelta
from collections import Counter, defaultdict
from pathlib import Path

from studio import db, paths, storytime, tracking

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


_YEAR_RE = re.compile(r"\b(1[6-9]\d{2})\b")


def _stated_year(scene: dict) -> int | None:
    """An absolute year the TEXT states, numeric OR spelled out
    ("August 4th, 1860"; "eighteen hundred and forty-seven")."""
    for evidence in scene.get("time_evidence", []):
        if evidence.get("type") != "date":
            continue
        text = evidence.get("text") or ""
        match = _YEAR_RE.search(text)
        if match:
            return int(match.group(1))
        spelled = re.search(r"((?:eighteen|nineteen|seventeen)[\s-]+hundred"
                            r"(?:[\s-]+and)?(?:[\s-]+[a-z-]+)*)", text.lower())
        if spelled:
            value = storytime.words_to_number(spelled.group(1))
            if value and 1600 <= value <= 1999:
                return value
    return None


def _plausible_years(scenes: list[dict]) -> set[int]:
    """Years the NARRATIVE happens in, not every year a character mentions.

    Defect found 2026-08-23: a line of dialogue about "in 1642" anchored a scene to
    the seventeenth century. Keep only years clustered with the rest — an aside about
    a distant century is not this book's clock."""
    stated = [y for y in (_stated_year(s) for s in scenes) if y]
    if not stated:
        return set()
    ordered = sorted(stated)
    median = ordered[len(ordered) // 2]
    return {y for y in stated if abs(y - median) <= 60}


def _date_anchor(scene: dict, allowed_years: set[int], context_year: int | None):
    """A real calendar date this scene STATES, if any ("August 4th, 1860")."""
    for evidence in scene.get("time_evidence", []):
        if evidence.get("type") != "date":
            continue
        parsed = storytime.parse_date(evidence.get("text") or "",
                                      default_year=context_year)
        if parsed and parsed.year in allowed_years:
            return parsed, evidence["text"]
    return None, None


def _scene_offset(scene: dict):
    """The largest clock-advancing duration this scene states ("Three weeks")."""
    best = None
    for evidence in scene.get("time_evidence", []):
        if evidence.get("type") not in ("duration", "date", "ordering"):
            continue
        span = storytime.parse_offset(evidence.get("text") or "")
        if span and (best is None or span > best[0]):
            best = (span, evidence["text"])
    return best or (None, None)


WINDOW = 3          # scenes of context handed to the gap filler on each side


def fill_location_gaps(scenes: list[dict], locations: dict) -> int:
    """Give every scene a location and a time, asking an agent for the ones the
    deterministic pipeline could not resolve. Returns how many it filled.

    Code interpolates an hour happily but can never interpolate a PLACE — the midpoint
    of two locations is meaningless. An agent reading the scene and the surrounding
    sequence can, so gaps (and only gaps) go to it.

    Owner decision 2026-08-23: **every scene must end up with a location and a time.**
    Downstream consumers need a place per scene, so the agent always commits rather
    than abstaining. Guardrails remain: an id outside the canonical list is refused
    rather than trusted, an agent failure leaves the gap rather than crashing, and
    everything filled is marked `inferred` with the reasoning stored beside it, so
    inference is always separable from stated evidence."""
    from agents import gap_filler

    for scene in scenes:
        scene.setdefault("location_confidence",
                         "stated" if scene.get("location_id") else "unknown")
    filled = 0
    for index, scene in enumerate(scenes):
        needs_place = not scene.get("location_id")
        needs_time = scene.get("time_of_day") in (None, "UNKNOWN")
        if not (needs_place or needs_time):
            continue
        before = [s for s in scenes[max(0, index - WINDOW):index]]
        after = [s for s in scenes[index + 1:index + 1 + WINDOW]]
        try:
            placement = gap_filler.place(scene, before, after, locations)
        except Exception as exc:                       # never let a gap break the run
            scene["location_reasoning"] = f"agent unavailable: {exc}"
            continue
        scene["location_reasoning"] = placement.reasoning
        if needs_place:
            if placement.location_id in locations:
                scene["location_id"] = placement.location_id
                scene["location_confidence"] = "inferred"
                scene["location_inference_confidence"] = placement.confidence
                filled += 1
            else:
                scene["location_confidence"] = "unknown"   # refuse an invented id
        if needs_time and placement.time_of_day in ("DAY", "NIGHT"):
            scene["time_of_day"] = placement.time_of_day
            scene["clock_confidence"] = "inferred"
    return filled


def assign_time_of_day(scenes: list[dict]) -> list[dict]:
    """Keep the precision the book gives.

    Extraction records DAY/NIGHT (the film-breakdown binary), but the text is finer —
    "noon exactly", "after ten at night", "That very evening" — and 9 scenes were
    marked UNKNOWN while carrying exactly such evidence. Each scene now gets
    `clock` (a readable label), `hour` (for ordering and daylight), and a `time_of_day`
    repaired from the evidence when extraction left it UNKNOWN. A scene with no
    evidence inherits the previous scene's clock only within the same day."""
    for scene in scenes:
        phrases = [e.get("text", "") for e in scene.get("time_evidence", [])
                   if e.get("type") in ("time_of_day", "date", "ordering")]
        parsed = storytime.finest_time_of_day(phrases)
        if parsed is None and scene.get("time_of_day") in ("DAY", "NIGHT"):
            parsed = ("daytime", 12) if scene["time_of_day"] == "DAY" else ("night", 22)
            scene["clock_confidence"] = "stated"
        elif parsed is not None:
            scene["clock_confidence"] = "stated"
        else:
            scene["clock_confidence"] = "unknown"
        scene["hour"] = parsed[1] if parsed else None
        scene["clock"] = parsed[0] if parsed else None

    by_day: dict[tuple[str, int], list[dict]] = defaultdict(list)
    for scene in scenes:
        by_day[(scene["track"], scene.get("day", 0))].append(scene)
    for in_day in by_day.values():
        _infer_hours_within_day(in_day)

    for scene in scenes:
        if scene["hour"] is not None:
            scene["clock"] = scene["clock"] or storytime._label_for_hour(scene["hour"])
            scene["time_of_day"] = storytime.daylight(scene["hour"])
    return scenes


def _infer_hours_within_day(in_day: list[dict]) -> None:
    """Place unstated scenes by where they SIT between the stated ones.

    A scene between a morning scene and an evening one is an afternoon scene; scenes
    after the last stated time drift later; scenes before the first drift earlier.
    Never crosses a day boundary (each day is inferred independently), and a stated
    hour is never overwritten."""
    known = [(i, s["hour"]) for i, s in enumerate(in_day) if s["hour"] is not None]
    if not known:
        return
    for (i0, h0), (i1, h1) in zip(known, known[1:]):      # between two stated times
        if i1 - i0 < 2:
            continue
        span = max(h1 - h0, 0)
        for offset in range(1, i1 - i0):
            scene = in_day[i0 + offset]
            step = span * offset / (i1 - i0)
            scene["hour"] = min(23, int(round(h0 + max(step, offset * 0.5))))
            scene["clock_confidence"] = "inferred"
    first_index, first_hour = known[0]
    for back, scene in enumerate(reversed(in_day[:first_index]), start=1):
        scene["hour"] = max(0, first_hour - back)
        scene["clock_confidence"] = "inferred"
    last_index, last_hour = known[-1]
    for forward, scene in enumerate(in_day[last_index + 1:], start=1):
        scene["hour"] = min(23, last_hour + forward)
        scene["clock_confidence"] = "inferred"


def assign_dates(scenes: list[dict]) -> list[dict]:
    """Real calendar dates from the book's own words (owner: no artificial 'Day N').

    Only dates the text STATES are anchors. Scenes between two anchors are
    INTERPOLATED across the gap and marked approximate; scenes outside any anchor
    pair carry only what the text gives (a month/day, or nothing).

    Deliberately NOT additive chaining: summing every duration a scene mentions
    ("for a week", "some weeks" — usually describing the past, not advancing the
    clock) pushed A Study in Scarlet into 1912 on the first attempt. The research is
    explicit: no arithmetic across vague gaps. Interpolation states less and is right.

    Each scene records `date_confidence`: `stated` | `approx` | `unknown`."""
    allowed_years = _plausible_years(scenes)
    by_track: dict[str, list[dict]] = defaultdict(list)
    for scene in scenes:
        scene["date"] = None
        scene["date_display"] = None
        scene["date_confidence"] = "unknown"
        scene["date_evidence"] = None
        by_track[scene["track"]].append(scene)

    for track, sequence in by_track.items():
        anchors = []
        for index, scene in enumerate(sequence):
            stated, source = _date_anchor(scene, allowed_years, None)
            if stated:
                scene["date"] = stated.isoformat()
                scene["date_confidence"] = "stated"
                scene["date_evidence"] = source
                anchors.append((index, stated))
        _interpolate(sequence, anchors)

    # A bare year mentioned in narration ("the year 1878", when Watson took his
    # degree) dates a MEMORY, not the scene — using it as an anchor put the London
    # investigation in 1878. Where the text gives only a day and month ("the 4th of
    # March"), show exactly that and say the year is unstated.
    for sequence in by_track.values():
        if any(s["date_confidence"] == "stated" for s in sequence):
            continue
        anchor = next(((s, _month_day(s)) for s in sequence if _month_day(s)), None)
        if anchor is None:
            continue
        anchor_scene, partial = anchor
        base_day = anchor_scene["day"]
        try:
            base = date(1900, MONTH_NUMBERS[partial.split()[-1].lower()],
                        int(partial.split()[0]) if partial.split()[0].isdigit() else 1)
        except (KeyError, ValueError):
            continue
        for scene in sequence:
            shifted = base + timedelta(days=scene["day"] - base_day)
            scene["date_display"] = f"{shifted.day} {shifted.strftime('%B')}"
            scene["date_confidence"] = ("stated-partial" if scene is anchor_scene
                                        else "approx-partial")
            scene["date_evidence"] = (f"{partial} stated; year not given in the text"
                                      if scene is anchor_scene
                                      else f"day {scene['day'] - base_day:+d} from {partial}")
    return scenes


MONTH_NUMBERS = {m: i + 1 for i, m in enumerate(
    ["january", "february", "march", "april", "may", "june", "july",
     "august", "september", "october", "november", "december"])}


_MONTH_DAY = re.compile(
    r"\b(?:(\d{1,2})(?:st|nd|rd|th)?\s+of\s+)?"
    r"(january|february|march|april|may|june|july|august|september|october|"
    r"november|december)\b(?:\s+(\d{1,2})(?:st|nd|rd|th)?)?", re.IGNORECASE)


def _month_day(scene: dict) -> str | None:
    """'the 4th of March' -> '4 March'. Year deliberately absent when unstated."""
    for evidence in scene.get("time_evidence", []):
        match = _MONTH_DAY.search(evidence.get("text") or "")
        if match:
            day = match.group(1) or match.group(3)
            month = match.group(2).capitalize()
            return f"{day} {month}" if day else month
    return None


def _interpolate(sequence: list[dict], anchors: list[tuple[int, object]]) -> None:
    """Fill scenes between stated dates by position; mark them approximate."""
    if not anchors:
        return
    for (i0, d0), (i1, d1) in zip(anchors, anchors[1:]):
        span_scenes = i1 - i0
        span_days = (d1 - d0).days
        if span_scenes <= 1:
            continue
        for offset in range(1, span_scenes):
            scene = sequence[i0 + offset]
            if scene["date_confidence"] == "stated":
                continue
            step = round(span_days * offset / span_scenes)
            scene["date"] = (d0 + timedelta(days=step)).isoformat()
            scene["date_confidence"] = "approx"
            scene["date_evidence"] = (f"between {d0.isoformat()} and {d1.isoformat()}")
    first_index, first_date = anchors[0]
    for scene in sequence[:first_index]:
        scene["date"] = first_date.isoformat()
        scene["date_confidence"] = "approx"
        scene["date_evidence"] = f"before {first_date.isoformat()}"
    last_index, last_date = anchors[-1]
    for offset, scene in enumerate(sequence[last_index + 1:], start=1):
        scene["date"] = (last_date + timedelta(days=offset)).isoformat()
        scene["date_confidence"] = "approx"
        scene["date_evidence"] = f"after {last_date.isoformat()}"


def build_day_axis(scenes: list[dict]) -> list[dict]:
    """Per-track day numbers, a STRICTLY MONOTONIC `t` per scene, and REAL DATES
    where the book states or implies them.

    Defects fixed 2026-08-23 (found by auditing output against the book):
    - every scene in a chapter collapsed onto one `t` (day + time-of-day only), which
      erased intra-day order and manufactured false 'bilocation' contradictions;
    - time-of-day could push a later scene EARLIER than the one before it;
    - stated dates were captured then ignored, so a 34-year flashback read as 14 days.
    Telling order now dominates `t`; time-of-day only nudges within the slot; and the
    calendar comes from the text (see assign_dates)."""
    day_by_track = defaultdict(lambda: 1)
    prev_by_track: dict[str, dict] = {}
    allowed_years = _plausible_years(scenes)
    year_by_track: dict[str, int | None] = {}

    for scene in scenes:
        track = scene["track"]
        prev = prev_by_track.get(track)
        scene["_advances"] = prev is not None and _new_day(prev, scene)
        if scene["_advances"]:
            day_by_track[track] += 1
        scene["day"] = day_by_track[track]
        stated = _stated_year(scene)
        if stated in allowed_years:
            year_by_track[track] = stated
        scene["year"] = year_by_track.get(track)
        prev_by_track[track] = scene

    # second pass: telling order inside each day decides `t`, so it is strictly
    # increasing; NIGHT scenes sit slightly later within their slot.
    per_day: dict[tuple[str, int], list[dict]] = defaultdict(list)
    for scene in scenes:
        per_day[(scene["track"], scene["day"])].append(scene)
    for (_, day), in_day in per_day.items():
        total = len(in_day)
        for index, scene in enumerate(in_day):
            slot = (index + 1) / (total + 1)
            nudge = 0.12 if scene.get("time_of_day") == "NIGHT" else 0.0
            scene["t"] = day + min(0.98, slot * 0.85 + nudge)
    assign_time_of_day(scenes)
    assign_dates(scenes)
    for scene in scenes:
        scene.pop("_advances", None)
        if not scene.get("date_display") and scene.get("date"):
            value = date.fromisoformat(scene["date"])
            scene["date_display"] = f"{value.day} {value.strftime('%B')} {value.year}"
        if scene.get("clock") and scene.get("date_display"):
            scene["when_display"] = f"{scene['date_display']}, {scene['clock']}"
        else:
            scene["when_display"] = scene.get("date_display") or scene.get("clock") or ""
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
            if other >= 3 * seen and share < 0.25:
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


def solve(scenes: list[dict], registry: dict, *, fill_gaps: bool = True) -> dict:
    locations = {loc["id"]: loc for loc in registry["locations"]}
    scenes = apply_region_track(partition(scenes), locations)
    scenes = build_day_axis(scenes)
    if fill_gaps:
        filled = fill_location_gaps(scenes, locations)
        if filled:
            build_day_axis(scenes)          # re-derive with the newly placed scenes
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
