"""E1 ablation, the VLM arm (retro 2026-10-19, P06) -- LOCAL, $0, GPU.

Replays the eval set under tests/fixtures/dq_eval/kawajiri_ep01/ through the
local Qwen3-VL reader (the same ask the gates send) and writes recall and
precision per kind to docs/audit/2026-10-19_kawajiri_retro/evals/ -- generated
evidence, never read by code.  A kind may refuse only at recall >= 0.6 and
precision >= 0.8 (`panel_content.calibrated`); flip `BODY_REFUSES` by hand
after reading the numbers.  Run only with the autopilot paused and /queue empty:

    uv run pytest tests/test_the_dq_eval_replay_writes_recall_and_precision.py -m local

The pure scoring is tested by default in the body-ask tests; this file is the
one that touches the model.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from studio import panel_content as pc, take_content as tc

ROOT = Path(__file__).parent / "fixtures" / "dq_eval" / "kawajiri_ep01"
OUT = Path(__file__).resolve().parents[1] / "docs" / "audit" / "2026-10-19_kawajiri_retro" / "evals"
MANIFEST = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))


def read_panels() -> list[tuple[dict, pc.Seen]]:
    from scripts.episode import panel_content_check as pcc
    return [(p, pcc.read(ROOT / p["file"])) for p in MANIFEST["panels"]]


def shape_scores(read: list[tuple[dict, pc.Seen]]) -> dict:
    """Per shape key: the VL's single-read vote against the agent's label."""
    return {key: pc.eval_scores([p[key] == bad for p, _ in read], [getattr(s, key) == bad for _, s in read])
            for key, bad in (("body", "fading"), ("limb_attached", "floating"))}


def read_takes() -> list[tuple[dict, list[pc.Seen]]]:
    from scripts.episode import take_content_check as tcc
    return [(t, [tcc.read_frame(ROOT / f, seed=11 + i) for i, f in enumerate(t["frames"])]) for t in MANIFEST["takes"]]


def crowd_scores(read: list[tuple[dict, list[pc.Seen]]]) -> dict:
    shots = {s["index"]: s for s in MANIFEST["plan"]["shots"]}
    flagged = [tc.crowd_fault(reads, shots[t["shot"]]["faces"] + shots[t["shot"]]["extras"],
                              MANIFEST["panel_people"].get(str(t["shot"]))) is not None for t, reads in read]
    return pc.eval_scores([t["crowd_leak"] for t, _ in read], flagged)


@pytest.mark.local
def test_the_vl_replay_writes_recall_and_precision():
    from studio import comfy
    with comfy.model_kept():
        shape, crowd = shape_scores(read_panels()), crowd_scores(read_takes())
    OUT.mkdir(parents=True, exist_ok=True)
    row = {"label_source": MANIFEST["label_source"], "ask_version": pc.ASK_VERSION, "shape": shape, "crowd": crowd,
           "refuses": {k: pc.calibrated(v["recall"], v["precision"]) for k, v in {**shape, "crowd": crowd}.items()}}
    (OUT / "dq_eval_vlm.json").write_text(json.dumps(row, indent=1), encoding="utf-8")
    assert set(shape) == {"body", "limb_attached"}
