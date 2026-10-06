"""The Take strips section carries what actually happened to the takes: every
ladder terminal's own note out of learnings.jsonl, and the roll count read off
the attempts room -- and a wardrobe drift row, when one was measured, lands
under Flags with the signed line naming its file."""
from __future__ import annotations

from scripts.publish import signoff
from studio import episode_home, publish_lock
from studio.learnings import Learning, record
from tests.publish_fixtures import book_with, episode_with


def test_a_terminal_and_the_roll_count_reach_the_strips(tmp_path):
    home, sha8 = episode_with(book_with(tmp_path))
    record(home / "learnings.jsonl",
           Learning(step="09", gate="TAKE", action="keep_best", terminal=True,
                    note="kept the best of 3; drift 0.41"))
    folder = episode_home.takes_under(home, "r2v")
    (folder / "attempts").mkdir(exist_ok=True)
    (folder / "attempts" / "T01_fail1.mp4").write_bytes(b"lost")
    (folder / "attempts" / "T01_fail2.mp4").write_bytes(b"lost again")
    text = signoff.write(home, sha8).read_text(encoding="utf-8")
    strips = publish_lock.sections(text)["Take strips"]
    assert "kept the best of 3; drift 0.41" in strips
    assert "T01: dq 88.0 pass, content pass, 3 roll(s)" in strips


def test_a_wardrobe_drift_row_lands_under_flags(tmp_path):
    home, sha8 = episode_with(book_with(tmp_path))
    episode_home.write_json(home / "review" / f"wardrobe_{sha8}.json",
                            [{"at": 31.0, "character": "narrator",
                              "expected": ["brown felt hat"], "seen": ["boater"],
                              "missing": ["brown felt hat"]}])
    text = signoff.write(home, sha8).read_text(encoding="utf-8")
    flags = publish_lock.sections(text)["Flags"]
    assert "narrator" in flags and "boater" in flags and "brown felt hat" in flags
    assert f"wardrobe_{sha8}.json" in text  # the signed line names its input


def test_an_episode_with_nothing_open_still_writes_a_flags_section(tmp_path):
    home, sha8 = episode_with(book_with(tmp_path))
    text = signoff.write(home, sha8).read_text(encoding="utf-8")
    assert len(publish_lock.sections(text)["Flags"]) >= publish_lock.MIN_SECTION
