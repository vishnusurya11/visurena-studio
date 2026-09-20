"""A take is current only when the prompt on disk is the prompt we would send.

MEASURED 2026-09-20 on WotW ep05.  A reviewer pass rewrote seven shots and
`pack_refs.props_named` stopped staging a setup's whole prop list on every take
of that setup -- the fix for chapter 5's humped dome sitting at the mast's foot
twenty shots before it rises.  All 28 take prompts changed: T12's old prompt
carried "Below it the humped black back of a Martian appliance lifts over the
rim of the pit" and a `<Picture 2> defines this object alone`, and the new one
carries neither.

`takes_r2v.main` would have re-rendered NONE of them.  Its skip is

    records[i].get("shots") == c["shots"] and out.exists()

-- the SHOT GROUPING and the file's existence.  The grouping did not change, so
every take is kept, the run prints nothing, and the next DQ pass comes back with
the identical numbers.  That is the failure mode already written down as "a fix
that changes nothing": the prompt was fixed, the artefact was not, and green
gates say so twice.

`--retake=` is not the answer.  It is a list a person types, and a person who
mistypes it gets silence, not a refusal.

THE BRICK: the graph each take ran with is already on disk beside it, written
by the run that made it (`T<NN>.graph.json`, "the exact graph this take ran
with").  So currency is not a flag or a record field to maintain -- it is a
comparison against a fact already kept.
"""
import json
from pathlib import Path

import pytest


SPENT = "the rod comes up out of the pit and the disk on it turns."


def graph_with(prompt: str) -> dict:
    return {"8": {"class_type": "MiniMaxH3ReferenceToVideo",
                  "inputs": {"prompt": prompt, "frames": 137, "seed": 5}},
            "2": {"class_type": "LoraLoader", "inputs": {"strength_model": 1.0}}}


def test_the_prompt_is_read_off_the_render_node(tmp_path):
    from studio.take_currency import prompt_of
    assert prompt_of(graph_with(SPENT)) == SPENT


def test_a_graph_with_no_render_node_has_no_prompt():
    from studio.take_currency import prompt_of
    assert prompt_of({"2": {"class_type": "LoraLoader", "inputs": {"strength_model": 1.0}}}) is None


def test_a_take_built_from_the_same_prompt_is_current(tmp_path):
    from studio.take_currency import is_current
    out = tmp_path / "T12.mp4"
    out.write_bytes(b"picture")
    (tmp_path / "T12.graph.json").write_text(json.dumps(graph_with(SPENT)), encoding="utf-8")
    assert is_current(SPENT, out) is True


def test_a_take_whose_prompt_changed_is_not_current(tmp_path):
    """ep05's whole episode: same shots, same file, a different prompt."""
    from studio.take_currency import is_current
    out = tmp_path / "T12.mp4"
    out.write_bytes(b"picture")
    (tmp_path / "T12.graph.json").write_text(
        json.dumps(graph_with(SPENT + " Below it the humped black back of a Martian appliance "
                                      "lifts over the rim of the pit.")), encoding="utf-8")
    assert is_current(SPENT, out) is False


def test_whitespace_alone_does_not_order_a_rerender(tmp_path):
    """A re-wrap costs 200 s of GPU and changes no picture."""
    from studio.take_currency import is_current
    out = tmp_path / "T12.mp4"
    out.write_bytes(b"picture")
    (tmp_path / "T12.graph.json").write_text(json.dumps(graph_with("  " + SPENT + "\n")),
                                             encoding="utf-8")
    assert is_current(SPENT, out) is True


def test_a_take_with_no_recorded_graph_is_not_current(tmp_path):
    """Cannot prove it is the same, so it is not assumed to be: the old
    episodes predate the graph file, and rendering is the safe answer."""
    from studio.take_currency import is_current
    out = tmp_path / "T12.mp4"
    out.write_bytes(b"picture")
    assert is_current(SPENT, out) is False


def test_a_missing_take_is_not_current(tmp_path):
    from studio.take_currency import is_current
    assert is_current(SPENT, tmp_path / "T12.mp4") is False


def test_the_runner_asks_whether_the_prompt_is_still_the_one_it_would_send():
    """The regression: the skip must not rest on the shot grouping alone."""
    import inspect

    import importlib.util
    import sys
    root = Path(__file__).resolve().parents[1]
    spec = importlib.util.spec_from_file_location("tkr", root / "scripts" / "episode" / "takes_r2v.py")
    tkr = importlib.util.module_from_spec(spec)
    sys.modules["tkr"] = tkr
    spec.loader.exec_module(tkr)
    body = inspect.getsource(tkr.main)
    skip = body[body.index("mark_retake("):body.index("graph = graph_for(")]
    assert "is_current" in skip, (
        "a take is kept on its shot grouping and the file existing; a rewritten "
        "prompt is then never sent to the GPU and DQ repeats the old numbers")
