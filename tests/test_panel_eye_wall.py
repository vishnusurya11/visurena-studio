"""P05 item 3: the eye reads under a deadline (the panel_checks wall less the step's booked seconds,
K3).  Changed panels first, then uncached, then cached; at the deadline it stops, records the unread
panels as `unread_for_time` and never passes them.  $0: a fake clock and fake readers."""
from __future__ import annotations

from PIL import Image

from studio.judges import panel_eye
from test_the_eye_rereads_only_the_rewound_panels import N, board28, tools


def ticking(step=10.0):
    t = {"now": 0.0}

    def clock():
        t["now"] += step
        return t["now"]
    return clock


def test_stop_halts_reads_and_records_unread(tmp_path):
    home, _, plan = board28(tmp_path)
    seen = {"n": 0}
    got = panel_eye.judge(home, plan, deadline=55.0, clock=ticking(), **tools(seen))
    assert 0 < seen["n"] < N and got.evidence["unread_for_time"]
    assert len(got.evidence["unread_for_time"]) == N - seen["n"]
    unread = [f for f in got.faults if f.kind == "unread_for_time"]
    assert len(unread) == N - seen["n"] and not got.passed


def test_a_stop_logs_a_cap_line_and_never_parks(tmp_path, capsys):
    home, _, plan = board28(tmp_path)
    panel_eye.judge(home, plan, deadline=55.0, clock=ticking(), **tools({"n": 0}))
    assert "CAP panel_checks:" in capsys.readouterr().out


def test_the_next_window_reads_what_was_left_and_clears_the_marker(tmp_path):
    home, board, plan = board28(tmp_path)
    panel_eye.judge(home, plan, deadline=55.0, clock=ticking(), **tools({"n": 0}))
    assert panel_eye.unread_marker(board).exists()
    done = panel_eye.judge(home, plan, **tools({"n": 0}))
    assert done.evidence["unread_for_time"] == [] and done.passed
    assert not panel_eye.unread_marker(board).exists() and done.evidence["cache_hits"] > 0


def test_changed_panels_are_read_before_cached_ones(tmp_path):
    home, board, plan = board28(tmp_path)
    panel_eye.judge(home, plan, **tools({"n": 0}))
    Image.new("RGB", (64, 64), (1, 2, 3)).save(board / "shot_28.png")
    got = panel_eye.judge(home, plan, deadline=15.0, clock=ticking(), **tools({"n": 0}))
    assert got.evidence["reads"] == 1 and "shot_28" not in got.evidence["unread_for_time"]


def test_no_deadline_reads_everything(tmp_path):
    home, _, plan = board28(tmp_path)
    got = panel_eye.judge(home, plan, deadline=None, **tools({"n": 0}))
    assert got.evidence["unread_for_time"] == [] and got.passed


def test_the_deadline_is_the_wall_less_the_booked_seconds():
    assert panel_eye.deadline_left(3000.0, 1200.0) == 1800.0
    assert panel_eye.deadline_left(3000.0, 4000.0) == 0.0
