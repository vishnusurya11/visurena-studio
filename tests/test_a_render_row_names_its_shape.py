"""Fleet C A1 (2026-10-22): a render's rows say what was rendered and what the engine served from cache.

The bench could not price the gap between the 33 min first-draw price and ep01's render spans
because no row said a render's shape (frames, refs, voice or silence, model, canvas) or whether it
was a first draw or a retake; and a B job run right after its A reused A's encodes
(`execution_cached`, 7-10 s), which no row recorded (skeptic M3).  renders.jsonl now carries the
card's shape and its retake round; phases.jsonl carries the classes the engine served from cache."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from studio import take_phases as tp

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("takes_shape", ROOT / "scripts" / "episode" / "takes_r2v.py")
takes = importlib.util.module_from_spec(_spec)
sys.modules["takes_shape"] = takes
_spec.loader.exec_module(takes)

RETAKE = {"index": 13, "frames": 141, "model": "singularity_v13_int8.safetensors", "refs": ["P13", "jekyll", "lab"],
          "audio": [["L05.wav", 0.0]], "render_canvas": [768, 768], "tries": 2, "retake_why": "frozen"}


def test_a_retake_row_carries_its_shape_and_round():
    row = takes.render_row(RETAKE, "pid-13", 0.0, {"render_s": 88.0})
    assert {k: row[k] for k in ("frames", "model", "refs", "audio", "canvas", "tries", "retake_why")} == {
        "frames": 141, "model": "singularity_v13_int8.safetensors", "refs": 3, "audio": True,
        "canvas": [768, 768], "tries": 2, "retake_why": "frozen"}


def test_a_first_draw_on_silence_is_round_zero_with_no_voice():
    row = takes.render_row({"index": 2, "frames": 56, "refs": [], "audio": "silence"}, "pid-2", 0.0, None, "lost")
    assert row["tries"] == 0 and row["audio"] is False and row["refs"] == 0 and "retake_why" not in row


RECORD = {"status": {"messages": [["execution_start", {"timestamp": 1000}],
                                  ["execution_cached", {"nodes": ["1", "5", "9"]}],
                                  ["execution_success", {"timestamp": 61000}]]},
          "prompt": [0, "pid", {"1": {"class_type": "UNETLoader"}, "5": {"class_type": "CLIPTextEncode"},
                                "9": {"class_type": "CLIPTextEncode"}, "12": {"class_type": "KSampler"}}]}


def test_the_phase_row_names_the_classes_served_from_cache():
    p = tp.phases(RECORD, [])
    assert p["cached"] == {"CLIPTextEncode": 2, "UNETLoader": 1} and p["cached_n"] == 3


def test_a_record_with_no_cache_line_names_none():
    p = tp.phases({"status": {"messages": []}, "prompt": [0, "pid", {}]}, [])
    assert p["cached"] == {} and p["cached_n"] == 0
