"""Step 03 — draft: the paid work. Two agent calls per beat.

Each scene file is written THE MOMENT it exists, so a crash at beat N keeps 1..N-1.
That is also the resume key: a beat whose file exists is not re-bought. The events
table is a record of what happened, never the authority on what is done.
"""

from __future__ import annotations

import json
from pathlib import Path

from agents import screenwriter, shot_designer
from studio import db, names, paths, tracking
from studio.screenplay_spec import (Scene, SceneDraft, ScreenplayPlan, ShotPlan, Slug,
                                    SceneRef)

STEP_ID = "03"
NAME = "draft"

TIME_NARROWING = {"DAY": {"DAY", "DAWN", "DUSK"}, "NIGHT": {"NIGHT", "DUSK"}}


SLUG_PREFIX = {"INT": "INT.", "EXT": "EXT.", "INT/EXT": "INT./EXT.",
               # Fountain recognises a scene heading by its PREFIX. "UNKNOWN." is not
               # one, so the parser typed two of the first real render's 22 slugs as
               # Action and the scenes silently lost their headings. INT is the safer
               # fallback: an interior slug on an exterior scene is a continuity note,
               # an exterior slug on an interior one implies a place we never had.
               "UNKNOWN": "INT."}


def slug_text(int_ext: str, location_name: str, time: str) -> str:
    """The printed line. Upper case is a Fountain requirement, not a house style."""
    head = SLUG_PREFIX.get(int_ext, "INT.")
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


def split_beat(scenes: list[dict], locations: dict) -> list[dict]:
    """Break one beat into the scenes a slugline can honestly describe.

    A beat is a SEQUENCE - Coppola's 50 sections became 225 slug lines - and rendering
    one beat as one scene produced the top finding of every reader who looked at the
    output: 16 of 22 scenes changed location or time under a single heading, one of them
    across six locations. A heading covering six places collapses to the vaguest thing
    covering them all, which is exactly how INT. UTAH happened.

    The unit is ONE PLACE AT ONE LIGHTING CONDITION - the same rule a strip board uses,
    because that is what a heading is for. A→B→A is three scenes, not two: each return
    is a new setup.

    A scene with NO location does not split off on its own. It continues the current
    unit, because splitting on a gap would manufacture headings nobody can shoot.
    """
    if not scenes:
        return [{"sources": [], "slug": build_slug([], locations)}]

    units: list[dict] = []
    current_key = None
    for scene in scenes:
        location, time = scene.get("location_id"), scene.get("time_of_day")
        key = (location, time)
        if location is None and units:
            units[-1]["sources"].append(scene)      # unplaced: stay where we are
            continue
        if not units or key != current_key:
            units.append({"sources": [scene]})
            current_key = key
        else:
            units[-1]["sources"].append(scene)
    for unit in units:
        unit["slug"] = build_slug(unit["sources"], locations)
    return units


def paragraphs_for(book_dir: Path, scenes: list[dict]) -> dict:
    """The verbatim source spans a `verbatim` claim will be checked against.

    NOTE the path: chapters live under source/, not analysis/. This looked in
    analysis/chapters/ on the first real run, silently returned {}, and the result was
    that the screenwriter never saw a word of the book while all 259 verbatim claims
    were checked against an empty string and downgraded. A join that returns nothing
    looks exactly like a join that found nothing.
    """
    out: dict = {}
    for scene in scenes:
        chapter_path = book_dir / "source" / "chapters" / f"ch_{scene['chapter']:02d}.json"
        if not chapter_path.exists():
            continue
        paras = json.loads(chapter_path.read_text(encoding="utf-8")).get("paragraphs", [])
        start, end = scene.get("para_start") or 1, scene.get("para_end") or 0
        text = [p.get("text", "") if isinstance(p, dict) else str(p)
                for p in paras[start - 1:end]]
        out[f"{scene['chapter']}:{scene['scene']}"] = text
    return out


def canonical_cue(character: str | None, registry: list[dict]) -> str | None:
    """Resolve whatever the writer put in `character` back to a canonical id.

    The skill asks for ids; the writer returns "Sherlock Holmes", because that is what a
    screenplay cue looks like. Eighteen characters were reported "not in the registry"
    who are plainly in it. Resolve rather than scold — and keep an unresolvable cue,
    because a walk-on with a line is still a line and G2 will report it honestly.
    """
    if not character:
        return character
    if not is_speakable(character):
        return None
    ids = {entity["id"] for entity in registry}
    if character in ids:
        return character
    index = names.build_index(registry)
    surnames = names.build_surname_index(registry)
    return (names.match_alias(character, index)
            or names.match_alias(character, surnames)
            or character)


# Extraction's own sentinels for "I could not tell who spoke". `_unknowable` reached
# the printed page as a character and would have gone on the call sheet.
SENTINEL_PREFIX = "_"
# A cue is the name production calls an actor. It is never a crowd, and never a plot
# fact: THE RETIRED SERGEANT OF MARINES printed the answer to Holmes's deduction in the
# left margin of the page on which he performs it.
COLLECTIVES = {"the mormons", "the crowd", "the men", "the women", "the others",
               "the group", "everyone", "all", "the party", "the mourners"}
PLOT_FACT = ("retired sergeant", "the murderer", "the victim", "the killer")


def is_speakable(character: str) -> bool:
    """May this string be a character cue at all?"""
    key = (character or "").strip().lower()
    if not key or key.startswith(SENTINEL_PREFIX):
        return False
    if key in COLLECTIVES:
        return False
    return not any(fact in key for fact in PLOT_FACT)


def source_scenes(dossier: dict, beat) -> list[dict]:
    wanted = [(r.chapter, r.scene) for r in beat.source]
    by_key = {(s["chapter"], s["scene"]): s for s in dossier["scenes"]}
    return [by_key[k] for k in wanted if k in by_key]


def assemble(beat, number: int, draft: SceneDraft, shots: ShotPlan,
             scenes: list[dict], locations: dict, registry: list[dict] | None = None,
             slug=None) -> Scene:
    """Code owns sluglines, numbering, cue resolution and measurement.

    `slug` is passed when a beat was split into units - the unit's own heading, true of
    everything under it, rather than the whole beat's.
    """
    for element in draft.elements:
        element.character = canonical_cue(element.character, registry or [])
        if element.kind != "dialogue":
            # An action line carrying a character is not a cue; it leaked into cast
            # lists and shot rows in the shipped screenplay.
            element.character = None
    return Scene(
        number=number,
        beat_id=beat.id,
        slug=slug or build_slug(scenes, locations),
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

    written, reused, number = 0, 0, 0
    for beat in plan.beats:
        scenes = source_scenes(dossier, beat)
        # A beat is a SEQUENCE, and one heading must be true of everything under it.
        # Splitting here rather than after the writing means each unit is ONE place at
        # ONE time - which is what a screenwriter writes and what a strip board needs.
        units = split_beat(scenes, locations)
        for unit in units:
            number += 1
            path = scene_path(out, number)
            if path.exists():               # resume key = the OUTPUT's existence
                reused += 1
                continue
            unit_scenes, slug = unit["sources"], unit["slug"]
            usage: dict = {}
            with tracker.step("03_01"):
                draft = screenwriter.write(
                    beat.model_dump(mode="json"), dossier,
                    paragraphs_for(book_dir, unit_scenes), target,
                    usage=usage)
            with tracker.step("03_02"):
                shots = shot_designer.design(
                    [e.model_dump(mode="json") for e in draft.elements],
                    slug.model_dump(mode="json"),
                    locations.get(slug.location_id, {}).get("visual"), usage=usage)
            with tracker.step("03_03"):
                scene = assemble(beat, number, draft, shots, unit_scenes, locations,
                                 dossier["characters"], slug=slug)
                path.write_text(scene.model_dump_json(indent=2), encoding="utf-8")
            written += 1
            tracker.log(f"beat {beat.id} unit {number}: {len(draft.elements)} elements, "
                        f"{len(shots.shots)} shots, usage {usage}", step_id="03_03")
            print(f"  beat {beat.id} -> sc_{number:04d} {slug.text[:46]} "
                  f"({len(draft.elements)} el, {len(shots.shots)} shots)")
    print(f"  03 draft: {written} written, {reused} reused from disk")


def repair_scene(scene, registry: list[dict]) -> Scene:
    """Apply cue and speech fixes to a scene that has ALREADY been paid for.

    The three readers found defects that live in the drafted element stream, not in the
    renderer — a sentinel printed as a character, one man under three cues, novel
    narration inside speeches. Fixing the writer's prompt only helps the NEXT draft, and
    a re-draft costs money, so these are repaired in place where they can be.

    A speech whose cue cannot be a character becomes ACTION rather than being dropped:
    `_unknowable` was words pinned to a bedspread, which is an insert, and losing the
    words would be worse than mislabelling them.
    """
    from studio import quotes

    for element in scene.elements:
        if element.kind != "dialogue":
            # An action or transition line carrying a character is not a cue. 68 of
            # them shipped, leaking into cast lists and shot rows.
            element.character = None
            element.emotion = None
            continue
        element.text = quotes.clean(element.text) or element.text
        cue = canonical_cue(element.character, registry)
        if cue is None:
            element.kind = "action"
            element.character = None
            element.parenthetical = None
        else:
            element.character = cue
    scene.speaking = sorted({e.character for e in scene.elements
                             if e.kind == "dialogue" and e.character})
    return scene
