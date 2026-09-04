"""Which turbo LoRA keeps a face: the same beat and seeds rendered through
each variant, scored by the trait-card distance to the reference sheet.

The trailer's turbo LoRA (EMA ckpt850) is FL2V-lineage on a ref2va base --
its own manifest says identity retention was never checked.  Two Ref2V-
lineage LoRAs exist for the same 8-step, 768p config.  A "cleaner" look in
an uncontrolled probe is not evidence; the gate's own metric, over the same
seeds, is.  Local GPU only; spends nothing.

    uv run python -m scripts.trailer.lora_ab 20260822113400 --beat B00 --seeds 3
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Callable

from scripts.trailer.build_clips import ROOT, WORKFLOW, bound_slots, render_take, take_values
from scripts.trailer.step_07_clips import SEED_BASE, measure, reference_of
from studio.describe import DISTINCT_AT, distance

LXREF = "video_minimax_h3_r2v_turbo_lxref"
VARIANTS: dict[str, dict] = {
    "ema850": {"workflow": WORKFLOW, "values": {}},
    "ref2v_v1": {"workflow": LXREF, "values": {
        "lora_name": "minimax_h3\minimax_h3_ref2v_turbo_8step_v1.0_768p_comfyui_bf16.safetensors",
        "lora_strength": 1.0, "steps": 8, "shift_video": 12, "shift_audio": 3}},
    "acc8": {"workflow": LXREF, "values": {
        "lora_name": "minimax_h3\MiniMax-H3-Ref2VA-Acc-8Step.safetensors",
        "lora_strength": 1.0, "steps": 8, "shift_video": 12, "shift_audio": 3}},
}
"""The control is the trailer's render exactly; the others differ only in
the LoRA node, its strength, and the sigma shifts the LoRA was trained at."""


def variant_values(values: dict, variant: dict) -> dict:
    """The take's values with one variant's LoRA choices laid over them."""
    return {**values, **variant["values"]}


def summarise(rows: list[dict]) -> dict[str, dict]:
    """Per variant: how many, how far from the sheet on average, how many bound, how slow."""
    out: dict[str, dict] = {}
    for name in sorted({r["variant"] for r in rows}):
        mine = [r for r in rows if r["variant"] == name]
        out[name] = {"n": len(mine),
                     "mean_distance": round(sum(r["distance"] for r in mine) / len(mine), 3),
                     "bound": sum(1 for r in mine if r["bound"]),
                     "mean_seconds": round(sum(r["seconds"] for r in mine) / len(mine), 1)}
    return out


def run_ab(book: Path, out_dir: Path, beat: dict, plan: dict, refs: dict, style: str,
           reference, bound: list[str], seeds: list[int], variants: dict[str, dict],
           values_for: Callable = take_values) -> list[dict]:
    """Every seed through every variant; one JSON line per take as it lands."""
    out_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict] = []
    with (out_dir / "ab.jsonl").open("a", encoding="utf-8") as log:
        for name, variant in variants.items():
            for seed in seeds:
                values = variant_values(values_for(beat, plan, refs, style, seed), variant)
                started = time.monotonic()
                take = render_take(values, bound, refs, book, out_dir / f"{name}-{seed}.mp4",
                                   workflow=variant["workflow"])
                seconds = round(time.monotonic() - started, 1)
                read = measure(take, reference, out_dir / "work" / take.stem, seed)
                apart = distance(read["card"], reference)
                rows.append({"variant": name, "seed": seed, "seconds": seconds, "distance": apart,
                             "bound": apart < DISTINCT_AT,
                             "known": read["known"], "differs": read["differs"],
                             "take": str(take.relative_to(book))})
                log.write(json.dumps(rows[-1]) + "\n")
                log.flush()
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("book_glob")
    parser.add_argument("--beat", default="B00")
    parser.add_argument("--seeds", type=int, default=3)
    parser.add_argument("--variants", default=",".join(VARIANTS))
    args = parser.parse_args()
    book = next(p for p in (ROOT / "library").iterdir() if p.name.startswith(args.book_glob))
    out = book / "trailer/main"
    plan = json.loads((out / "plan.json").read_text(encoding="utf-8"))
    refs_doc = json.loads((book / "refs/refs.json").read_text(encoding="utf-8"))
    refs = {r["ref_id"]: r for r in refs_doc["refs"]}
    index, beat = next((i, b) for i, b in enumerate(plan["beats"]) if b["beat_id"] == args.beat)
    bound = bound_slots(beat, refs)
    _, reference = reference_of(book, refs, bound)
    if reference is None:
        raise SystemExit(f"{args.beat} binds no character; pick a beat with a face")
    seeds = [SEED_BASE + index * 7 + 1000 * i for i in range(args.seeds)]
    variants = {k: VARIANTS[k] for k in args.variants.split(",")}
    rows = run_ab(book, out / "ab", beat, plan, refs, refs_doc["palette"], reference, bound,
                  seeds, variants)
    print(json.dumps(summarise(rows), indent=2))


if __name__ == "__main__":
    main()
