"""A speaker's own best line is the best one in the BOOK, not in this episode.

MEASURED building episode 10. John Ferrier's line 27 rendered at 0.63-0.69
against the 0.70 floor eight times, under four wordings and three redo seeds.
From the third try the clone is meant to use the speaker's own best PASSED
line (>= 0.75) as its reference instead of the design clip -- and this episode
has none: Ferrier's two passing lines here sit at 0.71 and 0.74. So every
"third try" went back to the design clip and came back the same.

Episode 8 has him at 0.815. A cast voice is a book-level asset; the reference
rule should see the whole book.
"""
import json
import sys

sys.path.insert(0, "scripts/episode")


def episode_records(tmp_path, n, rows):
    room = tmp_path / "episodes" / f"ep{n:02d}" / "audio" / "lines"
    room.mkdir(parents=True)
    for r in rows:
        (tmp_path / r["rel_path"]).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / r["rel_path"]).write_bytes(b"wav")
    (room / "lines.json").write_text(json.dumps({"lines": rows}), encoding="utf-8")


def test_the_best_reference_comes_from_another_episode_when_this_one_has_none(tmp_path):
    import say_lines

    here = {14: {"speaker": "john_ferrier", "passed": True, "similarity": 0.712, "index": 14,
                 "rel_path": "episodes/ep10/audio/lines/l14.wav", "text": "Give us time."}}
    episode_records(tmp_path, 8, [
        {"index": 25, "speaker": "john_ferrier", "passed": True, "similarity": 0.815,
         "rel_path": "episodes/ep08/audio/lines/l25.wav", "text": "My name is John Ferrier."},
        {"index": 3, "speaker": "lucy_ferrier_child", "passed": True, "similarity": 0.90,
         "rel_path": "episodes/ep08/audio/lines/l03.wav", "text": "Where is mother?"},
    ])
    got = say_lines.book_best_reference(tmp_path, here, "john_ferrier", exclude=27)
    assert got is not None and got.name == "l25.wav"
    assert got.with_suffix(".txt").read_text(encoding="utf-8") == "My name is John Ferrier."


def test_this_episode_wins_when_it_has_a_line_over_the_floor(tmp_path):
    import say_lines

    here = {14: {"speaker": "john_ferrier", "passed": True, "similarity": 0.80, "index": 14,
                 "rel_path": "episodes/ep10/audio/lines/l14.wav", "text": "Give us time."}}
    (tmp_path / "episodes/ep10/audio/lines").mkdir(parents=True)
    (tmp_path / "episodes/ep10/audio/lines/l14.wav").write_bytes(b"wav")
    episode_records(tmp_path, 8, [
        {"index": 25, "speaker": "john_ferrier", "passed": True, "similarity": 0.815,
         "rel_path": "episodes/ep08/audio/lines/l25.wav", "text": "My name is John Ferrier."}])
    got = say_lines.book_best_reference(tmp_path, here, "john_ferrier", exclude=27)
    assert got is not None and got.name == "l25.wav", "the book's best, 0.815, beats this episode's 0.80"


def test_nothing_over_the_floor_anywhere_means_the_design_clip(tmp_path):
    import say_lines

    episode_records(tmp_path, 8, [
        {"index": 25, "speaker": "john_ferrier", "passed": True, "similarity": 0.72,
         "rel_path": "episodes/ep08/audio/lines/l25.wav", "text": "x"}])
    assert say_lines.book_best_reference(tmp_path, {}, "john_ferrier", exclude=27) is None
