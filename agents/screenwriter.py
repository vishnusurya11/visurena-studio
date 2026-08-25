"""Screenwriter — one beat into a screen scene (screenplay 03_01).

Owns action AND dialogue, because they interleave into one ordered stream and each
depends on the other. "He doesn't answer. He pours the brandy." is only writable
knowing the previous line was a question.
"""

from __future__ import annotations

import json
from pathlib import Path

from studio import llm
from studio.screenplay_spec import SceneDraft

TIER = "reasoning"
SKILL_PATH = Path(__file__).parent / "skills" / "screenwriter.md"


def load_skill() -> str:
    return SKILL_PATH.read_text(encoding="utf-8")


def _source_scenes(dossier: dict, refs: list[dict]) -> list[dict]:
    wanted = {(r["chapter"], r["scene"]) for r in refs}
    return [s for s in dossier["scenes"] if (s["chapter"], s["scene"]) in wanted]


def voices(dossier: dict, cast: list[str]) -> dict:
    """Only the speakers in THIS beat. A voice note for someone absent is noise."""
    return {cid: v for cid, v in (dossier.get("voices") or {}).items() if cid in cast}


def write(beat: dict, dossier: dict, paragraphs: dict, target: dict,
          usage: dict | None = None) -> SceneDraft:
    """One beat's ordered element stream, with provenance on every dialogue line."""
    scenes = _source_scenes(dossier, beat["source"])
    cast = sorted({c for s in scenes for c in s.get("cast", [])})
    payload = {
        "beat": beat,
        "style": target.get("style"),
        "source_scenes": scenes,
        "source_paragraphs": paragraphs,
        "voices": voices(dossier, cast),
        "registry": [{"id": c["id"], "name": c["name"]}
                     for c in dossier["characters"] if c["id"] in cast],
    }
    prompt = (f"{load_skill()}\n\n--- THIS BEAT AND ITS SOURCE ---\n"
              f"{json.dumps(payload, ensure_ascii=False)}\n\n"
              f"Return the ordered element stream for this beat.")
    return llm.structured(TIER, prompt, SceneDraft, usage=usage)
