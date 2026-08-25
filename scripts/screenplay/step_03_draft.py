"""Step 03 — draft: the paid work. Two agent calls per beat.

Each scene file is written THE MOMENT it exists, so a crash at beat N keeps 1..N-1.
That is also the resume key: a beat whose file exists is not re-bought. The events
table is a record of what happened, never the authority on what is done.
"""

from __future__ import annotations

import json
from pathlib import Path

from agents import screenwriter, shot_designer
from studio import db, paths, tracking
from studio.screenplay_spec import (Scene, SceneDraft, ScreenplayPlan, ShotPlan, Slug,
                                    SceneRef)

STEP_ID = "03"
NAME = "draft"

TIME_NARROWING = {"DAY": {"DAY", "DAWN", "DUSK"}, "NIGHT": {"NIGHT", "DUSK"}}


def slug_text(int_ext: str, location_name: str, time: str) -> str:
    """The printed line. Upper case is a Fountain requirement, not a house style."""
    head = "INT./EXT." if int_ext == "INT/EXT" else f"{int_ext}."
    return f"{head} {location_name} - {time}".upper()


def build_slug(scenes: list[dict], locations: dict) -> Slug:
    """One slug from the beat's source scenes. The FIRST scene sets place and time."""
    first = scenes[0] if scenes else {}
    location_id = first.get("location_id")
    name = (locations.get(location_id, {}).get("name")
            or first.get("location_text") or "UNKNOWN")
    int_ext = first.get("int_ext") or "UNKNOWN"
    time = first.get("time_of_day") or "DAY"
    return Slug(int_ext=int_ext, location_id=location_id, location_name=name,
                time=time, text=slug_text(int_ext, name, time))


def paragraphs_for(book_dir: Path, scenes: list[dict]) -> dict:
    """The verbatim source spans a `verbatim` claim will be checked against."""
    out: dict = {}
    for scene in scenes:
        chapter_path = book_dir / "analysis" / "chapters" / f"ch_{scene['chapter']:02d}.json"
        if not chapter_path.exists():
            continue
        paras = json.loads(chapter_path.read_text(encoding="utf-8")).get("paragraphs", [])
        start, end = scene.get("para_start") or 1, scene.get("para_end") or 0
        text = [p.get("text", "") if isinstance(p, dict) else str(p)
                for p in paras[start - 1:end]]
        out[f"{scene['chapter']}:{scene['scene']}"] = text
    return out


def source_scenes(dossier: dict, beat) -> list[dict]:
    wanted = [(r.chapter, r.scene) for r in beat.source]
    by_key = {(s["chapter"], s["scene"]): s for s in dossier["scenes"]}
    return [by_key[k] for k in wanted if k in by_key]


def assemble(beat, number: int, draft: SceneDraft, shots: ShotPlan,
             scenes: list[dict], locations: dict) -> Scene:
    """Code owns sluglines, numbering and measurement. Never asked of an agent."""
    return Scene(
        number=number,
        beat_id=beat.id,
        slug=build_slug(scenes, locations),
        cast=sorted({c for s in scenes for c in s.get("cast", [])}),
        speaking=sorted({e.character for e in draft.elements
                         if e.kind == "dialogue" and e.character}),
        elements=draft.elements,
        shots=shots.shots,
        source=[SceneRef(chapter=s["chapter"], scene=s["scene"]) for s in scenes],
        transfer=beat.transfer,
    )


def scene_path(out: Path, number: int) -> Path:
    return out / "scenes" / f"sc_{number:04d}.json"


def run(codex_id: str, target_name: str = "feature") -> None:
    conn = db.get_connection()
    book_dir = paths.book_dir(codex_id)
    tracker = tracking.Tracker(conn, codex_id, "screenplay")
    print(f"[{STEP_ID}] {NAME}: run_id={tracker.run_id} target={target_name}")

    screenplay_dir = book_dir / "screenplay"
    dossier = json.loads((screenplay_dir / "dossier.json").read_text(encoding="utf-8"))
    out = screenplay_dir / target_name
    plan = ScreenplayPlan.model_validate_json(
        (out / "plan.json").read_text(encoding="utf-8"))
    (out / "scenes").mkdir(parents=True, exist_ok=True)
    locations = {loc["id"]: loc for loc in dossier["locations"]}
    target = {"style": ""}

    written, reused = 0, 0
    for number, beat in enumerate(plan.beats, start=1):
        path = scene_path(out, number)
        if path.exists():                       # resume key = the OUTPUT's existence
            reused += 1
            continue
        scenes = source_scenes(dossier, beat)
        usage: dict = {}
        with tracker.step("03_01"):
            draft = screenwriter.write(beat.model_dump(mode="json"), dossier,
                                       paragraphs_for(book_dir, scenes), target,
                                       usage=usage)
        with tracker.step("03_02"):
            slug = build_slug(scenes, locations)
            shots = shot_designer.design(
                [e.model_dump(mode="json") for e in draft.elements],
                slug.model_dump(mode="json"),
                locations.get(slug.location_id, {}).get("visual"), usage=usage)
        with tracker.step("03_03"):
            scene = assemble(beat, number, draft, shots, scenes, locations)
            path.write_text(scene.model_dump_json(indent=2), encoding="utf-8")
        written += 1
        tracker.log(f"beat {beat.id}: {len(draft.elements)} elements, "
                    f"{len(shots.shots)} shots, usage {usage}", step_id="03_03")
        print(f"  beat {beat.id} -> sc_{number:04d}.json "
              f"({len(draft.elements)} elements, {len(shots.shots)} shots)")
    print(f"  03 draft: {written} written, {reused} reused from disk")
