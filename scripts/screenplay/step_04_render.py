"""Step 04 — render: JSON is the artifact; Fountain and PDF are projections.

The direction of travel is one-way and never reversed. Fountain is LOSSY by
construction: it throws away provenance, source coordinates, location_id, every camera
field, and the difference between a character id and the cue printed on the page.
Nothing downstream may parse Fountain to recover a fact, because the fact is not there.

Zero LLM, byte-stable, always re-runs — it is free.
"""

from __future__ import annotations

import json
from pathlib import Path

from studio import db, fountain, paths, tracking
from studio.screenplay_spec import Scene, Screenplay, ScreenplayPlan, Totals

STEP_ID = "04"
NAME = "render"

SECONDS_PER_PAGE = 60.0


def load_scenes(out: Path) -> list[Scene]:
    return [Scene.model_validate_json(p.read_text(encoding="utf-8"))
            for p in sorted((out / "scenes").glob("sc_*.json"))]


def display_names(dossier: dict) -> dict:
    """Canonical id -> the name printed as a character cue."""
    return {c["id"]: c["name"] for c in dossier["characters"]}


def refresh_slug(scene: Scene) -> Scene:
    """Re-derive the printed slug line from its own structured fields.

    slug.text is a PROJECTION of int_ext + location_name + time, so storing it and
    trusting it makes the same fact true in two places, and they drift. Re-deriving at
    render means a fix to the formatting reaches artifacts already bought, instead of
    requiring a paid re-draft to repair a string code owns anyway.
    """
    from scripts.screenplay.step_03_draft import slug_text

    scene.slug.text = slug_text(scene.slug.int_ext, scene.slug.location_name,
                                scene.slug.time)
    return scene


def measure(scene: Scene, display: dict) -> Scene:
    """page_eighths and duration are MEASURED here, never asked of an agent."""
    scene = refresh_slug(scene)
    eighths = fountain.page_eighths(scene)
    scene.page_eighths = eighths
    scene.duration_s = round(eighths / 8 * SECONDS_PER_PAGE, 1)
    return scene


def totals(scenes: list[Scene]) -> Totals:
    eighths = sum(s.page_eighths for s in scenes)
    return Totals(scenes=len(scenes), pages=round(eighths / 8, 2),
                  runtime_s=round(sum(s.duration_s for s in scenes), 1),
                  cast=len({c for s in scenes for c in s.cast}))


def build(dossier: dict, plan: ScreenplayPlan, scenes: list[Scene],
          target_name: str, title: str) -> Screenplay:
    display = display_names(dossier)
    measured = [measure(s, display) for s in scenes]
    return Screenplay(title=title, source_work=title, target=target_name,
                      source_fingerprint=dossier["input_sha256"],
                      spine=plan.spine, logline=plan.logline,
                      scenes=measured, omitted=plan.omitted, totals=totals(measured))


def elements_index(screenplay: Screenplay) -> list[dict]:
    """A flattened VIEW keyed (scene, shot) for the video stage. Generated, never
    edited — if this and screenplay.json disagree, screenplay.json wins."""
    rows = []
    for scene in screenplay.scenes:
        for shot in scene.shots:
            covered = scene.elements[shot.covers_start:shot.covers_end + 1]
            rows.append({
                "scene": scene.number, "shot": shot.index,
                "slug": scene.slug.text, "location_id": scene.slug.location_id,
                "time": scene.slug.time, "cast": scene.cast,
                "setup": shot.setup, "term": shot.term,
                "visual_consequence": shot.visual_consequence,
                "axis_side": shot.axis_side, "crosses_axis": shot.crosses_axis,
                "text": [e.text for e in covered],
            })
    return rows


def budget_problems(screenplay: Screenplay, target: dict, slack: float = 0.25) -> list[str]:
    """Measured length against the target the editor was told. Slack is generous;
    this catches a plan that ignored the budget, not one that missed by a page."""
    want = target["pages"]
    got = screenplay.totals.pages
    if abs(got - want) > want * slack:
        return [f"{got} pages measured vs target {want} (slack {slack:.0%})"]
    return []


def lint_all(scenes: list[Scene], display: dict) -> list[str]:
    """Round-trip every scene: parse our own output, assert the typing is what we meant."""
    problems = []
    for scene in scenes:
        for problem in fountain.lint_scene(scene, display):
            problems.append(f"scene {scene.number}: {problem}")
    return problems


def run(codex_id: str, target_name: str = "feature") -> None:
    from scripts.screenplay.step_02_plan import load_target

    conn = db.get_connection()
    book_dir = paths.book_dir(codex_id)
    tracker = tracking.Tracker(conn, codex_id, "screenplay")
    print(f"[{STEP_ID}] {NAME}: run_id={tracker.run_id} target={target_name}")

    screenplay_dir = book_dir / "screenplay"
    dossier = json.loads((screenplay_dir / "dossier.json").read_text(encoding="utf-8"))
    out = screenplay_dir / target_name
    plan = ScreenplayPlan.model_validate_json(
        (out / "plan.json").read_text(encoding="utf-8"))
    title = json.loads(
        (book_dir / "source" / "book.json").read_text(encoding="utf-8")).get("title", "")
    display = display_names(dossier)

    with tracker.step("04_01"):
        screenplay = build(dossier, plan, load_scenes(out), target_name, title)
        (out / "screenplay.json").write_text(
            screenplay.model_dump_json(indent=2), encoding="utf-8")
    print(f"  04_01 json: {screenplay.totals.scenes} scenes, "
          f"{screenplay.totals.pages} pages, {screenplay.totals.runtime_s / 60:.0f} min")

    with tracker.step("04_02"):
        text = fountain.render(screenplay.scenes, display, title=title)
        (out / "screenplay.fountain").write_text(text, encoding="utf-8")
    print(f"  04_02 fountain: {len(text.splitlines())} lines")

    with tracker.step("04_03"):
        fountain.to_pdf(text, out / "screenplay.pdf")
    print(f"  04_03 pdf: {(out / 'screenplay.pdf').stat().st_size} bytes")

    with tracker.step("04_04"):
        rows = elements_index(screenplay)
        (out / "elements.json").write_text(
            json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  04_04 elements: {len(rows)} shot row(s)")

    with tracker.step("04_05"):
        problems = lint_all(screenplay.scenes, display)
        problems += budget_problems(screenplay, load_target(target_name))
        problems += balance_problems(screenplay.scenes)
        for problem in problems:
            tracker.log(f"render: {problem}", level="WARNING", step_id="04_05")
    shares = [action_share(sc) for sc in screenplay.scenes] or [0.0]
    print(f"  04_05 format: {len(problems)} problem(s) | action share "
          f"min {min(shares):.0%} mean {sum(shares) / len(shares):.0%}")
    for problem in problems[:5]:
        print(f"         - {problem}")


MAX_VOLLEY = 8               # consecutive dialogue elements with nothing staged between


def action_share(scene: Scene) -> float:
    """Share of a scene's elements that stage something. A measurement, not a verdict."""
    if not scene.elements:
        return 0.0
    return sum(1 for e in scene.elements if e.kind == "action") / len(scene.elements)


def _longest_volley(scene: Scene) -> int:
    """Longest run of dialogue with no action between. Transitions do not break it —
    a CUT TO: stages nothing, and counting it would launder an unstaged scene."""
    longest = run = 0
    for element in scene.elements:
        run = run + 1 if element.kind == "dialogue" else (0 if element.kind == "action"
                                                          else run)
        longest = max(longest, run)
    return longest


def balance_problems(scenes: list[Scene], max_volley: int = MAX_VOLLEY) -> list[str]:
    """A screenplay is not a transcript.

    The screenwriter is handed a dialogue list, and a model handed a list of lines will
    return a list of lines. Nothing else in this pipeline was checking that anything is
    STAGED. Two checks, both of which need no corpus to justify:

      * a scene with dialogue and no action at all is a radio play
      * an unbroken volley is dialogue nobody has bothered to put in a room

    Deliberately NOT checked: an action:dialogue ratio. There is no measured ratio in
    the craft references, and a fabricated threshold would be worse than no threshold.
    """
    problems = []
    for scene in scenes:
        if not scene.elements:
            problems.append(f"scene {scene.number}: no elements at all")
            continue
        speaks = any(e.kind == "dialogue" for e in scene.elements)
        stages = any(e.kind == "action" for e in scene.elements)
        if speaks and not stages:
            problems.append(f"scene {scene.number}: dialogue but no action — nobody "
                            f"moves and nothing is seen")
        volley = _longest_volley(scene)
        if volley > max_volley:
            problems.append(f"scene {scene.number}: {volley} consecutive dialogue "
                            f"elements with nothing staged between them")
    return problems
