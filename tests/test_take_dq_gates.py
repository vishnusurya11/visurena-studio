"""take_dq wiring: one verdict per attempt, one score, and --attempts keeps the
best file automatically.  No video is decoded, no model is loaded, nothing spends.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
from types import SimpleNamespace

from studio import take_verdict as tv

spec = importlib.util.spec_from_file_location(
    "take_dq", Path(__file__).resolve().parents[1] / "scripts" / "episode" / "take_dq.py")
dq = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dq)


def make(passed: bool, score: float, take: int = 1, attempt: int = 0, name: str = "T01.mp4") -> tv.TakeVerdict:
    v = tv.TakeVerdict(take, attempt, name, 5.0, "narration", [], [])
    v.score, v.passed = score, passed
    return v


class FakeEpisode:
    """The plan, without pydantic: the shots and lines take_dq reads."""
    def __init__(self):
        self.lines = [SimpleNamespace(kind="dialogue", shot=0, text="Watson? Good Lord, man."),
                      SimpleNamespace(kind="narration", shot=1, text="I had neither kith nor kin.")]
        self.shots = {0: SimpleNamespace(index=0, size="medium_close", motion="Static shot; he speaks"),
                      1: SimpleNamespace(index=1, size="medium", motion="Tracking behind at walking pace")}

    def shot(self, index):
        return self.shots[index]


def test_segment_kinds_come_from_the_plan():
    kinds = dq.segment_kinds(FakeEpisode(), [("Q00_0.png", 0), ("Q01_0.png", 60), ("Q01_0E.png", 100)])
    assert kinds == {"Q00_0.png": "dialogue", "Q01_0.png": "track", "Q01_0E.png": "track"}


def test_a_cell_whose_shot_is_not_in_the_plan_is_a_hold():
    assert dq.segment_kinds(FakeEpisode(), [("Q99_0.png", 0)]) == {"Q99_0.png": "hold"}


def test_the_line_text_of_a_dialogue_take_is_what_the_wer_is_scored_against():
    ep = FakeEpisode()
    assert dq.line_text(ep, {"lane": "dialogue", "shots": [0]}) == "Watson? Good Lord, man."
    assert dq.line_text(ep, {"lane": "narration", "shots": [1]}) == ""


def test_attempts_of_lists_the_kept_file_first(tmp_path):
    for name in ("T01.mp4", "T01_retake1.mp4", "T01_fail1.mp4", "T02.mp4"):
        (tmp_path / name).write_bytes(b"x")
    assert [p.name for p in dq.attempts_of(tmp_path, 1)] == ["T01.mp4", "T01_fail1.mp4", "T01_retake1.mp4"]
    assert [p.name for p in dq.attempts_of(tmp_path, 9)] == []


def test_the_next_fail_name_does_not_overwrite_an_existing_one(tmp_path):
    assert dq.next_fail(tmp_path, 1).name == "T01_fail1.mp4"
    (tmp_path / "T01_fail1.mp4").write_bytes(b"x")
    (tmp_path / "T01_fail3.mp4").write_bytes(b"x")
    assert dq.next_fail(tmp_path, 1).name == "T01_fail4.mp4"


def test_settle_keeps_the_best_attempt_and_renames_the_one_it_displaces(tmp_path):
    """Iteration 4: the hand-renaming demoted T01_retake1 (0.5 s freeze) in favour of
    T01 (1.5 s), and left T18.dq.json describing a file that no longer existed."""
    kept, retake = tmp_path / "T01.mp4", tmp_path / "T01_retake1.mp4"
    kept.write_bytes(b"worse")
    retake.write_bytes(b"better")
    best = dq.settle(tmp_path, 1, {kept: make(False, 60.0), retake: make(True, 96.0)})
    assert best == retake
    assert kept.read_bytes() == b"better"
    assert (tmp_path / "T01_fail1.mp4").read_bytes() == b"worse"
    assert not retake.exists()


def test_settle_leaves_the_kept_file_alone_when_it_is_already_the_best(tmp_path):
    kept, retake = tmp_path / "T01.mp4", tmp_path / "T01_retake1.mp4"
    kept.write_bytes(b"good")
    retake.write_bytes(b"worse")
    best = dq.settle(tmp_path, 1, {kept: make(True, 99.0), retake: make(False, 20.0)})
    assert best == kept and kept.read_bytes() == b"good" and retake.exists()


def test_the_printed_row_names_the_verdict_the_score_and_the_file():
    v = make(False, 47.5, take=17)
    v.gates = [tv.Gate("frozen-at-start", 5.75, False, True, "5.75s", 40.0)]
    row = dq.row(17, v, kept="T17_fail1.mp4", attempts=3)
    assert row.startswith("T17 FAIL 47")
    assert "frozen-at-start 5.75s HARD" in row and "kept T17_fail1.mp4 of 3" in row


def test_the_record_carries_every_attempt_and_the_budget_flag():
    best = make(False, 40.0, take=1, attempt=0, name="T01.mp4")
    also = make(False, 30.0, take=1, attempt=1, name="T01_retake1.mp4")
    record = dq.record(best, [best, also])
    assert record["passed"] is False and record["score"] == 40.0
    assert [a["file"] for a in record["attempts"]] == ["T01.mp4", "T01_retake1.mp4"]
    assert record["budget_spent"] is False                  # one retake left of RETAKE_BUDGET = 2
    three = dq.record(best, [best, also, make(False, 20.0, name="x.mp4")])
    assert three["budget_spent"] is True


def test_the_record_keeps_foreign_and_off_beat_scalar_for_the_run_cards():
    """runcards.dq_row prints `foreign` and `off_beat` as numbers; the sampled rows
    move to `foreign_samples` so the card keeps rendering after the ladder lands."""
    v = make(False, 60.0)
    v.foreign = [{"foreign": True}, {"foreign": False}]
    v.segments = [tv.SegmentReport("Q01_0.png", "Q01_0.png", 0.0, 3.0, 0.0, 0.0, "hold", 1.0, 1.0, True, 0),
                  tv.SegmentReport("Q01_1.png", "Q01_1.png", 3.0, 6.0, 0.0, 0.0, "hold", 0.3, 1.0, False, 34)]
    row = dq.record(v, [v])
    assert row["foreign"] == 1 and row["off_beat"] == 1
    assert len(row["foreign_samples"]) == 2


def test_a_takes_own_end_picture_is_not_a_foreign_picture():
    """A segment travels from its cell to that cell's END picture, and since the
    END pins were removed the END cell is no longer an anchor -- so the gate was
    reading a take ARRIVING WHERE IT WAS SENT as a picture from another shot.

    MEASURED on iteration 5: T02 matched Q02_0E at 0.988 and T03 matched Q03_0E
    at 0.821, and both takes were failed for it and queued for a retake."""
    anchors = [("Q02_0.png", 0), ("Q02_1.png", 94)]
    assert dq.own_family(anchors) == {"Q02_0.png", "Q02_0E.png", "Q02_1.png", "Q02_1E.png"}


def test_another_shots_picture_is_still_foreign():
    family = dq.own_family([("Q02_0.png", 0)])
    assert "Q10_1.png" not in family and "Q10_1E.png" not in family
