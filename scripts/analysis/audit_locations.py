"""Audit ANALYSIS scene locations with independent judges.

The screenplay audit found five unanimously-wrong locations, but a screenplay only
copies what analysis decided. This audits the source: timeline.json, where a scene's
location is actually assigned. Fixing it here fixes every screenplay ever made from it.

Sampling is stratified rather than exhaustive, because the purpose is to find SYSTEMATIC
error worth changing a skill over, not to grade every scene. A sample that covers the
book start to end will show a pattern if there is one.

Run: uv run python -m scripts.analysis.audit_locations <codex_id> [sample_size]
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from agents import location_auditor
from studio import consensus, db, llm, paths

JUDGES = 3
SAMPLE = 25


def stratified(scenes: list[dict], size: int) -> list[dict]:
    """An evenly spaced sample across the whole book, first and last always included.

    Evenly spaced rather than random: a location error is often positional - front
    matter, a flashback block, the last chapter - and a random sample can miss a run
    of them entirely."""
    if len(scenes) <= size:
        return list(scenes)
    step = (len(scenes) - 1) / (size - 1)
    return [scenes[round(i * step)] for i in range(size)]


def scene_text(scene: dict) -> list[str]:
    """What the judge reads: the scene's own synopsis and its typed evidence."""
    out = [scene.get("synopsis") or scene.get("summary") or ""]
    out += [f'"{e.get("text")}"' for e in (scene.get("time_evidence") or [])[:3]
            if e.get("text")]
    if scene.get("location_text"):
        out.append(f'(the text names: {scene["location_text"]})')
    return [line for line in out if line]


def run(codex_id: str, sample: int = SAMPLE, judges: int = JUDGES) -> dict:
    conn = db.get_connection()
    book_dir = paths.book_dir(codex_id)
    analysis = book_dir / "analysis"
    timeline = json.loads((analysis / "timeline.json").read_text(encoding="utf-8"))
    registry = json.loads((analysis / "registry.json").read_text(encoding="utf-8"))

    chosen = stratified(timeline["scenes"], sample)
    rows, previous = [], None
    with llm.spend_context(conn, codex_id, "analysis", "06"):
        for scene in chosen:
            answers, judgments = [], []
            for _ in range(judges):
                verdict = location_auditor.judge(
                    scene_text(scene), registry["locations"], previous_location=previous)
                answers.append(verdict.location_id)
                judgments.append(verdict.model_dump(mode="json"))
            row = consensus.verdict(answers, scene.get("location_id"))
            rows.append({**row, "chapter": scene["chapter"], "scene": scene["scene"],
                         "judgments": judgments})
            previous = scene.get("location_id")

    report = {"judges": judges, "sampled": len(chosen),
              "of_scenes": len(timeline["scenes"]),
              "summary": consensus.summarise(rows), "scenes": rows}
    (analysis / "location_audit.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


if __name__ == "__main__":
    result = run(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else SAMPLE)
    s = result["summary"]
    print(f"sampled {result['sampled']} of {result['of_scenes']} scenes")
    print(f"  {s['confirmed']} confirmed / {s['wrong']} wrong / {s['disputed']} disputed"
          f" / {s['unknowable']} unknowable / {s['registry_gap']} registry gap")
    print(f"  confirmation rate: {s['confirmed_rate']:.0%} over {s['decidable']} decidable")
