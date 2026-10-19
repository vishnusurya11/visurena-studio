"""A 1024 tiny-face draw whose scale to the episode canvas fails never stays on disk claiming that
canvas (ship review, skeptic minor 2, 2026-10-19).  `collect` wrote the 1024 bytes as T<NN>.mp4 and
then scaled them in place: an ffmpeg failure left a 1024 take beside a graph that says `scaled_to`
the episode canvas, so take_currency read it current and every gate measured the wrong size.  Now
the scaled bytes land whole (ffmpeg writes beside the take, a finished file replaces it) and a
failed scale gives the take it replaced back, with its graph, and says so as a lost take.
ffmpeg and ComfyUI are fakes here."""
from __future__ import annotations

import json
import subprocess

import pytest

from scripts.episode import takes_r2v as tr

DRAW_GRAPH = {"8": {"class_type": "MiniMaxH3ReferenceToVideo", "inputs": {"width": 1024, "height": 1024}},
              "scaled_to": [768, 768]}


@pytest.fixture()
def landed(tmp_path, monkeypatch):
    """A room whose T01 was displaced for a 1024 draw (make_room), its draw graph written, the
    draw rendered on the engine; returns (card, out, the engine's video)."""
    monkeypatch.setattr(tr, "W", 768)
    monkeypatch.setattr(tr, "H", 768)
    room = tmp_path / "r2v"
    room.mkdir()
    out = room / "T01.mp4"
    out.write_bytes(b"old take")
    out.with_suffix(".graph.json").write_text(json.dumps({"old": "graph"}), encoding="utf-8")
    out.with_suffix(".dq.json").write_text('{"old": "dq"}', encoding="utf-8")
    card = {"index": 1, "render_canvas": [1024, 1024]}
    tr.make_room(card, out, {}, None)
    out.with_suffix(".graph.json").write_text(json.dumps(DRAW_GRAPH), encoding="utf-8")
    video = tmp_path / "engine" / "draw.mp4"
    video.parent.mkdir()
    video.write_bytes(b"1024 draw")
    for name, fake in (("wait_record", lambda pid, timeout=0: {}), ("outputs_of", lambda record: [video]),
                       ("ran_for", lambda record: 100.0), ("clip_seconds", lambda path: 5.5),
                       ("phases_of", lambda *a: None)):
        monkeypatch.setattr(tr, name, fake)
    return card, out, video


def failing_ffmpeg(argv, check=False, **kw):
    raise subprocess.CalledProcessError(1, argv, stderr="Conversion failed!")


def scaling_ffmpeg(argv, check=False, **kw):
    open(argv[-1], "wb").write(b"768 draw")
    return subprocess.CompletedProcess(argv, 0)


def test_a_failed_scale_gives_the_old_take_and_its_graph_back(landed, monkeypatch):
    card, out, video = landed
    monkeypatch.setattr(tr.subprocess, "run", failing_ffmpeg)
    with pytest.raises(RuntimeError, match="could not be scaled"):
        tr.collect(card, "pid", out)
    assert out.read_bytes() == b"old take"
    assert json.loads(out.with_suffix(".graph.json").read_text(encoding="utf-8")) == {"old": "graph"}
    assert out.with_suffix(".dq.json").exists()
    assert not list(out.parent.glob("T01_fit*.mp4")) and not list(out.parent.glob("T01_draw*.mp4"))


def test_a_failed_scale_is_a_lost_take_named_for_the_retake(landed, monkeypatch):
    card, out, video = landed
    monkeypatch.setattr(tr.subprocess, "run", failing_ffmpeg)
    done, lost = [], []
    tr.claim_one(card, "pid", lambda c: out, None, done, lost)
    assert done == [] and [c["index"] for c, _ in lost] == [1] and "scaled" in lost[0][1]


def test_a_scaled_draw_lands_whole_at_the_canvas(landed, monkeypatch):
    card, out, video = landed
    monkeypatch.setattr(tr.subprocess, "run", scaling_ffmpeg)
    record = tr.collect(card, "pid", out)
    assert out.read_bytes() == b"768 draw" and record["measured_seconds"] == 5.5
    assert json.loads(out.with_suffix(".graph.json").read_text(encoding="utf-8")) == DRAW_GRAPH
    assert not out.with_suffix(".dq.json").exists()                  # fresh bytes retire the old verdicts
    assert not list(out.parent.glob("T01_fit*.mp4"))


def test_a_draw_at_the_canvas_is_copied_as_before(landed, monkeypatch):
    card, out, video = landed
    card["render_canvas"] = [768, 768]
    monkeypatch.setattr(tr.subprocess, "run", failing_ffmpeg)       # never called
    tr.collect(card, "pid", out)
    assert out.read_bytes() == b"1024 draw"
