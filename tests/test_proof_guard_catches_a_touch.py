"""The stat guard, the SECOND check behind the fence (DESIGN 2.6; 2026-10-21_ep02_proof P1).

A stat snapshot of named paths (listed one level, never walked) taken before and after a
suite: a planted touch, a new ep02 folder or a new db companion fails with
`REAL LIBRARY TOUCHED: <path>`; an untouched tree passes."""
from __future__ import annotations

import os
import time
from pathlib import Path

import pytest

from studio.rehearsal import guard

JEKYLL = "20260827135504_the-strange-case-of-dr-jekyll-and-mr-hyde"


@pytest.fixture
def repo(tmp_path):
    """A stand-in repo with the shapes guard.named_paths reads."""
    lib = tmp_path / "library"
    ep01 = lib / JEKYLL / "episodes" / "ep01"
    for d in (ep01 / "takes" / "r2v", lib / ".vlm_cache", lib / ".autopilot", lib / ".device",
              lib / JEKYLL / "autopilot", tmp_path / "db", tmp_path / "docs", tmp_path / "comfy" / "input",
              tmp_path / "comfy" / "output"):
        d.mkdir(parents=True)
    for f in (ep01 / "plan.json", ep01 / "takes" / "r2v" / "T01.mp4", lib / "vlm_calls.jsonl",
              lib / ".autopilot" / "heartbeat.json", lib / JEKYLL / "autopilot" / "series.json",
              tmp_path / "db" / "visurena_studio.db", tmp_path / "db" / "visurena_studio.db-wal",
              tmp_path / "docs" / "DECISIONS.md"):
        f.write_text("x", encoding="utf-8")
    return tmp_path


def paths(repo: Path) -> list[Path]:
    return guard.named_paths(repo=repo, comfy=repo / "comfy")


def test_the_named_paths_cover_the_design_list_without_a_walk(repo):
    got = {p.relative_to(repo).as_posix() for p in paths(repo)}
    for rel in (f"library/{JEKYLL}/episodes/ep01/plan.json", f"library/{JEKYLL}/episodes/ep01/takes/r2v/T01.mp4",
                f"library/{JEKYLL}/episodes/ep02", "library/vlm_calls.jsonl", "library/.vlm_cache",
                "library/.autopilot/heartbeat.json", f"library/{JEKYLL}/autopilot/series.json",
                "db/visurena_studio.db", "db/visurena_studio.db-wal", "db", "comfy/input", "comfy/output",
                "docs/DECISIONS.md", "docs/episode_handbook.html"):
        assert rel in got, rel


def test_an_untouched_tree_passes(repo):
    before = guard.snapshot(paths(repo))
    assert guard.touched(before, guard.snapshot(paths(repo))) == []
    guard.check(before, paths(repo))


def bump(path: Path) -> None:
    later = time.time() + 5
    os.utime(path, (later, later))


@pytest.mark.parametrize("plant", ["touch", "ep02", "wal"])
def test_a_planted_change_fails_with_the_path(repo, plant):
    before = guard.snapshot(paths(repo))
    ep01 = repo / "library" / JEKYLL / "episodes" / "ep01"
    if plant == "touch":
        bump(ep01 / "takes" / "r2v" / "T01.mp4")
    elif plant == "ep02":
        (ep01.parent / "ep02").mkdir()
    else:
        (repo / "db" / "visurena_studio.db-shm").write_text("x", encoding="utf-8")
    with pytest.raises(guard.RealLibraryTouched, match="REAL LIBRARY TOUCHED: "):
        guard.check(before, paths(repo))


def test_the_message_names_each_touched_path(repo):
    before = guard.snapshot(paths(repo))
    (repo / "library" / "vlm_calls.jsonl").write_text("xy", encoding="utf-8")
    assert guard.touched(before, guard.snapshot(paths(repo))) == [
        f"REAL LIBRARY TOUCHED: {repo / 'library' / 'vlm_calls.jsonl'}"]


@pytest.mark.parametrize("plant", ["deep_line", "other_book_episode", "other_book_top"])
def test_a_native_write_two_levels_down_or_in_another_book_is_seen(repo, plant):
    """The backstop for writes the fence cannot see (a C library opening its own path)."""
    lines = repo / "library" / JEKYLL / "episodes" / "ep01" / "audio" / "lines"
    other = repo / "library" / "20260827135508_the-war-of-the-worlds"
    for d in (lines, other / "episodes" / "ep01"):
        d.mkdir(parents=True)
    before = guard.snapshot(paths(repo))
    target = {"deep_line": lines / "x.wav", "other_book_episode": other / "episodes" / "ep09",
              "other_book_top": other / "plan.json"}[plant]
    target.write_text("x", encoding="utf-8") if target.suffix else target.mkdir()
    with pytest.raises(guard.RealLibraryTouched, match="REAL LIBRARY TOUCHED: "):
        guard.check(before, paths(repo))


def test_a_new_entry_shows_even_when_the_folder_clock_did_not_move(repo):
    """NTFS stamps a folder from a coarse system clock: an entry added in the same tick as the
    snapshot leaves the folder's (size, mtime_ns) as they were (the flaky other_book_top case).
    The folder's entry names are part of its stat, so the new entry still shows."""
    other = repo / "library" / "20260827135508_the-war-of-the-worlds"
    (other / "episodes").mkdir(parents=True)
    before = guard.snapshot(paths(repo))
    was = os.stat(other).st_mtime_ns
    (other / "plan.json").write_text("x", encoding="utf-8")
    os.utime(other, ns=(was, was))
    assert f"REAL LIBRARY TOUCHED: {other}" in guard.touched(before, guard.snapshot(paths(repo)))
