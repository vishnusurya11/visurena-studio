"""Binding a chapter's cast reads who is PRESENT in its scenes, not who has a
journey row there.  On a real chapter the journey listed a figure the prose
only invokes, and binding it would have ordered a sheet and a voice for
someone who is never on screen."""
from __future__ import annotations

import json
from pathlib import Path

from scripts.episode import step_01_bind as bind


def _book(tmp_path: Path, scenes: list[dict] | None) -> Path:
    chars = tmp_path / "analysis" / "characters"
    chars.mkdir(parents=True)
    rows = {"lead": {"id": "lead", "role": "protagonist", "appearances": 40, "journey": [{"chapter": 3, "scene": 1}]},
            "guest": {"id": "guest", "role": "major", "appearances": 9, "journey": [{"chapter": 3, "scene": 2}]},
            "invoked": {"id": "invoked", "role": "minor", "appearances": 5, "journey": [{"chapter": 3, "scene": 2}]},
            "crowd": {"id": "crowd", "role": "group", "appearances": 7, "journey": [{"chapter": 3, "scene": 1}]}}
    for who, row in rows.items():
        (chars / f"{who}.json").write_text(json.dumps(row), encoding="utf-8")
    if scenes is not None:
        (tmp_path / "analysis" / "scenes.json").write_text(json.dumps(scenes), encoding="utf-8")
    return tmp_path


def test_only_the_figures_present_in_a_scene_are_bound(tmp_path):
    book = _book(tmp_path, [{"chapter": 3, "scene": 1, "characters": ["lead", "crowd"]},
                            {"chapter": 3, "scene": 2, "characters": ["lead", "guest"]},
                            {"chapter": 4, "scene": 1, "characters": ["invoked"]}])
    assert bind.chapter_cast(book, 3) == ["lead", "guest"]


def test_without_a_scenes_file_the_journey_still_answers(tmp_path):
    book = _book(tmp_path, None)
    assert bind.chapter_cast(book, 3) == ["lead", "guest", "invoked"]
