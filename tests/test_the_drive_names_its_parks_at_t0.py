"""drive.py names every gap the episode will meet before it spends a second (craft ruling A23, the t=0 preflight).

Jekyll ep01's run charged 6.69 h before step 13 died on a book.json with no `series` (drive_run08.log).  The
proof harness's precondition audit (scripts/proof/preconditions.py, imported here and never moved) already lists a
chapter's gaps; the launch now reads it at t=0, with the two publish doors the audit does not hold: the owner's
standing hand (publish/standing.json lists the episode) and the YouTube token's age (a Testing consent dies at 7
days).  Each finding is "refuse now" (nothing can run: no chapter text) or "will park at step N"; a publish-only
gap always parks, never refuses.  Fixture: tests/fixtures/proof/ch2_preconditions/book (the Jekyll records)."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from scripts.episode import drive
from scripts.proof import preconditions as proof
from studio import standing_approval

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "proof" / "ch2_preconditions" / "book"
NOW = 1_800_000_000.0
DAY = 86_400.0


@pytest.fixture
def book(tmp_path):
    dest = tmp_path / "library" / "jekyll"
    shutil.copytree(FIXTURE, dest)
    for rel in json.loads((dest / "present_files.json").read_text(encoding="utf-8"))["present"]:
        (dest / rel).parent.mkdir(parents=True, exist_ok=True)
        (dest / rel).write_bytes(b"")
    return dest


@pytest.fixture
def env(tmp_path):
    path = tmp_path / ".env"
    path.write_text(f"YOUTUBE_REFRESH_TOKEN=x\nYOUTUBE_REFRESH_TOKEN_AT={NOW - DAY}\n", encoding="utf-8")
    return path


def edit_book(book: Path, **drop) -> None:
    path = book / "source" / "book.json"
    said = json.loads(path.read_text(encoding="utf-8"))
    path.write_text(json.dumps({k: v for k, v in said.items() if k not in drop}), encoding="utf-8")


def sign(book: Path, episodes: list[int]) -> None:
    standing_approval.path(book).parent.mkdir(parents=True, exist_ok=True)
    standing_approval.path(book).write_text(json.dumps({"kind": "publish", "decision": standing_approval.DECISION,
                                                        "by": "owner", "episodes": episodes}), encoding="utf-8")


def test_a_book_without_series_will_park_at_step_13(book, env):
    edit_book(book, series=True)
    lines = drive.preflight(book, 2, env, NOW)
    assert any(l.startswith("will park at step 13") and "series" in l for l in lines)
    assert not drive.refusals(lines)


def test_a_chapter_with_no_text_refuses_now(book, env):
    (book / "source" / "chapters" / "ch_02.json").unlink()
    assert any("chapter_text" in l for l in drive.refusals(drive.preflight(book, 2, env, NOW)))


def test_an_unlisted_episode_will_park_at_g_standing(book, env):
    assert any("G-STANDING" in l and l.startswith("will park at step 13") for l in drive.preflight(book, 2, env, NOW))
    sign(book, [1, 2])
    assert not any("G-STANDING" in l for l in drive.preflight(book, 2, env, NOW))


def test_a_token_that_dies_before_the_run_ends_will_park_at_step_13(book, env):
    sign(book, [2])
    assert not any("token" in l for l in drive.preflight(book, 2, env, NOW))
    env.write_text(f"YOUTUBE_REFRESH_TOKEN=x\nYOUTUBE_REFRESH_TOKEN_AT={NOW - 6.9 * DAY}\n", encoding="utf-8")
    assert any(l.startswith("will park at step 13") and "token" in l for l in drive.preflight(book, 2, env, NOW))


def test_the_preflight_reads_the_proof_harness_audit(book, env, monkeypatch):
    seen = []
    monkeypatch.setattr(proof.pre, "audit", lambda b, n: seen.append(n) or {"gaps": []})
    drive.preflight(book, 2, env, NOW)
    assert seen == [2] and (Path(drive.ROOT) / "scripts" / "proof" / "preconditions.py").is_file()


def test_an_unreadable_book_is_said_and_never_crashes(tmp_path, env):
    lines = drive.preflight(tmp_path / "nobook", 2, env, NOW)
    assert any(l.startswith("preflight: book records not read") for l in lines) and not drive.refusals(lines)


def test_an_audit_that_breaks_never_stops_the_launch(book, env, monkeypatch):
    """Wave-3 review: the audit is the proof harness's file, still in build; any fault in it (here an
    AttributeError, the four caught types aside) is said, and never refuses or crashes the drive at t=0."""
    def broken(b, n):
        raise AttributeError("'NoneType' object has no attribute 'get'")
    monkeypatch.setattr(proof.pre, "audit", broken)
    lines = drive.preflight(book, 2, env, NOW)
    assert any(l.startswith("preflight: book records not read (AttributeError") for l in lines)
    assert not drive.refusals(lines)


def test_the_launch_refuses_at_t0_on_a_refuse_now_line(tmp_path, monkeypatch):
    said = []
    monkeypatch.setattr(drive, "git", lambda *a: "" if a[0] == "status" else "abc123")
    monkeypatch.setattr(drive.episode_home, "book_dir", lambda codex: tmp_path)
    monkeypatch.setattr(drive.episode_home, "home", lambda b, n: tmp_path / "ep02")
    monkeypatch.setattr(drive, "dry_check", lambda codex, n: [])
    monkeypatch.setattr(drive, "preflight", lambda *a, **k: ["refuse now: chapter_text chapters/ch_02.json"])
    monkeypatch.setattr(drive, "notify", said.append)
    assert drive.main("jekyll", 2) == 2
    assert "refuse now" in (tmp_path / "ep02" / "drive_run01.log").read_text(encoding="utf-8")
    rows = [json.loads(l) for l in (tmp_path / "ep02" / "drive.jsonl").read_text(encoding="utf-8").splitlines()]
    assert rows[-1]["refused"] == "preflight"
