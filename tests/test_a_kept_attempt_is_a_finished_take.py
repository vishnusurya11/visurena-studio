"""A kept attempt is a finished take, and no take is ever overwritten.

Jekyll HEL ep01 v2 finish (2026-10-15): `take_dq --attempts` swapped an older
attempt into `T<NN>.mp4`.  The file kept its old mtime while `T<NN>.graph.json`
(the newer, displaced render's) was minutes younger, so `take_currency` read the
kept take as an interrupted render.  The next `takes_r2v` -- and step 11's
retake round, which runs the step-09 renderer -- re-rendered it over the kept
file, with no archive and with `tries` reset to try 0's seed.  T22's G-GAIT cure
and T19's 87.6 were lost that way, T19 twice.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path
from types import SimpleNamespace

from scripts.episode import take_dq
from scripts.episode import takes_r2v
from scripts.episode import step_09_shoot as shoot
from studio import episode_home, take_currency as tc
from studio import take_verdict as tv

HOUR = 3600.0


def verdict(passed: bool, score: float) -> tv.TakeVerdict:
    v = tv.TakeVerdict(22, 0, "T22.mp4", 5.0, "narration", [], [])
    v.score, v.passed = score, passed
    return v


def graph(prompt: str) -> dict:
    return {"5": {"class_type": tc.RENDER_NODE, "inputs": {"prompt": prompt, "width": 768, "height": 768}}}


def put(path: Path, body: bytes | dict, age: float) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(body).encode() if isinstance(body, dict) else body
    path.write_bytes(data)
    t = time.time() - age
    os.utime(path, (t, t))
    return path


def jekyll_room(room: Path, own_graph: bool) -> Path:
    """T22 as the finish left it: a newer failed render kept, the cured render
    an hour older in attempts/, the graph beside T22 the newer render's."""
    put(room / "T22.mp4", b"newer, failed", 120)
    put(room / "T22.graph.json", graph("walk on"), 400)
    cured = put(room / "attempts" / "T22_fail1.mp4", b"cured, 95", HOUR)
    if own_graph:
        put(room / "attempts" / "T22_fail1.graph.json", graph("walk on"), HOUR + 300)
    return cured


# ---- take_dq: the swap ----------------------------------------------------------------

def test_a_swapped_in_attempt_reads_as_a_finished_take(tmp_path):
    cured = jekyll_room(tmp_path, own_graph=False)
    kept = tmp_path / "T22.mp4"
    take_dq.settle(tmp_path, 22, {kept: verdict(False, 40.0), cured: verdict(True, 95.0)})
    assert kept.read_bytes() == b"cured, 95"
    assert tc.is_current("walk on", kept, canvas=(768, 768))


def test_the_swap_carries_each_render_its_own_graph(tmp_path):
    cured = jekyll_room(tmp_path, own_graph=True)
    kept = tmp_path / "T22.mp4"
    (tmp_path / "T22.graph.json").write_text(json.dumps(graph("newer words")), encoding="utf-8")
    take_dq.settle(tmp_path, 22, {kept: verdict(False, 40.0), cured: verdict(True, 95.0)})
    assert tc.recorded_prompt(kept) == "walk on"
    displaced = tmp_path / "attempts" / "T22_fail2.mp4"
    assert displaced.read_bytes() == b"newer, failed"
    assert tc.recorded_prompt(displaced) == "newer words"


def test_a_legacy_attempt_without_a_graph_leaves_one_with_the_displaced_take(tmp_path):
    cured = jekyll_room(tmp_path, own_graph=False)
    kept = tmp_path / "T22.mp4"
    take_dq.settle(tmp_path, 22, {kept: verdict(False, 40.0), cured: verdict(True, 95.0)})
    assert tc.recorded_prompt(tmp_path / "attempts" / "T22_fail2.mp4") == "walk on"


def test_step_09_does_not_call_a_swapped_take_stale(tmp_path, monkeypatch):
    """Step 09's done() read the swapped take stale, so the next pass re-ran it."""
    home = tmp_path / "ep01"
    room = home / "takes" / "r2v"
    cured = jekyll_room(room, own_graph=False)
    episode_home.write_json(room / "prompts.json", [{"index": 22, "prompt": "walk on", "anchors": []}])
    take_dq.settle(room, 22, {room / "T22.mp4": verdict(False, 40.0), cured: verdict(True, 95.0)})
    monkeypatch.setattr(shoot, "card_pictures", lambda c, book, n: [])
    ctx = SimpleNamespace(home=home, book_dir=tmp_path, number=1)
    assert shoot.stale_takes(ctx) == []


# ---- takes_r2v: nothing overwritten, tries carried ------------------------------------

def test_displace_moves_a_take_and_its_graph_to_the_attempts_room(tmp_path):
    put(tmp_path / "T05.mp4", b"kept", 60)
    put(tmp_path / "T05.graph.json", graph("x"), 90)
    moved = episode_home.displace(tmp_path / "T05.mp4", 5)
    assert moved == tmp_path / "attempts" / "T05_fail1.mp4" and moved.read_bytes() == b"kept"
    assert moved.with_suffix(".graph.json").exists()
    assert not (tmp_path / "T05.mp4").exists() and not (tmp_path / "T05.graph.json").exists()
    assert episode_home.displace(tmp_path / "T05.mp4", 5) is None


def test_a_stale_take_is_archived_and_rendered_on_its_next_seed(tmp_path):
    out = put(tmp_path / "T19.mp4", b"87.6", 60)
    c = {"index": 19, "seed": 7}
    takes_r2v.make_room(c, out, {19: {"tries": 2}}, None)
    assert (tmp_path / "attempts" / "T19_fail1.mp4").read_bytes() == b"87.6"
    assert c["tries"] == 3 and c["seed"] == 7 + 101 * 3


def test_a_first_render_keeps_its_seed(tmp_path):
    c = {"index": 3, "seed": 7}
    takes_r2v.make_room(c, tmp_path / "T03.mp4", {}, None)
    assert c == {"index": 3, "seed": 7}


def test_a_retake_round_leaves_every_other_kept_take_alone(tmp_path):
    """Step 11's retake of one shot re-rendered T19 and T22 beside it."""
    out = put(tmp_path / "T19.mp4", b"kept", 60)
    stale = lambda: False                                           # noqa: E731
    assert takes_r2v.wants_render({"index": 19, "shots": [19]}, out, {}, [13], stale) is False
    assert takes_r2v.wants_render({"index": 13, "shots": [13]}, out, {}, [13], stale) is True
    missing = tmp_path / "T20.mp4"
    assert takes_r2v.wants_render({"index": 20, "shots": [20]}, missing, {}, [13], stale) is True


def test_a_first_round_renders_what_is_not_current(tmp_path):
    out = put(tmp_path / "T04.mp4", b"kept", 60)
    rec = {4: {"shots": [4]}}
    c = {"index": 4, "shots": [4]}
    assert takes_r2v.wants_render(c, out, rec, [], lambda: True) is False
    assert takes_r2v.wants_render(c, out, rec, [], lambda: False) is True
    assert takes_r2v.wants_render(c, out, {4: {"shots": [3, 4]}}, [], lambda: True) is True


def test_collect_never_writes_over_a_take_on_disk(tmp_path, monkeypatch):
    rendered = put(tmp_path / "comfy" / "out.mp4", b"new render", 0)
    out = put(tmp_path / "T22.mp4", b"cured, 95", HOUR)
    monkeypatch.setattr(takes_r2v, "wait_record", lambda pid, timeout=None: {})
    monkeypatch.setattr(takes_r2v, "outputs_of", lambda record: [rendered])
    monkeypatch.setattr(takes_r2v, "clip_seconds", lambda p: 5.0)
    monkeypatch.setattr(takes_r2v, "phases_of", lambda *a: None)
    takes_r2v.collect({"index": 22}, "pid", out)
    assert out.read_bytes() == b"new render"
    assert (tmp_path / "attempts" / "T22_fail1.mp4").read_bytes() == b"cured, 95"
