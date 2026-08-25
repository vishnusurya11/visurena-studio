"""Step 05 — verify: deterministic guards first, one agent over a sample second.

Nothing here scores. Findings must be located and quotable, or they are not findings.
The four guards are free and gating; the auditor is the only paid call, and it cannot
manufacture evidence — an issue whose book_quote fails is_grounded() is dropped before
it reaches the improve loop.
"""

from __future__ import annotations

import json
from pathlib import Path

from studio import db, paths, tracking
from studio.screenplay_spec import Scene, Screenplay

STEP_ID = "05"
NAME = "verify"

K_SAMPLED = 3
MAX_IMPROVE_ROUNDS = 2
NARROWING = {"DAY": {"DAY", "DAWN", "DUSK", "CONTINUOUS", "LATER", "MOMENTS LATER"},
             "NIGHT": {"NIGHT", "DUSK", "CONTINUOUS", "LATER", "MOMENTS LATER"}}


def g1_coordinates(scene: Scene, known: set) -> list[str]:
    """Every source ref exists in the dossier. Kills invented coordinates."""
    return [f"scene {scene.number}: cites {(r.chapter, r.scene)}, which does not exist"
            for r in scene.source if (r.chapter, r.scene) not in known]


def g2_roster(scene: Scene, registry: set, placed: dict) -> list[str]:
    """Characters exist AND the timeline puts them there. Kills invented people and
    bilocation."""
    problems = []
    for character in scene.speaking:
        if character not in registry:
            problems.append(f"scene {scene.number}: {character!r} is not in the registry")
        elif placed and character not in placed.get(scene.number, set()):
            problems.append(f"scene {scene.number}: {character!r} speaks but the source "
                            f"scenes do not place them there")
    return problems


def g3_place_and_time(scene: Scene, sources: list[dict]) -> list[str]:
    """A slug may NARROW its source's time (DAY->DAWN) but never contradict it."""
    problems = []
    for source in sources:
        source_time = source.get("time_of_day")
        allowed = NARROWING.get(source_time)
        if allowed and scene.slug.time not in allowed:
            problems.append(f"scene {scene.number}: slug says {scene.slug.time}, "
                            f"source ch{source['chapter']} sc{source['scene']} "
                            f"says {source_time}")
        if (scene.slug.location_id and source.get("location_id")
                and scene.slug.location_id != source["location_id"]):
            problems.append(f"scene {scene.number}: slug at {scene.slug.location_id}, "
                            f"source at {source['location_id']}")
    return problems


def g4_verbatim(scene: Scene, paragraphs: dict) -> list[str]:
    """A failed grounding DOWNGRADES the claim to `adapted` and counts. It never fails
    the build: the line is fine, only the label was wrong."""
    from scripts.analysis.step_02_extract import is_grounded

    problems = []
    for element in scene.elements:
        if element.provenance != "verbatim":
            continue
        source = " ".join(sum(paragraphs.values(), []))
        if not is_grounded(element.text, source):
            element.provenance = "adapted"
            problems.append(f"scene {scene.number}: verbatim claim not in source, "
                            f"downgraded to adapted: {element.text[:60]!r}")
    return problems


def sample(scenes: list, k: int = K_SAMPLED) -> list:
    """First, middle, last. A sample the reader can predict is a sample they can check."""
    if len(scenes) <= k:
        return list(scenes)
    return [scenes[0], scenes[len(scenes) // 2], scenes[-1]][:k]


def keep_grounded_issues(issues: list, paragraphs: list[str]) -> list:
    """No quote, no issue. Dropped BEFORE the improve loop, so a hallucinated finding
    never costs a paid re-run."""
    from scripts.analysis.step_02_extract import is_grounded

    source = " ".join(paragraphs)
    return [issue for issue in issues if is_grounded(issue.book_quote, source)]


def guards(screenplay: Screenplay, dossier: dict) -> list[str]:
    """G1-G4 over every scene. Free, deterministic, gating."""
    known = {(s["chapter"], s["scene"]) for s in dossier["scenes"]}
    registry = {c["id"] for c in dossier["characters"]}
    by_key = {(s["chapter"], s["scene"]): s for s in dossier["scenes"]}
    placed = {sc.number: {c for r in sc.source
                          for c in by_key.get((r.chapter, r.scene), {}).get("cast", [])}
              for sc in screenplay.scenes}
    problems = []
    for scene in screenplay.scenes:
        sources = [by_key[(r.chapter, r.scene)] for r in scene.source
                   if (r.chapter, r.scene) in by_key]
        problems += g1_coordinates(scene, known)
        problems += g2_roster(scene, registry, placed)
        problems += g3_place_and_time(scene, sources)
    return problems


def run(codex_id: str, target_name: str = "feature") -> None:
    from agents import adaptation_auditor
    from scripts.screenplay.step_03_draft import paragraphs_for

    conn = db.get_connection()
    book_dir = paths.book_dir(codex_id)
    tracker = tracking.Tracker(conn, codex_id, "screenplay")
    print(f"[{STEP_ID}] {NAME}: run_id={tracker.run_id} target={target_name}")

    screenplay_dir = book_dir / "screenplay"
    dossier = json.loads((screenplay_dir / "dossier.json").read_text(encoding="utf-8"))
    out = screenplay_dir / target_name
    screenplay = Screenplay.model_validate_json(
        (out / "screenplay.json").read_text(encoding="utf-8"))
    by_key = {(s["chapter"], s["scene"]): s for s in dossier["scenes"]}

    with tracker.step("05_01"):
        problems = guards(screenplay, dossier)
        for scene in screenplay.scenes:
            sources = [by_key[(r.chapter, r.scene)] for r in scene.source
                       if (r.chapter, r.scene) in by_key]
            problems += g4_verbatim(scene, paragraphs_for(book_dir, sources))
    print(f"  05_01 guards: {len(problems)} finding(s)")

    issues, dropped = [], 0
    with tracker.step("05_02"):
        for scene in sample(screenplay.scenes):
            sources = [by_key[(r.chapter, r.scene)] for r in scene.source
                       if (r.chapter, r.scene) in by_key]
            paras = sum(paragraphs_for(book_dir, sources).values(), [])
            usage: dict = {}
            verdict = adaptation_auditor.audit(
                scene.model_dump(mode="json"), paras, usage=usage)
            kept = keep_grounded_issues(verdict.issues, paras)
            dropped += len(verdict.issues) - len(kept)
            issues += [i.model_dump(mode="json") for i in kept]
            tracker.log(f"scene {scene.number}: {len(kept)} kept, "
                        f"{len(verdict.issues) - len(kept)} ungrounded, usage {usage}",
                        step_id="05_02")
    print(f"  05_02 audit: {len(issues)} issue(s) kept, {dropped} ungrounded dropped")

    with tracker.step("05_04"):
        report = {"guards": problems, "issues": issues,
                  "ungrounded_dropped": dropped,
                  "totals": screenplay.totals.model_dump(),
                  "verdict": "PASS" if not problems and not issues else "REVIEW"}
        (out / "qc_report.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  05_04 report: {report['verdict']}")
