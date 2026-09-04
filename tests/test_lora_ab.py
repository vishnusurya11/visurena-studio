"""The identity A/B: the same beat and seeds rendered through each LoRA
variant, scored by the trait-card distance to the reference sheet.  Nothing
here touches the engine: render and measure are injected."""
from __future__ import annotations

import json
from pathlib import Path

from scripts.trailer import lora_ab as ab
from scripts.trailer.build_clips import WORKFLOW


def test_the_current_render_is_the_control_and_adds_nothing():
    values = {"prompt": "p", "steps": 8, "seed": 1}
    control = ab.VARIANTS["ema850"]
    assert control["workflow"] == WORKFLOW
    assert ab.variant_values(values, control) == values


def test_a_variant_overrides_the_lora_and_shifts():
    values = {"prompt": "p", "steps": 8, "seed": 1}
    made = ab.variant_values(values, ab.VARIANTS["ref2v_v1"])
    assert made["lora_name"].endswith("ref2v_turbo_8step_v1.0_768p_comfyui_bf16.safetensors")
    assert made["steps"] == 8 and made["shift_video"] == 12 and made["shift_audio"] == 3
    assert made["prompt"] == "p" and ab.VARIANTS["ref2v_v1"]["workflow"].endswith("lxref")


def test_summarise_averages_distance_and_time_per_variant():
    rows = [{"variant": "a", "distance": 1.0, "known": 8, "seconds": 100.0, "bound": True},
            {"variant": "a", "distance": 3.0, "known": 8, "seconds": 300.0, "bound": False},
            {"variant": "b", "distance": 0.5, "known": 7, "seconds": 50.0, "bound": True}]
    summary = ab.summarise(rows)
    assert summary["a"] == {"n": 2, "mean_distance": 2.0, "bound": 1, "mean_seconds": 200.0}
    assert summary["b"]["mean_distance"] == 0.5 and summary["b"]["bound"] == 1


def test_run_ab_renders_every_seed_through_every_variant_and_logs_each_row(tmp_path, monkeypatch):
    calls = []

    def render(values, bound, refs, book, dest, workflow):
        calls.append((workflow, values["seed"], values.get("lora_name")))
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(b"mp4")
        return dest
    monkeypatch.setattr(ab, "render_take", render)
    monkeypatch.setattr(ab, "measure", lambda take, reference, work, seed: {
        "card": "card", "differs": ["age"], "known": 8, "seconds": 7.0})
    monkeypatch.setattr(ab, "distance", lambda card, reference: 0.5)
    rows = ab.run_ab(book=tmp_path, out_dir=tmp_path / "ab", beat={"beat_id": "B00"},
                     plan={"shots": []}, refs={}, style="noir", reference="ref", bound=[],
                     seeds=[1, 2], variants={k: ab.VARIANTS[k] for k in ("ema850", "ref2v_v1")},
                     values_for=lambda beat, plan, refs, style, seed: {"prompt": "p", "steps": 8, "seed": seed})
    assert len(rows) == 4 and {r["variant"] for r in rows} == {"ema850", "ref2v_v1"}
    assert [c[1] for c in calls] == [1, 2, 1, 2]
    assert calls[0][2] is None and calls[2][2].endswith(".safetensors")
    assert rows[0]["distance"] == 0.5 and rows[0]["bound"] is True and rows[0]["differs"] == ["age"]
    logged = [json.loads(l) for l in (tmp_path / "ab/ab.jsonl").read_text(encoding="utf-8").splitlines()]
    assert len(logged) == 4 and logged[3]["seed"] == 2
