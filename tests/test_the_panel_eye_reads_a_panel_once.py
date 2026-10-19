"""The panel eye reads a panel once per set of inputs (timeline debate 2026-10-18, P2; owner go):
Jekyll ep01's eye ran 4x (1076, 554, 676, 445 s = 46 of step 08's 66 min), once on unchanged
bytes, because every ladder rung re-read every panel.  A panel's read is cached by what it reads --
its bytes, its shot's size/faces/frame/at_rest, the setup's words, its references' bytes and the
judge's version; the board-wide checks (stored rows, repeats, place) stay live.  $0: fake tools."""
from __future__ import annotations

from PIL import Image

from studio.judges import panel_eye
from test_the_panel_eye_signs_flagged_with_its_faults_listed import board_of, tools


def counting():
    t, seen = tools(), {"n": 0}

    def detect(rgb):
        seen["n"] += 1
        return []
    return {**t, "detect": detect}, seen


def test_an_unchanged_panel_is_read_once(tmp_path):
    board, plan = board_of(tmp_path, [])
    t, seen = counting()
    first = panel_eye.judge(board.parent, plan, **t)
    again = panel_eye.judge(board.parent, plan, **t)
    assert seen["n"] == 1 and again.faults == first.faults and again.reads == first.reads == 1


def test_new_bytes_are_read_again(tmp_path):
    board, plan = board_of(tmp_path, [])
    t, seen = counting()
    panel_eye.judge(board.parent, plan, **t)
    Image.new("RGB", (64, 64), (200, 10, 10)).save(board / "shot_01.png")
    panel_eye.judge(board.parent, plan, **t)
    assert seen["n"] == 2


def test_a_reprosed_frame_is_read_again(tmp_path):
    # a reprose rung edits the shot's frame text: the same bytes are judged against new words
    board, plan = board_of(tmp_path, [])
    t, seen = counting()
    panel_eye.judge(board.parent, plan, **t)
    plan["shots"][0]["frame"] = "a yard at dusk"
    panel_eye.judge(board.parent, plan, **t)
    assert seen["n"] == 2


def test_the_stored_rows_are_never_cached(tmp_path):
    board, plan = board_of(tmp_path, [])
    t, _ = counting()
    assert panel_eye.judge(board.parent, plan, **t).passed
    from studio import episode_home
    episode_home.write_json(board / "panel_dq.json", [{"shot": 1, "passed": False, "flags": ["stacked"]}])
    assert not panel_eye.judge(board.parent, plan, **t).passed


def test_a_recut_room_with_a_new_mtime_gives_zero_new_reads(tmp_path):
    # P05: refs are keyed by their bytes, not their mtime -- a re-cut of identical pixels moves nothing
    import os
    board, plan = board_of(tmp_path, [])
    room = board.parent / "room.png"
    Image.new("RGB", (8, 8), (9, 9, 9)).save(room)
    shot, setup = plan["shots"][0], plan["setups"]["s"]
    before = panel_eye.read_key(shot, setup, board / "shot_01.png", [room])
    os.utime(room, ns=(1, room.stat().st_mtime_ns + 5_000_000_000))
    assert panel_eye.read_key(shot, setup, board / "shot_01.png", [room]) == before
    Image.new("RGB", (8, 8), (9, 9, 10)).save(room)
    assert panel_eye.read_key(shot, setup, board / "shot_01.png", [room]) != before
