"""Step 02 — plan: what survives, and in what order. ONE agent call per target.

The checks here exist because silent dropping is the failure mode of adaptation. An
omission you can defend is fine; an omission nobody noticed is not. So every source
scene must be inside a beat or listed in `omitted` with a reason, and code counts.
"""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from agents import story_editor
from studio import db, paths, tracking
from studio.screenplay_spec import ScreenplayPlan

STEP_ID = "02"
NAME = "plan"

TARGETS_PATH = Path("targets.yaml")


def load_target(name: str) -> dict:
    with open(TARGETS_PATH, encoding="utf-8") as fh:
        return yaml.safe_load(fh)["targets"][name]


SCENES_PER_SEQUENCE = 4.5      # Coppola's notebook: 50 sections over 225 slug lines


def beat_window(target: dict, source_scenes: int) -> tuple[int, int]:
    """How many beats this book can honestly support, capped by the target.

    Metamorphosis failed on "8 beats outside target window 18-26". It is a novella with
    21 source scenes, and demanding 18 sequences of it would mean sequences of one scene
    each - which is not what a sequence is.

    So the expectation follows from the SOURCE, and the target's window is a cap on
    ambition rather than a floor a short book must somehow meet.
    """
    low, high = target["beats"]
    supportable = max(1, round(source_scenes / SCENES_PER_SEQUENCE))
    if supportable >= low:
        return low, high                      # the book can fill the target
    # The ratio sets an EXPECTATION, not a ceiling. 18 beats over 37 scenes is two
    # scenes to a sequence - tight, but a real choice for a short work. The ceiling is
    # the source itself: there cannot be more sequences than there are scenes.
    return max(1, supportable // 2), max(1, min(high, source_scenes))


def resolve_protagonist(name: str, characters: list[dict]) -> str | None:
    """A canonical id for whatever the editor called the protagonist.

    It returns "Alice" and "Buck" - names, because that is what a person calls a
    protagonist - and demanding an id failed two books outright while the registry
    plainly contained them. Same resolution the character cues use, same reason.
    """
    from studio import names as name_index

    if not name:
        return None
    ids = {c["id"] for c in characters}
    if name in ids:
        return name
    return (name_index.match_alias(name, name_index.build_index(characters))
            or name_index.match_alias(name, name_index.build_surname_index(characters)))


def _refs(plan: ScreenplayPlan) -> set:
    return {(r.chapter, r.scene) for beat in plan.beats for r in beat.source}


def check(plan: ScreenplayPlan, dossier: dict, target: dict) -> list[str]:
    """Coordinates exist, roster is real, budget holds, nothing vanished silently."""
    problems = []
    known = {(s["chapter"], s["scene"]) for s in dossier["scenes"]}
    ids = {c["id"] for c in dossier["characters"]}
    used = _refs(plan)
    for ref in sorted(used - known):
        problems.append(f"beat cites a scene that does not exist: {ref}")
    for beat in plan.beats:
        resolved = resolve_protagonist(beat.protagonist, dossier["characters"])
        if resolved is None:
            problems.append(f"beat {beat.id}: protagonist {beat.protagonist!r} "
                            f"is not in the registry")
        else:
            beat.protagonist = resolved      # normalise in place; the plan is stored
    accounted = used | {(o.source.chapter, o.source.scene) for o in plan.omitted}
    for ref in sorted(known - accounted):
        problems.append(f"scene {ref} is in no beat and not in `omitted` — silent drop")
    low, high = beat_window(target, len(known))
    if not low <= len(plan.beats) <= high:
        problems.append(f"{len(plan.beats)} beats outside window {low}-{high} "
                        f"for {len(known)} source scenes")
    return problems + check_opening(plan)


def check_opening(plan: ScreenplayPlan) -> list[str]:
    """The opening and the final beat are one decision, and it must be stated."""
    problems = []
    ids = {beat.id for beat in plan.beats}
    for label, beat_id in (("opening", plan.opening_beat_id),
                           ("final", plan.final_beat_id)):
        if beat_id not in ids:
            problems.append(f"{label}_beat_id {beat_id!r} is not one of the beats")
    opening = next((b for b in plan.beats if b.id == plan.opening_beat_id), None)
    if opening and not opening.reversal:
        problems.append("the opening beat names no reversal — it has no punchline")
    if not plan.bookend.strip():
        problems.append("no bookend stated: opening and ending were chosen separately")
    return problems


def target_dir(book_dir: Path, target_name: str) -> Path:
    return book_dir / "screenplay" / target_name


def run(codex_id: str, target_name: str = "feature") -> None:
    conn = db.get_connection()
    book_dir = paths.book_dir(codex_id)
    tracker = tracking.Tracker(conn, codex_id, "screenplay")
    print(f"[{STEP_ID}] {NAME}: run_id={tracker.run_id} target={target_name}")

    dossier = json.loads(
        (book_dir / "screenplay" / "dossier.json").read_text(encoding="utf-8"))
    out = target_dir(book_dir, target_name)
    out.mkdir(parents=True, exist_ok=True)

    with tracker.step("02_01"):
        target = load_target(target_name)
        index = story_editor.scene_index(dossier["scenes"])
    print(f"  02_01 brief: {len(index)} scenes, target {target['pages']}pp / "
          f"{target['beats'][0]}-{target['beats'][1]} beats")

    # Resume on the OUTPUT's existence, never on the events table.
    plan_path = out / "plan.json"
    if plan_path.exists():
        plan = ScreenplayPlan.model_validate_json(plan_path.read_text(encoding="utf-8"))
        print(f"  02_02 select: reusing existing plan ({len(plan.beats)} beats)")
    else:
        with tracker.step("02_02"):
            usage: dict = {}
            plan = story_editor.plan(dossier, target, usage=usage)
            tracker.log(f"plan usage: {usage}", step_id="02_02")
        print(f"  02_02 select: {len(plan.beats)} beats, {len(plan.omitted)} omitted "
              f"| tokens {usage.get('input_tokens')}in/{usage.get('output_tokens')}out")

    with tracker.step("02_03"):
        problems = check(plan, dossier, target)
        for problem in problems:
            tracker.log(f"plan: {problem}", level="ERROR", step_id="02_03")
        if problems:
            raise ValueError(f"plan checks failed: {len(problems)}; first: {problems[0]}")
    print(f"  02_03 checks: 0 problems")

    with tracker.step("02_04"):
        plan_path.write_text(plan.model_dump_json(indent=2), encoding="utf-8")
        (out / "source_fingerprint.txt").write_text(
            dossier["input_sha256"], encoding="utf-8")
    print(f"  02_04 emit: {plan_path}")
