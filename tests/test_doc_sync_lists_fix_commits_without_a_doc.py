"""doc_sync is an advisory report, not a hook: it lists fix commits that changed runtime code
(studio/, scripts/episode/) with no GATES/LESSONS change and no `Docs: none (reason)` trailer (P16).

Of the 12 commits that fixed Jekyll Kawajiri ep01's failures on 2026-10-18 exactly one touched a
skill doc (6475f79, LESSONS); 5d3dc08 changed step 05's packing ruler and wrote nothing down.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("doc_sync", ROOT / "scripts" / "audit" / "doc_sync.py")
doc_sync = importlib.util.module_from_spec(spec)
spec.loader.exec_module(doc_sync)


def test_a_runtime_change_with_a_lesson_passes():
    assert not doc_sync.undocumented(["studio/take_ladder.py", ".claude/skills/episode/LESSONS.md"], "")


def test_a_runtime_change_with_no_doc_is_listed():
    assert doc_sync.undocumented(["scripts/episode/step_05_timeline.py", "tests/test_x.py"], "")


def test_the_trailer_with_a_reason_excuses_it():
    assert not doc_sync.undocumented(["studio/comfy.py"], "body\n\nDocs: none (a rename)\n")


def test_a_trailer_without_a_reason_does_not():
    assert doc_sync.undocumented(["studio/comfy.py"], "Docs: none\n")


def test_a_commit_with_no_runtime_code_is_not_a_fix_commit():
    assert not doc_sync.undocumented(["tests/test_x.py", "docs/DECISIONS.md"], "")


def test_the_ep01_commits_6475f79_passes_and_5d3dc08_is_listed():
    assert doc_sync.listed(["6475f79", "5d3dc08"]) == ["5d3dc08"]
