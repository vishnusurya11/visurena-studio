"""A miss is named by the artefact's relative path, never by what was said.

The report lands in docs/, which is book-neutral: it may carry codex ids,
sha8s and relative paths (opaque), never the owner's words, the story or an
absolute path.  So `misses` returns paths, and the report quotes nothing
from a row's source.
"""
from pathlib import Path

from studio import judge_bench as jb

FIXTURES = Path(__file__).parent / "fixtures" / "judge_bench"


def passes_everything(row):
    return {"refused": False, "classes": [], "values": {}}


def test_misses_are_relative_posix_paths():
    outcomes = jb.run(jb.load_rows(FIXTURES, "take"), passes_everything)
    missed = jb.misses(outcomes)
    assert missed and all(isinstance(m, str) for m in missed)
    assert all(not m.startswith("/") and ":" not in m and "\\" not in m for m in missed)
    assert all(m.startswith("episodes/") for m in missed)


def test_the_report_quotes_no_source_words():
    rows = jb.load_rows(FIXTURES, "take")
    outcomes = jb.run(rows, passes_everything)
    text = jb.report(outcomes, "fixture", "abcdef01", "git:0000000")
    for row in rows:
        if row.source.startswith("owner note"):
            assert row.source not in text
    assert "slid with the fence" not in text and "#L" not in text
    assert "episodes/ep01/takes/r2v/T04.mp4" in text
