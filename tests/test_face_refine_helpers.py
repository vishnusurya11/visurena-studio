"""The face refine's small helpers, each pinned: a take's identity by its bytes, the
forward crop reader, the seed a crop renders with, what is owed and its price, the
live engine's three calls (with ComfyUI faked underneath) and the command line."""
from __future__ import annotations

import json
import subprocess

import numpy as np
import pytest

from scripts.episode import face_refine as cli
from studio import comfy, face_paste, face_refine as fr


def test_a_takes_identity_is_its_bytes(tmp_path):
    a, b = tmp_path / "a.mp4", tmp_path / "b.mp4"
    a.write_bytes(b"one")
    b.write_bytes(b"two")
    assert len(face_paste.sha8(a)) == 8 and face_paste.sha8(a) != face_paste.sha8(b)
    assert face_paste.sha8(tmp_path / "missing.mp4") == ""


def test_the_crop_reader_reads_forward_and_holds_its_last_frame(tmp_path):
    path = tmp_path / "c.mp4"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "color=c=white:s=32x32:r=24:d=0.25",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", str(path)], check=True)
    r = face_paste.CropReader(path)
    assert r.frame(0).shape == (32, 32, 3) and r.frame(2) is not None
    assert np.array_equal(r.frame(99), r.frame(99))


def test_a_crop_renders_with_the_seed_its_take_did(tmp_path):
    (tmp_path / "T04.graph.json").write_text(json.dumps({"12": {"inputs": {"noise_seed": 9001}}}))
    assert cli.take_seed(tmp_path, {"seed": 5}, 4) == 9001
    assert cli.take_seed(tmp_path, {"seed": 5}, 6) == 5


def test_what_is_owed_is_priced_by_its_staged_faces_and_frames(tmp_path, monkeypatch):
    room = tmp_path / "room"
    room.mkdir()
    (room / "prompts.json").write_text(json.dumps([{"index": 2, "faces": ["a", "b"], "frames": 96}]))
    monkeypatch.setattr(cli, "room_of", lambda book, n: room)
    monkeypatch.setattr(cli, "pending", lambda book, n, among=None: [2])
    assert cli.owed(tmp_path, 1) == {2: pytest.approx(fr.price(2, 96))}


def test_a_decision_is_current_only_for_the_same_bytes(tmp_path):
    (tmp_path / "T01.mp4").write_bytes(b"x")
    sha = face_paste.sha8(tmp_path / "T01.mp4")
    assert cli.current({"T01": {"status": "refined", "take_sha8": sha}}, tmp_path, 1)
    assert not cli.current({"T01": {"status": "refined", "take_sha8": "0" * 8}}, tmp_path, 1)
    assert not cli.current({"T01": {"status": "cut", "take_sha8": sha}}, tmp_path, 1)


def test_the_live_engine_stages_submits_and_waits_through_the_client(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(comfy, "stage_image", lambda p: calls.append("stage") or "x.png")
    monkeypatch.setattr(comfy, "submit", lambda g: calls.append("submit") or "id")
    record = {"outputs": {"17": {"images": [{"filename": "o.mp4", "subfolder": "", "type": "output"}]}}}
    monkeypatch.setattr(comfy, "wait_record", lambda pid, poll=5.0: calls.append("wait") or record)
    engine = cli.Comfy()
    assert engine.stage(tmp_path / "s.png") == "x.png" and engine.submit({}) == "id"
    assert engine.wait("id") == {"17": [comfy.COMFY_ROOT / "output" / "o.mp4"]}
    assert calls == ["stage", "submit", "wait"]


def test_the_command_line_takes_the_book_the_episode_the_takes_and_the_clock_row(monkeypatch):
    seen = {}
    monkeypatch.setattr(cli.episode_home, "book_dir", lambda codex: f"/books/{codex}")
    monkeypatch.setattr(cli, "refine", lambda book, n, indices, within="": seen.update(
        book=book, n=n, indices=indices, within=within) or {})
    assert cli.main(["face_refine.py", "codex", "1", "0", "7", "--within=takes"]) == 0
    assert seen == {"book": "/books/codex", "n": 1, "indices": [0, 7], "within": "takes"}


def test_the_graph_fills_the_f2_workflow_by_its_manifest():
    person = fr.Person(1, "a", "Mr. A", "Grey hair. <Picture 2> defines this man alone.", "refs/characters/a/s.png")
    g = cli.graph_for(person, "detailed_description:\nInk.", 39, 11,
                      {"sheet": "s.png", "crop": "c.mp4", "audio": "g.wav"}, "face_refine/T00_p0")
    assert (g["30"]["inputs"]["file"], g["21"]["inputs"]["audio"], g["18"]["inputs"]["image"]) == ("c.mp4", "g.wav", "s.png")
    assert g["9"]["inputs"]["denoise"] == fr.DENOISE and g["8"]["inputs"]["length"] == 39
    assert "<Picture 1> defines this man alone" in g["8"]["inputs"]["prompt"]


@pytest.mark.local
def test_the_loose_detector_loads():
    from studio import face_track
    assert face_track.loose_detector()(np.zeros((64, 64, 3), np.uint8)) == []
