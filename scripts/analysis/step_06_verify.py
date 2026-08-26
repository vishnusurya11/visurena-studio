"""Step 06 — verify: the analysis stage's own QC report. Deterministic, zero cost.

Checks the whole chain hangs together: manifest -> extraction -> registry -> timeline
-> dossiers, and that the timeline can actually answer THE question the owner set as
the acceptance test: "which character is at which location at what story time".

06_01 integrity   every artifact present, counts agree across steps
06_02 coverage    scene/location/character resolution rates
06_03 timeline    worldline queryability + contradiction summary
06_04 report      analysis/qc_report.json + a printed verdict
"""

from __future__ import annotations

import json
from pathlib import Path

from studio import db, paths, tracking

STEP_ID = "06"
NAME = "verify"

MIN_LOCATION_COVERAGE = 0.80     # share of scenes that must resolve to a canonical place
MIN_QUERYABLE_DAYS = 0.75        # share of story days with at least one placed character


def _load(book_dir: Path, name: str):
    path = book_dir / "analysis" / name
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def integrity(book_dir: Path) -> tuple[list[str], dict]:
    problems, facts = [], {}
    manifest = json.loads((book_dir / "source" / "book.json").read_text(encoding="utf-8"))
    facts["chapters"] = len([c for c in manifest["chapters"] if c["n"] > 0])
    extraction_files = sorted((book_dir / "analysis" / "extraction").glob("ch_*.json"))
    facts["extraction_files"] = len(extraction_files)
    if facts["extraction_files"] != facts["chapters"]:
        problems.append(f"extraction files {facts['extraction_files']} != "
                        f"chapters {facts['chapters']}")
    for name in ("registry.json", "scenes.json", "timeline.json"):
        if _load(book_dir, name) is None:
            problems.append(f"missing artifact: {name}")
    for folder in ("characters", "locations"):
        count = len(list((book_dir / "analysis" / folder).glob("*.json")))
        facts[f"{folder}_files"] = count
        if count == 0:
            problems.append(f"no files in analysis/{folder}")
    return problems, facts


def coverage(timeline: dict) -> tuple[list[str], dict]:
    problems, facts = [], {}
    scenes = timeline["scenes"]
    placed = [s for s in scenes if s["location_id"]]
    facts["scenes"] = len(scenes)
    facts["scenes_with_location"] = len(placed)
    facts["location_coverage"] = round(len(placed) / max(1, len(scenes)), 3)
    if facts["location_coverage"] < MIN_LOCATION_COVERAGE:
        problems.append(f"location coverage {facts['location_coverage']:.0%} below "
                        f"{MIN_LOCATION_COVERAGE:.0%}")
    facts["characters"] = len(timeline["characters"])
    facts["locations"] = len(timeline["locations"])
    no_coords = [l for l in timeline["locations"].values() if not (l["lat"] or l["lon"])]
    if no_coords:
        problems.append(f"{len(no_coords)} location(s) without coordinates")
    return problems, facts


def who_is_where(timeline: dict, track: str, day: int) -> dict[str, str]:
    """THE query the acceptance test needs: character -> location on a story day."""
    answer = {}
    for cid, segments in timeline["worldlines"].items():
        for segment in segments:
            if segment["track"] != track or segment["kind"] != "observed":
                continue
            if segment["day"] == day:
                answer[cid] = segment["location_id"]
    return answer


def timeline_health(timeline: dict) -> tuple[list[str], dict]:
    problems, facts = [], {}
    facts["worldlines"] = len(timeline["worldlines"])
    facts["tracks"] = {t: info["days"] for t, info in timeline["tracks"].items()}
    queryable = total = 0
    for track, info in timeline["tracks"].items():
        for day in range(1, info["days"] + 1):
            total += 1
            if who_is_where(timeline, track, day):
                queryable += 1
    facts["queryable_days"] = queryable
    facts["total_days"] = total
    facts["queryable_ratio"] = round(queryable / max(1, total), 3)
    if facts["queryable_ratio"] < MIN_QUERYABLE_DAYS:
        problems.append(f"only {facts['queryable_ratio']:.0%} of story days can answer "
                        f"'who is where' (need {MIN_QUERYABLE_DAYS:.0%})")
    contradictions = timeline["contradictions"]
    facts["contradictions"] = len(contradictions)
    facts["contradiction_types"] = {}
    for problem in contradictions:
        facts["contradiction_types"][problem["type"]] = \
            facts["contradiction_types"].get(problem["type"], 0) + 1
    if not timeline["worldlines"]:
        problems.append("no worldlines — the timeline cannot answer any query")
    return problems, facts


def run(codex_id: str) -> None:
    conn = db.get_connection()
    book_dir = paths.book_dir(codex_id)
    tracker = tracking.Tracker(conn, codex_id, "analysis")
    print(f"[{STEP_ID}] {NAME}: run_id={tracker.run_id}")

    all_problems, report = [], {}
    with tracker.step("06_01"):
        problems, facts = integrity(book_dir)
        all_problems += problems
        report["integrity"] = facts
    print(f"  06_01 integrity: {facts['chapters']} chapters, "
          f"{facts['extraction_files']} extractions, "
          f"{facts.get('characters_files')} character files, "
          f"{facts.get('locations_files')} location files — {len(problems)} problem(s)")

    timeline = _load(book_dir, "timeline.json")
    with tracker.step("06_02"):
        problems, facts = coverage(timeline)
        all_problems += problems
        report["coverage"] = facts
    print(f"  06_02 coverage: {facts['scenes_with_location']}/{facts['scenes']} scenes placed "
          f"({facts['location_coverage']:.0%}), {facts['characters']} characters, "
          f"{facts['locations']} locations — {len(problems)} problem(s)")

    with tracker.step("06_03"):
        problems, facts = timeline_health(timeline)
        all_problems += problems
        report["timeline"] = facts
    print(f"  06_03 timeline: {facts['worldlines']} worldlines, "
          f"{facts['queryable_days']}/{facts['total_days']} story days answerable "
          f"({facts['queryable_ratio']:.0%}), {facts['contradictions']} contradictions")
    for track, days in facts["tracks"].items():
        sample = who_is_where(timeline, track, min(2, days))
        preview = ", ".join(f"{c}@{l}" for c, l in list(sample.items())[:3])
        print(f"         {track} day 2: {preview or '(no placements)'}")

    with tracker.step("06_04"):
        report["problems"] = all_problems
        report["verdict"] = "PASS" if not all_problems else "REVIEW"
        (book_dir / "analysis" / "qc_report.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        for problem in all_problems:
            tracker.log(f"qc: {problem}", level="WARNING", step_id="06_04")
    print(f"  06_04 report: {report['verdict']} ({len(all_problems)} problem(s))")
    for problem in all_problems[:5]:
        print(f"         - {problem}")
