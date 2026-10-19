"""P08 item 6: for a take with archived draws (attempts/T<nn>_fail*.mp4; ep01 T21, T24) the
terminal measures every draw through an injected runner, keeps the fewest hard rows then the lowest
Se, restores the winner to T<nn>.mp4 and logs it.  The last draw is not the best by being last."""
from __future__ import annotations

from types import SimpleNamespace

from studio import take_ladder as tl
from studio.judges.verdict import Fault, Verdict


def room_with(tmp_path, names):
    room = tmp_path / "takes" / "r2v"
    (room / "attempts").mkdir(parents=True)
    (room / "T21.mp4").write_bytes(b"last")
    for n, body in names.items():
        (room / "attempts" / n).write_bytes(body)
    return room


def runner(scores):
    return lambda path: scores[path.read_bytes()]


def test_the_lowest_se_among_equal_hard_rows_is_restored_and_the_last_is_archived(tmp_path):
    room = room_with(tmp_path, {"T21_fail1.mp4": b"first", "T21_fail2.mp4": b"second"})
    scores = {b"last": {"hard": 1, "Se": 3.34}, b"first": {"hard": 1, "Se": 3.55}, b"second": {"hard": 1, "Se": 2.9}}
    said = tl.best_draw(room, 21, runner(scores))
    assert (room / "T21.mp4").read_bytes() == b"second"
    assert b"last" in {p.read_bytes() for p in (room / "attempts").glob("T21_fail*.mp4")}     # nothing lost
    assert "T21" in said and "2.9" in said


def test_fewer_hard_rows_beat_a_lower_se(tmp_path):
    room = room_with(tmp_path, {"T21_fail1.mp4": b"first"})
    scores = {b"last": {"hard": 0, "Se": 4.0}, b"first": {"hard": 1, "Se": 1.0}}
    assert tl.best_draw(room, 21, runner(scores)) == ""
    assert (room / "T21.mp4").read_bytes() == b"last"


def test_a_tie_keeps_the_current_take(tmp_path):
    room = room_with(tmp_path, {"T21_fail1.mp4": b"first"})
    scores = {b"last": {"hard": 1, "Se": 3.0}, b"first": {"hard": 1, "Se": 3.0}}
    assert tl.best_draw(room, 21, runner(scores)) == ""


def test_a_take_with_no_draws_is_left_alone_and_never_measured(tmp_path):
    room = room_with(tmp_path, {})
    assert tl.best_draw(room, 21, lambda p: 1 / 0) == ""


def test_the_winners_dq_record_is_written_when_the_runner_hands_one_back(tmp_path):
    room = room_with(tmp_path, {"T21_fail1.mp4": b"first"})
    scores = {b"last": {"hard": 2, "Se": 3.0}, b"first": {"hard": 1, "Se": 3.0, "dq": {"take_sha8": "abc"}}}
    tl.best_draw(room, 21, runner(scores))
    assert '"abc"' in (room / "T21.dq.json").read_text(encoding="utf-8")


def test_terminal_for_runs_the_draws_of_every_faulted_take(tmp_path):
    room = room_with(tmp_path, {"T21_fail1.mp4": b"first"})
    ctx = SimpleNamespace(home=tmp_path, book_dir=tmp_path, unit="ep01", log=lambda *a, **k: None)
    scores = {b"last": {"hard": 1, "Se": 3.5}, b"first": {"hard": 1, "Se": 2.0}}
    plan = SimpleNamespace(lines=[], turn=lambda: SimpleNamespace(index=98), button=lambda: SimpleNamespace(shot=99))
    v = Verdict(judge="take_eye", version="1", passed=False, confidence=1.0, reads=1,
                faults=[Fault(kind="warp", where="T21")])
    tl.terminal_for(ctx, plan, draws=runner(scores))(v)
    assert (room / "T21.mp4").read_bytes() == b"first"
