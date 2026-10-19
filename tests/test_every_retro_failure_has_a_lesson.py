"""Every failure of the Jekyll Kawajiri ep01 retro is a lesson: its measurement, its brick and
the test that pins it (P16; the owner's rule of 2026-10-08: improve the skill after every run).

The failure list is a copy of the retro's (code and tests never read docs/audit/).
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / ".claude" / "skills" / "episode" / "LESSONS_ARCHIVE.md"
INDEX = ROOT / ".claude" / "skills" / "episode" / "LESSONS.md"
FAILURES = ROOT / "tests" / "fixtures" / "ep01_replay" / "P16" / "failures.json"
BLOCK = "## Jekyll Kawajiri ep01 retro"


def failures() -> list[dict]:
    return json.loads(FAILURES.read_text(encoding="utf-8"))["failures"]


def entry(n: int) -> str:
    block = ARCHIVE.read_text(encoding="utf-8").split(BLOCK, 1)[1].split("\n## ", 1)[0]
    return block.split(f"**Failure {n}.", 1)[1].split("**Failure ", 1)[0]


def test_there_are_thirteen():
    assert [f["id"] for f in failures()] == list(range(1, 14))


def test_each_failure_has_its_measurement_brick_commits_and_test():
    for f in failures():
        text = entry(f["id"])
        assert "Measured:" in text and f["brick"] in text, f["id"]
        assert all(sha in text for sha in f["commits"]), f["id"]
        assert f["test"] in text and (ROOT / f["test"]).exists(), f["id"]


def test_the_index_points_at_the_retro_block():
    assert BLOCK[3:] in INDEX.read_text(encoding="utf-8")
