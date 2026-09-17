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
    """`attempts_of` and `next_fail` moved to `episode_home`: the judge and the
    renderer each had their own copy, both globbing only the flat take dir while
    the displaced rolls had moved to `attempts/`.
    See tests/test_every_attempt_is_found_and_none_overwritten.py."""
    from studio import episode_home
    for name in ("T01.mp4", "T01_retake1.mp4", "T01_fail1.mp4", "T02.mp4"):
        (tmp_path / name).write_bytes(b"x")
    assert [p.name for p in episode_home.attempts_of(tmp_path, 1)] == [
        "T01.mp4", "T01_fail1.mp4", "T01_retake1.mp4"]
    assert [p.name for p in episode_home.attempts_of(tmp_path, 9)] == []


def test_the_next_fail_name_does_not_overwrite_an_existing_one(tmp_path):
    from studio import episode_home
    assert episode_home.next_fail(tmp_path, 1).name == "T01_fail1.mp4"
    (tmp_path / "T01_fail1.mp4").write_bytes(b"x")
    (tmp_path / "T01_fail3.mp4").write_bytes(b"x")
    assert episode_home.next_fail(tmp_path, 1).name == "T01_fail4.mp4"


def test_settle_keeps_the_best_attempt_and_renames_the_one_it_displaces(tmp_path):
    """Iteration 4: the hand-renaming demoted T01_retake1 (0.5 s freeze) in favour of
    T01 (1.5 s), and left T18.dq.json describing a file that no longer existed."""
    kept, retake = tmp_path / "T01.mp4", tmp_path / "T01_retake1.mp4"
    kept.write_bytes(b"worse")
    retake.write_bytes(b"better")
    best = dq.settle(tmp_path, 1, {kept: make(False, 60.0), retake: make(True, 96.0)})
    assert best == retake
    assert kept.read_bytes() == b"better"
    # the displaced roll goes to the ATTEMPTS room, which is where
    # `migrate_layout` has been putting them and where `next_fail` now looks
    assert (tmp_path / "attempts" / "T01_fail1.mp4").read_bytes() == b"worse"
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


def test_a_retakes_record_carries_the_superseded_attempts():
    """Six of ep10's seven retaken takes have `attempts == [self]` (analyst H):
    the reviewer's labels applied to renders whose rows survived only in
    scratch logs.  Judged again after a re-render, the record prepends the
    prior record's attempts -- the earlier render first."""
    old = make(False, 64.7, take=3, name="T03.mp4")
    old.bytes = 1_000
    prior = dq.record(old, [old])
    new = make(True, 100.0, take=3, name="T03.mp4")
    new.bytes = 2_000
    rec = dq.record(new, [new], prior)
    assert [a["score"] for a in rec["attempts"]] == [64.7, 100.0]
    assert rec["attempts"][0]["superseded"] is True and "superseded" not in rec["attempts"][1]
    assert rec["score"] == 100.0 and rec["passed"] is True
    twice = dq.record(new, [new], rec)                            # the ledger keeps growing, never doubling
    assert [a["score"] for a in twice["attempts"]] == [64.7, 100.0]


def test_rejudging_the_same_render_replaces_its_entry_instead_of_doubling_it():
    """The same file, the same bytes, a new verdict (the gate changed): one entry."""
    v = make(True, 95.0, take=3, name="T03.mp4")
    v.bytes = 1_000
    prior = dq.record(v, [v])
    again = make(True, 100.0, take=3, name="T03.mp4")
    again.bytes = 1_000
    rec = dq.record(again, [again], prior)
    assert [a["score"] for a in rec["attempts"]] == [100.0]
    legacy = dq.record(again, [again], {"attempts": [{"file": "T03.mp4", "score": 90.0}]})   # ep10's records carry no bytes
    assert [a["score"] for a in legacy["attempts"]] == [100.0]


def test_the_prior_record_is_read_before_it_is_overwritten(tmp_path):
    assert dq.prior_record(tmp_path, 3) is None
    (tmp_path / "T03.dq.json").write_text('{"attempts": [{"file": "T03.mp4"}]}')
    assert dq.prior_record(tmp_path, 3) == {"attempts": [{"file": "T03.mp4"}]}


def test_the_printed_row_says_how_many_rows_can_fire():
    """"30/30 pass" is a statement about the rows with a value.  ep05-10:
    foreign, cut-landing and lip-sync fired 0 times on 172 renders; identity
    never measured (analyst H, change 6)."""
    v = make(True, 100.0, take=3)
    v.gates = [tv.Gate("churn", 3.6, True, False, "3.6 wide"), tv.Gate("identity", None, True, False, "not measured"),
               tv.Gate("lip-sync", None, True, True, "n/a narration")]
    row = dq.row(3, v)
    assert row.startswith("T03 PASS 100/100 (1 of 3 rows live)")
    assert dq.live_rows(v.gates) == (1, 3)


def test_the_plan_size_and_every_shots_motion_reach_the_record():
    ep = FakeEpisode()
    assert dq.planned_size(ep, {"shots": [0, 1], "index": 0}) == "medium_close"
    assert dq.planned_size(ep, {"index": 40}) == ""
    assert dq.planned_motions(ep, {"shots": [0, 1], "index": 0}) == ["Static shot; he speaks", "Tracking behind at walking pace"]
    assert dq.planned_motions(ep, {"index": 40}) == [""]


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


def test_the_placed_seconds_are_read_from_the_current_timeline_not_the_render_record():
    """ep11: shot 6's line was shortened AFTER the render so its shot would end
    before the take's hard cut at 3.3 s; the record still said 5.42 s and the
    DQ judged the cut inside the window three times over."""
    from scripts.episode import take_dq

    placed = {"shots": [{"index": 5, "seconds": 2.0}, {"index": 6, "seconds": 2.8}, {"index": 7, "seconds": 4.0}]}
    assert take_dq.current_placed(placed, {"index": 6, "shots": [6], "placed_seconds": 5.42}) == 2.8
    assert take_dq.current_placed(placed, {"index": 5, "shots": [5, 6], "placed_seconds": 9.0}) == 4.8
    assert take_dq.current_placed({"shots": []}, {"index": 9, "placed_seconds": 3.0}) == 3.0


def test_best_of_n_ignores_an_attempt_shorter_than_the_shot():
    """ep11 T15: the line grew after the render; the 8.25 s re-render lost the
    settle to the old 5.16 s file, which scored 100 and could not fill the shot."""
    from scripts.episode import take_dq

    short, long = object(), object()
    seconds = {short: 5.16, long: 8.25}
    keep = take_dq.fitting({short: "v", long: "v"}, placed=8.25, seconds_of=lambda p: seconds[p])
    assert list(keep) == [long]
    both = take_dq.fitting({short: "v", long: "v"}, placed=5.0, seconds_of=lambda p: seconds[p])
    assert set(both) == {short, long}
