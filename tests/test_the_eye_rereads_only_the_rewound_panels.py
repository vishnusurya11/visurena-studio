"""P05: on a 28-panel board the eye re-reads only the panels whose inputs moved.  The key holds the
ask text (SIZE_ASK, CAPTION, the DWPose workflow); a transient failure (Unreadable, TimeoutError) is
never kept.  Jekyll ep01 ran four whole-board passes (1076/554/676/445 s) for want of this.  $0: fakes."""
from __future__ import annotations

import json

from PIL import Image

from studio import episode_home
from studio.judges import panel_eye

N = 28


def board28(tmp_path):
    home = tmp_path / "book" / "episodes" / "ep01"
    board = home / "storyboard"
    board.mkdir(parents=True)
    for i in range(1, N + 1):
        Image.new("RGB", (64, 64), (i * 5, 50, 50)).save(board / f"shot_{i:02d}.png")
    episode_home.write_json(board / "panel_dq.json", [{"shot": i, "passed": True, "flags": []} for i in range(1, N + 1)])
    episode_home.write_json(board / "panel_content.json", [{"shot": i, "passed": True, "faults": []} for i in range(1, N + 1)])
    plan = {"setups": {"s": {"described": "a yard"}},
            "shots": [{"index": i, "setup": "s", "size": "wide", "faces": [], "frame": "a yard"} for i in range(1, N + 1)]}
    return home, board, plan


def tools(seen, size_said=None, pose=None):
    def run(workflow, values, timeout=0.0):
        if workflow == panel_eye.CAPTION:
            return size_said or '{"size": "wide", "pictures": 1}'
        if workflow == panel_eye.keypoints.WORKFLOW and pose == "timeout":
            raise TimeoutError("queued behind a render")
        return "[]"

    def detect(rgb):
        seen["n"] += 1
        return []
    return dict(run=run, stage=lambda p: getattr(p, "name", str(p)), reader=lambda p: [],
                detect=detect, embed=lambda rgb, box: None)


def test_two_rewritten_panels_make_two_reads_and_26_hits(tmp_path):
    home, board, plan = board28(tmp_path)
    seen = {"n": 0}
    first = panel_eye.judge(home, plan, **tools(seen))
    assert seen["n"] == N and first.evidence["reads"] == N and first.evidence["cache_hits"] == 0
    for i in (3, 20):
        Image.new("RGB", (64, 64), (250, i, 9)).save(board / f"shot_{i:02d}.png")
    seen["n"] = 0
    again = panel_eye.judge(home, plan, **tools(seen))
    assert seen["n"] == 2 and again.evidence["reads"] == 2 and again.evidence["cache_hits"] == 26
    assert again.reads == N        # the verdict still covers every panel


def test_the_evidence_names_the_seconds_per_reader(tmp_path):
    home, _, plan = board28(tmp_path)
    got = panel_eye.judge(home, plan, **tools({"n": 0})).evidence
    assert set(got["seconds"]) >= {"keypoints", "size", "faces", "lettering"} and got["unread_for_time"] == []


def test_an_ask_text_change_reads_again(tmp_path, monkeypatch):
    home, _, plan = board28(tmp_path)
    seen = {"n": 0}
    panel_eye.judge(home, plan, **tools(seen))
    monkeypatch.setattr(panel_eye, "SIZE_ASK", panel_eye.SIZE_ASK + " Be brief.")
    seen["n"] = 0
    panel_eye.judge(home, plan, **tools(seen))
    assert seen["n"] == N


def test_a_changed_keypoint_workflow_reads_again(tmp_path, monkeypatch):
    home, _, plan = board28(tmp_path)
    seen = {"n": 0}
    panel_eye.judge(home, plan, **tools(seen))
    monkeypatch.setattr(panel_eye.keypoints, "WORKFLOW", "image_dwpose_keypoints_v2")
    seen["n"] = 0
    panel_eye.judge(home, plan, **tools(seen))
    assert seen["n"] == N


def test_an_unreadable_size_is_asked_again(tmp_path):
    home, _, plan = board28(tmp_path)
    seen = {"n": 0}
    first = panel_eye.judge(home, plan, **tools(seen, size_said="not json at all"))
    assert first.evidence["cache_hits"] == 0
    seen["n"] = 0
    again = panel_eye.judge(home, plan, **tools(seen))
    assert seen["n"] == N and again.evidence["cache_hits"] == 0


def test_a_timed_out_keypoint_ask_is_never_kept(tmp_path):
    home, _, plan = board28(tmp_path)
    seen = {"n": 0}
    panel_eye.judge(home, plan, **tools(seen, pose="timeout"))
    seen["n"] = 0
    panel_eye.judge(home, plan, **tools(seen))
    assert seen["n"] == N


def test_the_evidence_reaches_timing_jsonl(tmp_path):
    home, _, plan = board28(tmp_path)
    ev = panel_eye.judge(home, plan, **tools({"n": 0})).evidence
    note = panel_eye.timing_note(ev)
    assert "reads=28" in note and "cache_hits=0" in note and json.loads(note.split("|", 1)[1])["reads"] == 28
