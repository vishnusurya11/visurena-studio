"""Step 09 runs the tiny-face rung (09_08) once, after its face refine: the refine's refusals are
known only then.  A draw the rung kept changed a take's bytes, so the take eye signs again, the
staged inputs are walled again and the new bytes are refined (refine_rest); a rung that kept
nothing changes nothing and re-runs nothing.  And step 10 re-cuts when refine.json is newer than
the master: a refine decided after the cut (a rerun from 09's refine) reaches no picture otherwise."""
from __future__ import annotations

import os
from types import SimpleNamespace

from scripts.episode import step_09_shoot as step
from scripts.episode import step_10_edit as edit
from scripts.episode import tiny_face as tf


def ctx_at(tmp_path):
    return SimpleNamespace(home=tmp_path / "home", book_dir=tmp_path, number=1, budget=None,
                           log=lambda *a, **k: None, run_script=lambda *a, **k: 0)


def test_a_kept_draw_is_judged_walled_and_refined(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(tf, "rung", lambda ctx, flag, judge, checks=(): calls.append(("rung", flag)) or [1])
    for name in ("judge_takes", "inputs_wall", "refine_rest"):
        monkeypatch.setattr(step, name, lambda ctx, *a, n=name: calls.append((n,)))
    step.tiny_face_rung(ctx_at(tmp_path), "--approved=render")
    assert calls == [("rung", "--approved=render"), ("judge_takes",), ("inputs_wall",), ("refine_rest",)]


def test_a_rung_that_kept_nothing_runs_nothing_after(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(tf, "rung", lambda ctx, flag, judge, checks=(): [])
    for name in ("judge_takes", "inputs_wall", "refine_rest"):
        monkeypatch.setattr(step, name, lambda ctx, *a, n=name: calls.append(n))
    step.tiny_face_rung(ctx_at(tmp_path), "--approved=render")
    assert calls == []


def test_the_rung_runs_once_after_the_refine(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(step, "panel_refusals", lambda home: [])
    monkeypatch.setattr(step, "approved", lambda policy: "--approved=render")
    monkeypatch.setattr(step.gate_policy, "of", lambda stage, row: None)
    monkeypatch.setattr(step, "affordable", lambda ctx: (True, 0.0, 0.0))
    monkeypatch.setattr(step, "takes_of", lambda room: [room / "T01.mp4"])
    for name in ("shoot", "say_first_wall", "gpu_window", "judge_takes", "inputs_wall", "refine_rest", "tiny_face_rung"):
        monkeypatch.setattr(step, name, lambda *a, n=name: calls.append(n))
    ctx = ctx_at(tmp_path)
    ctx.stage = "episode"
    step.run(ctx)
    assert calls[-3:] == ["inputs_wall", "refine_rest", "tiny_face_rung"] and calls.count("tiny_face_rung") == 1


def test_a_refine_decided_after_the_cut_makes_step_10_cut_again(tmp_path):
    ctx = SimpleNamespace(home=tmp_path / "home", book_dir=tmp_path, number=1, extra=[])
    room = ctx.home / "takes" / "r2v"
    room.mkdir(parents=True)
    (room / "refine.json").write_text("{}", encoding="utf-8")
    assert room / "refine.json" in edit.inputs(ctx)
    os.utime(room / "refine.json", (1, 1))
    assert room / "refine.json" in edit.inputs(ctx)
