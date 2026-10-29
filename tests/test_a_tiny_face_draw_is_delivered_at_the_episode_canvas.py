"""The tiny-face rung's draw (face-blur round 2, BENCH_R2 lead 5, arm A3c) renders on a NEW graph,
the Spark take graph at 1024x1024 (comfy_studio `..._spark_zechengtang_sq1024_visurena.json`; the base
file is never edited), and lands as T<NN>.mp4 at the EPISODE's canvas: every gate, the cut and the
paste read a take at its canvas.  Its graph.json says so (`scaled_to`), so the take is current to the
canvas it is, never re-rendered as a stale 1024 take.  No GPU, no ffmpeg run here."""
from __future__ import annotations

import json
from pathlib import Path

from scripts.episode import takes_r2v as tr
from studio import take_currency


def write_take(folder: Path, graph: dict) -> Path:
    take = folder / "T01.mp4"
    take.write_bytes(b"take")
    take.with_suffix(".graph.json").write_text(json.dumps(graph), encoding="utf-8")
    return take


RENDER = {"8": {"class_type": "MiniMaxH3ReferenceToVideo", "inputs": {"prompt": "p", "width": 1024, "height": 1024}}}


def test_a_scaled_draw_reads_at_the_canvas_it_was_delivered_at(tmp_path):
    take = write_take(tmp_path, {**RENDER, "scaled_to": [768, 768]})
    assert take_currency.recorded_canvas(take) == (768, 768)
    assert take_currency.is_current("p", take, canvas=(768, 768))


def test_an_unscaled_graph_still_reads_its_render_node(tmp_path):
    take = write_take(tmp_path, RENDER)
    assert take_currency.recorded_canvas(take) == (1024, 1024)
    assert not take_currency.is_current("p", take, canvas=(768, 768))


def test_only_a_retaken_card_of_a_tiny_face_pass_renders_on_the_1024_graph(monkeypatch):
    monkeypatch.setattr(tr, "TINY_FACE", True)
    assert tr.render_plan(True) == (tr.TINY_FACE_BASE, (1024, 1024))
    assert tr.render_plan(False) == ("", None)
    monkeypatch.setattr(tr, "TINY_FACE", False)
    assert tr.render_plan(True) == ("", None)


def test_the_1024_graph_is_the_spark_take_graph_by_name():
    assert tr.TINY_FACE_BASE == tr.WIDE_BASE + "_sq1024_visurena"
    assert tr.TINY_FACE_BASE in tr.MODELS and tr.steps_for(tr.TINY_FACE_BASE) == tr.STEPS


def test_the_flag_turns_the_pass_on():
    tr._set_tiny_face(["takes_r2v.py", "book", "1", "--tiny-face"])
    try:
        assert tr.TINY_FACE
    finally:
        tr._set_tiny_face([])
    assert not tr.TINY_FACE


def test_the_card_says_what_it_rendered_on_and_at_what_size():
    card = {"index": 1, "workflow": tr.WIDE_BASE + " + anchors"}
    tr.mark_tiny(card, tr.TINY_FACE_BASE, (1024, 1024))
    assert card["workflow"] == tr.TINY_FACE_BASE + " + anchors" and card["render_canvas"] == [1024, 1024]
    assert card["model"] == tr.MODELS[tr.TINY_FACE_BASE]


def test_the_written_graph_carries_the_episode_canvas_and_the_submitted_one_does_not(monkeypatch):
    monkeypatch.setattr(tr, "W", 768)
    monkeypatch.setattr(tr, "H", 768)
    assert tr.recorded(RENDER, (1024, 1024)) == {**RENDER, "scaled_to": [768, 768]}
    assert tr.recorded(RENDER, None) is RENDER and "scaled_to" not in RENDER


def test_the_draw_is_scaled_lanczos_to_the_canvas_with_its_sound_copied(tmp_path):
    argv = tr.fit_argv(tmp_path / "a.mp4", tmp_path / "b.mp4", 768, 768)
    assert "scale=768:768:flags=lanczos" in argv and argv[argv.index("-c:a") + 1] == "copy"
    assert argv[argv.index("-crf") + 1] == "10" and argv[-1] == str(tmp_path / "b.mp4")


def test_only_a_card_rendered_off_the_canvas_is_scaled(monkeypatch):
    monkeypatch.setattr(tr, "W", 768)
    monkeypatch.setattr(tr, "H", 768)
    assert tr.off_canvas({"render_canvas": [1024, 1024]})
    assert not tr.off_canvas({"render_canvas": [768, 768]}) and not tr.off_canvas({})
