"""Audit every scene's location with independent judges, then compare their answers.

Run: uv run python -m scripts.screenplay.audit_locations <codex_id> [target]

Each scene is judged JUDGES times from the book's own words. No judge sees the
pipeline's answer or another judge's, so the agreement between them is evidence rather
than an echo. Writes location_audit.json beside the screenplay.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from agents import location_auditor
from studio import consensus, db, llm, paths
from studio.screenplay_spec import Screenplay

JUDGES = 3          # odd, so a majority exists
STAGE = "screenplay"
STEP_ID = "05"


def scene_paragraphs(dossier: dict, scene) -> list[str]:
    """The book's own words for the source scenes this screen scene covers."""
    by_key = {(s["chapter"], s["scene"]): s for s in dossier["scenes"]}
    out = []
    for ref in scene.source:
        source = by_key.get((ref.chapter, ref.scene))
        if source:
            out.append(f"[ch{ref.chapter} sc{ref.scene}] {source.get('synopsis') or ''}")
            for line in source.get("dialogue", [])[:6]:
                if line.get("speech"):
                    out.append(f'  "{line["speech"]}"')
    return out


def audit_scene(scene, dossier: dict, previous: str | None,
                judges: int = JUDGES) -> dict:
    """Ask `judges` independent judges where this scene happens."""
    paragraphs = scene_paragraphs(dossier, scene)
    verdicts = []
    for _ in range(judges):
        verdicts.append(location_auditor.judge(
            paragraphs, dossier["locations"], previous_location=previous))
    answers = [v.location_id for v in verdicts]
    row = consensus.verdict(answers, scene.slug.location_id)
    return {**row,
            "scene": scene.number,
            "slug": scene.slug.text,
            "judgments": [v.model_dump(mode="json") for v in verdicts]}


def run(codex_id: str, target: str = "feature", judges: int = JUDGES) -> dict:
    conn = db.get_connection()
    book_dir = paths.book_dir(codex_id)
    out = book_dir / "screenplay" / target
    dossier = json.loads(
        (book_dir / "screenplay" / "dossier.json").read_text(encoding="utf-8"))
    screenplay = Screenplay.model_validate_json(
        (out / "screenplay.json").read_text(encoding="utf-8"))

    rows, previous = [], None
    with llm.spend_context(conn, codex_id, STAGE, STEP_ID):
        for scene in screenplay.scenes:
            row = audit_scene(scene, dossier, previous, judges)
            rows.append(row)
            previous = scene.slug.location_id
            mark = {"confirmed": "ok", "wrong": "WRONG", "disputed": "disputed",
                    "unknowable": "unknowable", "registry_gap": "not in registry"
                    }.get(row["verdict"], row["verdict"])
            print(f"  scene {scene.number:>2}  {row['level']:<9} {mark:<15} "
                  f"{scene.slug.location_id or '-'}"
                  + (f"  -> {row['should_be']}" if row.get("should_be") else ""))

    report = {"judges": judges, "summary": consensus.summarise(rows), "scenes": rows}
    (out / "location_audit.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    s = report["summary"]
    print(f"\n{s['confirmed']} confirmed / {s['wrong']} wrong / {s['disputed']} disputed"
          f" / {s['unknowable']} unknowable / {s['registry_gap']} registry gap")
    print(f"confirmation rate over {s['decidable']} decidable scenes: "
          f"{s['confirmed_rate']:.0%}")
    return report


if __name__ == "__main__":
    run(sys.argv[1], *(sys.argv[2:3] or []))
