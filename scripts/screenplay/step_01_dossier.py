"""Step 01 — dossier: join what analysis scattered. Code, zero LLM, per BOOK.

Analysis wrote one scene's facts into three artifacts, because three different steps
needed three different things. A slugline needs all of them at once:

    INT. 221B BAKER STREET - DAY
    ^^^  ^^^^^^^^^^^^^^^^^   ^^^
    |    |                   +-- time_of_day .... timeline.json
    |    +---------------------- location_id ..... timeline.json (gap-filled)
    +--------------------------- int_ext ......... analysis/extraction/ ONLY

Two rules this step exists to obey:

  * Read timeline.json, NOT scenes.json. scenes.json leaves 27 of this book's 92 scenes
    at UNKNOWN location; the timeline solver filled them and scenes.json never learned.
  * Never drop a scene because a sibling artifact is thin. A missing extraction costs
    you int_ext, not the scene. Silent loss is the failure mode of every join.

01_01 gather   read the analysis artifacts; hash them into input_sha256 (the resume key)
01_02 join     one record per source scene, canonical ids resolved
01_03 checks   hard rules on slugline inputs; WARN on a speaking character with no voice
01_04 emit     screenplay/dossier.json
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from studio import db, names, paths, screenformat, tracking

STEP_ID = "01"
NAME = "dossier"

TIME_OF_DAY = ("DAY", "NIGHT", "DAWN", "DUSK")


def load_profiles(book_dir: Path) -> dict:
    """Canonical character id -> its `profile` block, for whoever wrote one."""
    profiles = {}
    for path in sorted((book_dir / "analysis" / "characters").glob("*.json")):
        character = json.loads(path.read_text(encoding="utf-8"))
        profiles[character["id"]] = character.get("profile") or {}
    return profiles


def load_analysis(book_dir: Path) -> tuple[dict, dict, dict, dict]:
    """Read the four artifact families this step joins. Missing extraction is allowed."""
    analysis = book_dir / "analysis"
    timeline = json.loads((analysis / "timeline.json").read_text(encoding="utf-8"))
    registry = json.loads((analysis / "registry.json").read_text(encoding="utf-8"))
    extractions = {}
    for path in sorted((analysis / "extraction").glob("ch_*.json")):
        chapter = json.loads(path.read_text(encoding="utf-8"))
        extractions[chapter["chapter"]] = chapter
    return timeline, registry, extractions, load_profiles(book_dir)


def input_sha256(book_dir: Path) -> str:
    """Hash every input file. The resume key is the INPUTS, never the events table."""
    digest = hashlib.sha256()
    analysis = book_dir / "analysis"
    to_hash = [analysis / "timeline.json", analysis / "registry.json"]
    to_hash += sorted((analysis / "extraction").glob("ch_*.json"))
    to_hash += sorted((analysis / "characters").glob("*.json"))
    for path in to_hash:
        digest.update(path.read_bytes())
    return digest.hexdigest()


def _extraction_scene(extraction: dict | None, scene_number: int) -> dict:
    """Find the extraction scene by its NUMBER. Position in the list is not identity."""
    if not extraction:
        return {}
    for scene in extraction.get("scenes", []):
        if scene.get("n") == scene_number:
            return scene
    return {}


def _resolve(text: str | None, char_index: dict, surnames: dict) -> str | None:
    """Aliases first, bare surname only as a fallback. Order matters: an alias is
    evidence the registry recorded on purpose; a surname is an inference we allowed."""
    return names.match_alias(text, char_index) or names.match_alias(text, surnames)


def _resolve_dialogue(lines: list[dict], char_index: dict, surnames: dict) -> list[dict]:
    """Attach canonical speaker and addressee ids, keeping every surface form.

    Analysis writes `speaker_text` / `addressee_text`; an unresolved one stays None
    rather than dropping the line. Who a line is aimed at is what makes it a tactic
    instead of a statement, so the addressee is resolved too."""
    resolved = []
    for line in lines:
        resolved.append({
            **line,
            "speaker_id": _resolve(line.get("speaker_text"), char_index, surnames),
            "addressee_id": _resolve(line.get("addressee_text"), char_index, surnames),
        })
    return resolved


def _narration(extraction: dict, char_index: dict) -> dict:
    """analysis records pov once per chapter as {"narrator": ..., "tense": ...}."""
    pov = extraction.get("pov") or {}
    narrator = pov.get("narrator") if isinstance(pov, dict) else pov
    return {"pov": names.match_alias(narrator or "", char_index),
            "narrator_text": narrator,
            "tense": pov.get("tense") if isinstance(pov, dict) else None}


def _speaking(dialogue: list[dict]) -> list[str]:
    """Canonical ids with a line, in first-spoken order. Unresolved speakers drop out."""
    order = []
    for line in dialogue:
        speaker_id = line.get("speaker_id")
        if speaker_id and speaker_id not in order:
            order.append(speaker_id)
    return order


def join_scene(scene: dict, extraction: dict, char_index: dict,
               surnames: dict) -> dict:
    """One source scene as a single record: timeline facts + what only extraction kept."""
    found = _extraction_scene(extraction, scene["scene"])
    dialogue = _resolve_dialogue(found.get("dialogue") or [], char_index, surnames)
    narration = _narration(extraction, char_index)
    return {
        "chapter": scene["chapter"],
        "scene": scene["scene"],
        "type": scene.get("type"),
        "int_ext": screenformat.normalize_int_ext(found.get("int_ext")),
        "location_id": scene.get("location_id"),
        "location_text": scene.get("location_text") or "",
        "time_of_day": scene.get("time_of_day"),
        "story_day": scene.get("story_day"),
        "t": scene.get("t"),
        "cast": list(scene.get("characters") or []),
        "pov": narration["pov"],
        "narration": narration,
        "dialogue": dialogue,
        "speaking": _speaking(dialogue),
        "events": found.get("events") or [],
        "summary": scene.get("summary") or "",
        "para_start": scene.get("para_start"),
        "para_end": scene.get("para_end"),
    }


def join(timeline_scenes: list[dict], extractions: dict, registry: dict) -> list[dict]:
    """One record per source scene, in book order. Every scene survives."""
    char_index = names.build_index(registry["characters"])
    surnames = names.build_surname_index(registry["characters"])
    return [join_scene(scene, extractions.get(scene["chapter"], {}), char_index, surnames)
            for scene in timeline_scenes]


def _scene_problems(scene: dict) -> list[str]:
    """Hard rules: without these a slugline cannot be written at all."""
    where = f"ch{scene['chapter']:02d} sc{scene['scene']:02d}"
    problems = []
    if not (scene.get("location_id") or scene.get("location_text")):
        problems.append(f"{where}: no location")
    if scene.get("time_of_day") not in TIME_OF_DAY:
        problems.append(f"{where}: time_of_day {scene.get('time_of_day')!r} unusable")
    return problems


def _scene_warnings(scene: dict, profiles: dict) -> list[str]:
    """Quality signals for the screenwriter. None of these may stop the build."""
    where = f"ch{scene['chapter']:02d} sc{scene['scene']:02d}"
    warnings = []
    if scene.get("int_ext") == "UNKNOWN":
        warnings.append(f"{where}: int_ext UNKNOWN - slugline will guess")
    for speaker_id in scene.get("speaking", []):
        if not (profiles.get(speaker_id) or {}).get("voice"):
            warnings.append(f"{where}: {speaker_id} speaks but has no profile.voice")
    for line in scene.get("dialogue", []):
        if line.get("speaker_id") is None:
            warnings.append(f"{where}: unresolved speaker {line.get('speaker_text')!r}")
    return warnings


def check(scenes: list[dict], profiles: dict) -> tuple[list[str], list[str]]:
    """Problems fail the step; warnings are recorded and the build continues."""
    problems, warnings = [], []
    for scene in scenes:
        problems += _scene_problems(scene)
        warnings += _scene_warnings(scene, profiles)
    return problems, warnings


def build(book_dir: Path) -> tuple[dict, list[str], list[str]]:
    """The whole step as one function, so the runner below stays thin."""
    timeline, registry, extractions, profiles = load_analysis(book_dir)
    scenes = join(timeline["scenes"], extractions, registry)
    problems, warnings = check(scenes, profiles)
    dossier = {
        "input_sha256": input_sha256(book_dir),
        "scenes": scenes,
        "characters": registry["characters"],
        "locations": registry["locations"],
        "voices": {cid: p.get("voice") for cid, p in profiles.items() if p.get("voice")},
        "totals": {"scenes": len(scenes),
                   "speaking": len({s for sc in scenes for s in sc["speaking"]})},
    }
    return dossier, problems, warnings


def run(codex_id: str, target_name: str | None = None) -> None:
    """The dossier is per BOOK, shared by every target, so target_name is ignored."""
    conn = db.get_connection()
    book_dir = paths.book_dir(codex_id)
    tracker = tracking.Tracker(conn, codex_id, "screenplay")
    print(f"[{STEP_ID}] {NAME}: run_id={tracker.run_id}")

    with tracker.step("01_01"):
        timeline, _registry, extractions, profiles = load_analysis(book_dir)
    print(f"  01_01 gather: {len(timeline['scenes'])} scenes, "
          f"{len(extractions)} extraction file(s), {len(profiles)} character(s)")

    with tracker.step("01_02"):
        dossier, problems, warnings = build(book_dir)
    print(f"  01_02 join: {dossier['totals']['scenes']} scene records, "
          f"{dossier['totals']['speaking']} speaking character(s)")

    with tracker.step("01_03"):
        for warning in warnings:
            tracker.log(f"dossier: {warning}", level="WARNING", step_id="01_03")
        for problem in problems:
            tracker.log(f"dossier: {problem}", level="ERROR", step_id="01_03")
        if problems:
            raise ValueError(f"dossier checks failed: {len(problems)} problem(s); "
                             f"first: {problems[0]}")
    print(f"  01_03 checks: 0 problems, {len(warnings)} warning(s)")
    for warning in warnings[:5]:
        print(f"         - {warning}")

    with tracker.step("01_04"):
        out = book_dir / "screenplay"
        out.mkdir(parents=True, exist_ok=True)
        (out / "dossier.json").write_text(
            json.dumps(dossier, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  01_04 emit: {out / 'dossier.json'}")
