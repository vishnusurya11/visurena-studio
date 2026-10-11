"""The legacy-path replay (C1_verdict #10; bench block 5): A Study in Scarlet runs
the OLD pipeline -- `char-*_indoor` sheets, `boards/cells` cells, no looks.json --
so `look_replay` cannot replay it. A legacy take replays its own ran
`T*.graph.json` with exactly the content-addressed names it staged; only the
pictures a job swaps change. ep01-03 staged UNHASHED names (`char-sherlock_holmes_bench.png`,
`voice_18.wav`) that later episodes overwrote in ComfyUI/input (C1_A: 5 stale guides),
so a graph with an unhashed name is refused: its inputs are unknown.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.refs import legacy_replay as lr

ROOT = Path(__file__).resolve().parents[1]
SCARLET = ROOT / "library" / "20260822113400_a-study-in-scarlet" / "episodes"


def graph(*names: str) -> dict:
    out = {"9": {"class_type": "RandomNoise", "inputs": {"noise_seed": 95004}}}
    for k, name in enumerate(names):
        cls = "LoadAudio" if name.endswith(".wav") else "LoadImage"
        out[str(18 + k)] = {"class_type": cls, "inputs": {("audio" if cls == "LoadAudio" else "image"): name}}
    return out


HASHED = graph("char-sherlock_holmes_indoor_4e7e69a0.png", "Q04_0_096d02bd.png", "voice_04_2e07b6cc.wav")


def test_a_dry_replay_stages_exactly_the_shipped_names():
    assert lr.staged(lr.replay_graph(HASHED)) == lr.staged(HASHED)


def test_a_swap_changes_only_the_named_picture():
    out = lr.replay_graph(HASHED, swaps={"Q04_0_096d02bd.png": "Q04_0_replay_11112222.png"}, seed=7)
    assert lr.staged(out) == {"18": "char-sherlock_holmes_indoor_4e7e69a0.png", "19": "Q04_0_replay_11112222.png",
                              "20": "voice_04_2e07b6cc.wav"}
    assert out["9"]["inputs"]["noise_seed"] == 7 and HASHED["19"]["inputs"]["image"] == "Q04_0_096d02bd.png"


def test_an_unhashed_name_is_refused():
    with pytest.raises(SystemExit, match="char-sherlock_holmes_bench.png"):
        lr.replay_graph(graph("char-sherlock_holmes_bench.png", "voice_18.wav"))


@pytest.mark.skipif(not SCARLET.exists(), reason="the Scarlet library is not on disk")
def test_the_ep14_dialogue_takes_build_and_ep01_is_refused():
    for t in ("T04", "T05"):
        shipped = json.loads((SCARLET / "ep14" / "takes" / "r2v" / f"{t}.graph.json").read_text(encoding="utf-8"))
        assert lr.staged(lr.replay_graph(shipped)) == lr.staged(shipped)
    with pytest.raises(SystemExit):
        lr.replay_graph(json.loads((SCARLET / "ep01" / "takes" / "r2v" / "T18.graph.json").read_text(encoding="utf-8")))
