"""A2 (fleet E, 2026-10-22): every take render, kept or lost, writes one row.

The step's `take_render` row times the whole GPU span, and shots.json keeps only the latest
draw's `render_s`, so a retake, a lost take and the card/CPU split inside step 09 had no
record (fleet E bench R1 had to estimate the split).  `takes/r2v/renders.jsonl` gets one
append-only row per claimed render: the index, the prompt id, the engine's seconds, the wait,
and why a lost one was lost."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("takes_rows", ROOT / "scripts" / "episode" / "takes_r2v.py")
takes = importlib.util.module_from_spec(_spec)
sys.modules["takes_rows"] = takes
_spec.loader.exec_module(takes)


def rows(room: Path) -> list[dict]:
    return [json.loads(line) for line in (room / "renders.jsonl").read_text(encoding="utf-8").splitlines()]


def test_three_renders_write_three_rows_with_their_engine_seconds(tmp_path, monkeypatch):
    def collect(c, prompt_id, out):
        if c["index"] == 2:
            raise RuntimeError("interrupted")
        return {**c, "render_s": 40.0 + c["index"], "waited_s": 41.5}
    monkeypatch.setattr(takes, "collect", collect)
    tickets = [({"index": i}, f"pid-{i}") for i in (1, 2, 3)]
    done, lost = takes.collect_all(tickets, lambda c: tmp_path / f"T{c['index']:02d}.mp4")
    got = rows(tmp_path)
    assert [(r["index"], r["prompt_id"], r["ok"]) for r in got] == [(1, "pid-1", True), (2, "pid-2", False),
                                                                    (3, "pid-3", True)]
    assert [r.get("render_s") for r in got] == [41.0, None, 43.0]
    assert got[1]["lost"] == "interrupted" and all(r["waited_s"] >= 0 for r in got)


def test_a_take_with_no_room_writes_no_row_and_still_renders(monkeypatch):
    monkeypatch.setattr(takes, "collect", lambda c, pid, out: {**c, "render_s": 1.0, "waited_s": 1.0})
    done, lost = takes.collect_all([({"index": 1}, "pid-1")], lambda c: None)
    assert [d["index"] for d in done] == [1] and lost == []
