#!/usr/bin/env python
"""Phase-0 H3 take bench (continuity retro 2026-10-10, S_skeptic_verdict.md §4/§6).

An ARM is a new workflow file in comfy_studio (never an edited base). A bench JOB
replays one SHIPPED take: its ran `T*.graph.json` (same prompt, refs, audio guide,
anchors, frames, seed) with the arm file's model / LoRA / attention / shift /
scheduler-steps / save nodes laid over it. The graph actually submitted is
written beside the video and its knobs are asserted before the result counts.

    uv run --no-sync python scripts/bench/h3_arms.py run <plan.json> <out_dir>

`plan.json` is a list of {"shot", "graph" (shipped ran graph path), "arm"
(workflow id), "seed" (optional), "expect" (knob claims)}. Jobs are queued
together (one model load per arm run) and collected in order; each record
lands in <out_dir>/runs.jsonl.
"""
from __future__ import annotations

import json
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

MODEL_NODES = ("1", "2", "lora_second", "3", "4")
SAVE_KEYS = ("format", "codec", "format.codec", "format.codec.encoding", "format.codec.encoding.crf")


def node_of(graph: dict, cls: str) -> tuple[str, dict]:
    return next((k, n) for k, n in graph.items() if n.get("class_type") == cls)


def arm_graph(shipped: dict, arm: dict, prefix: str, seed: int | None = None) -> dict:
    """The shipped graph with the arm's model chain, steps and save settings."""
    out = json.loads(json.dumps(shipped))
    for k in MODEL_NODES:
        out.pop(k, None)
        if k in arm:
            out[k] = json.loads(json.dumps(arm[k]))
    sk, _ = node_of(out, "BasicScheduler")
    out[sk]["inputs"]["steps"] = node_of(arm, "BasicScheduler")[1]["inputs"]["steps"]
    vk, save = node_of(out, "SaveVideo")
    keep = {k: v for k, v in save["inputs"].items() if k not in SAVE_KEYS}
    arm_save = {k: v for k, v in node_of(arm, "SaveVideo")[1]["inputs"].items() if k in SAVE_KEYS}
    out[vk]["inputs"] = {**keep, **arm_save, "filename_prefix": prefix}
    if seed is not None:
        out[node_of(out, "RandomNoise")[0]]["inputs"]["noise_seed"] = seed
    return out


def lora_chain(graph: dict) -> list[tuple[str, float]]:
    """LoRAs from the UNET outward, following each loader's `model` link."""
    unet = node_of(graph, "UNETLoader")[0]
    chain, at = [], unet
    while True:
        nxt = next((k for k, n in graph.items() if n.get("class_type") == "LoraLoaderModelOnly"
                    and n["inputs"].get("model", [None])[0] == at), None)
        if nxt is None:
            return chain
        n = graph[nxt]["inputs"]
        chain.append((n["lora_name"].split("\\")[-1].split("/")[-1], float(n["strength_model"])))
        at = nxt


def knobs(graph: dict) -> dict:
    """The settings a result speaks for, read from the graph itself."""
    save = node_of(graph, "SaveVideo")[1]["inputs"]
    attn = next((n["inputs"].get("sage_attention") for n in graph.values()
                 if n.get("class_type") == "PathchSageAttentionKJ"), None)
    return {"unet": node_of(graph, "UNETLoader")[1]["inputs"]["unet_name"],
            "loras": lora_chain(graph),
            "steps": node_of(graph, "BasicScheduler")[1]["inputs"]["steps"],
            "attention": attn,
            "crf": save.get("format.codec.encoding.crf"),
            "seed": node_of(graph, "RandomNoise")[1]["inputs"]["noise_seed"],
            "frames": node_of(graph, "MiniMaxH3ReferenceToVideo")[1]["inputs"]["length"]}


def assert_knobs(k: dict, expect: dict) -> None:
    for key, want in expect.items():
        got = k[key]
        if key == "loras":
            got = [list(x) for x in got]
        assert got == want, f"knob {key}: graph has {got!r}, arm claims {want!r}"


def arm_template(arm: str) -> dict:
    from studio.comfy import load_workflow
    return load_workflow(arm)[0]


def build(job: dict) -> dict:
    shipped = json.loads(Path(job["graph"]).read_text("utf-8"))
    g = arm_graph(shipped, arm_template(job["arm"]), prefix=f"bench_{job['tag']}", seed=job.get("seed"))
    assert_knobs(knobs(g), job.get("expect", {}))
    return g


def ran_for(record: dict) -> float | None:
    """Seconds ComfyUI stamped between execution_start and the end (as takes_r2v.ran_for)."""
    msgs = record.get("status", {}).get("messages", [])
    t0 = next((m[1].get("timestamp") for m in msgs if m[0] == "execution_start"), None)
    t1 = next((m[1].get("timestamp") for m in msgs if m[0] in ("execution_success", "execution_error")), None)
    return round((t1 - t0) / 1000, 1) if t0 and t1 else None


def collect_one(job: dict, pid: str, out_dir: Path) -> dict:
    from studio.comfy import outputs_of, wait_record
    rec = wait_record(pid, timeout=3600)
    video = next(p for p in outputs_of(rec) if p.suffix == ".mp4")
    dest = out_dir / f"{job['tag']}.mp4"
    shutil.copyfile(video, dest)
    return {"tag": job["tag"], "shot": job["shot"], "arm": job["arm"], "prompt_id": pid,
            "video": str(dest), "ran_s": ran_for(rec), "collected": time.strftime("%Y-%m-%dT%H:%M:%S")}


def run(plan_path: Path, out_dir: Path) -> None:
    from studio.comfy import submit
    out_dir.mkdir(parents=True, exist_ok=True)
    jobs = json.loads(plan_path.read_text("utf-8"))
    tickets = []
    for job in jobs:
        g = build(job)
        (out_dir / f"{job['tag']}.graph.json").write_text(json.dumps(g, indent=1), "utf-8")
        tickets.append((job, submit(g), knobs(g)))
        print("queued", job["tag"], flush=True)
    for job, pid, k in tickets:
        try:
            row = {**collect_one(job, pid, out_dir), "knobs": k}
        except Exception as raised:  # one lost job costs only itself
            row = {"tag": job["tag"], "error": str(raised)}
        with (out_dir / "runs.jsonl").open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row) + "\n")
        print("done", row.get("tag"), row.get("ran_s"), row.get("error", ""), flush=True)


if __name__ == "__main__":
    if sys.argv[1] == "run":
        run(Path(sys.argv[2]), Path(sys.argv[3]))
