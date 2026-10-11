"""A take is saved at CRF 10, not ffmpeg's default 23 (bench phase 0, 2026-10-10):
the shipped takes were 0.9-2.5 Mb/s and banded in the dark before any re-encode."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from studio import comfy

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("takes_r2v_crf", ROOT / "scripts" / "episode" / "takes_r2v.py")
takes = importlib.util.module_from_spec(spec)
sys.modules["takes_r2v_crf"] = takes
spec.loader.exec_module(takes)


def save_node(graph: dict) -> dict:
    return next(n["inputs"] for n in graph.values() if n.get("class_type") == "SaveVideo")


def test_the_take_workflow_sets_its_own_crf():
    template, _ = comfy.load_workflow(takes.BASE)
    assert save_node(template).get("format.codec.encoding.crf", 23) <= 12
