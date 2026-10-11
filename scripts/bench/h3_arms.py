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


def model_chain(graph: dict, head: str = "4") -> list[str]:
    """The model-patch nodes from `head` back to the UNET, following `model` links:
    an arm-only node (an attention backend) is in it wherever the arm wired it."""
    chain, at = [], head
    while at in graph:
        chain.append(at)
        link = graph[at]["inputs"].get("model")
        if not isinstance(link, list):
            return chain
        at = link[0]
    return chain


def lay(out: dict, arm: dict, cls: str, keys: tuple) -> None:
    """The arm's values of `keys` on the shipped graph's node of class `cls`."""
    if not any(n.get("class_type") == cls for n in out.values()) or             not any(n.get("class_type") == cls for n in arm.values()):
        return
    ok, ak = node_of(out, cls)[0], node_of(arm, cls)[0]
    out[ok]["inputs"].update({k: arm[ak]["inputs"][k] for k in keys if k in arm[ak]["inputs"]})


def lay_model(out: dict, arm: dict) -> None:
    for k in set(MODEL_NODES) | set(model_chain(out)):
        out.pop(k, None)
    for k in model_chain(arm):
        out[k] = json.loads(json.dumps(arm[k]))


def lay_save(out: dict, arm: dict, prefix: str) -> None:
    vk, save = node_of(out, "SaveVideo")
    keep = {k: v for k, v in save["inputs"].items() if k not in SAVE_KEYS}
    arm_save = {k: v for k, v in node_of(arm, "SaveVideo")[1]["inputs"].items() if k in SAVE_KEYS}
    out[vk]["inputs"] = {**keep, **arm_save, "filename_prefix": prefix}


def arm_graph(shipped: dict, arm: dict, prefix: str, seed: int | None = None,
              canvas: tuple[int, int] | None = None, images: dict | None = None) -> dict:
    """The shipped graph with the arm's model chain (every patch node), scheduler,
    steps, sampler, ref sizing and save; the canvas and restaged images are the
    JOB's (an arm template's 1280x736 default is never a claim)."""
    out = json.loads(json.dumps(shipped))
    lay_model(out, arm)
    lay(out, arm, "BasicScheduler", ("scheduler", "steps"))
    lay(out, arm, "KSamplerSelect", ("sampler_name",))
    lay(out, arm, "MiniMaxH3ReferenceToVideo", ("ref_image_size",))
    lay_save(out, arm, prefix)
    if canvas:
        out[node_of(out, "MiniMaxH3ReferenceToVideo")[0]]["inputs"].update(width=canvas[0], height=canvas[1])
    for node, name in (images or {}).items():
        out[node]["inputs"]["image"] = name
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


def input_of(graph: dict, cls: str, key: str):
    """One input of the first node of class `cls`, None when the graph has none."""
    return next((n["inputs"].get(key) for n in graph.values() if n.get("class_type") == cls), None)


def panel_of(graph: dict) -> str | None:
    """The staged storyboard panel (a LoadImage named shot_*), None for refs-only."""
    return next((n["inputs"]["image"] for n in graph.values() if n.get("class_type") == "LoadImage"
                 and str(n["inputs"].get("image", "")).startswith("shot_")), None)


def knobs(graph: dict, sizer=None) -> dict:
    """The settings a result speaks for, read from the graph itself; `sizer(name)`
    adds the staged panel's pixel size."""
    save, r2v = node_of(graph, "SaveVideo")[1]["inputs"], node_of(graph, "MiniMaxH3ReferenceToVideo")[1]["inputs"]
    k = {"unet": node_of(graph, "UNETLoader")[1]["inputs"]["unet_name"], "loras": lora_chain(graph),
         "steps": input_of(graph, "BasicScheduler", "steps"), "scheduler": input_of(graph, "BasicScheduler", "scheduler"),
         "sampler": input_of(graph, "KSamplerSelect", "sampler_name"),
         "shift_video": input_of(graph, "MiniMaxH3SigmaShift", "shift_video"),
         "shift_audio": input_of(graph, "MiniMaxH3SigmaShift", "shift_audio"),
         "attention": input_of(graph, "PathchSageAttentionKJ", "sage_attention"),
         "attention_backend": input_of(graph, "ModelAttentionBackend", "attention"),
         "crf": save.get("format.codec.encoding.crf"), "seed": node_of(graph, "RandomNoise")[1]["inputs"]["noise_seed"],
         "frames": r2v["length"], "width": r2v.get("width"), "height": r2v.get("height"),
         "ref_image_size": r2v.get("ref_image_size"), "panel": panel_of(graph)}
    if sizer and k["panel"]:
        k["panel_px"] = list(sizer(k["panel"]))
    return k


def assert_knobs(k: dict, expect: dict) -> None:
    for key, want in expect.items():
        got = k[key]
        if key == "loras":
            got = [list(x) for x in got]
        assert got == want, f"knob {key}: graph has {got!r}, arm claims {want!r}"


def size_fault(k: dict, size) -> str:
    """'' when the render is the canvas, else what assert_size says: the row is kept, the arm voided."""
    try:
        assert_size(k, tuple(size))
    except AssertionError as why:
        return str(why)
    return ""


def assert_size(k: dict, size: tuple[int, int]) -> None:
    """The rendered video's (w, h) by ffprobe must be the canvas the graph asked for."""
    assert tuple(size) == (k["width"], k["height"]), f"rendered {size}, canvas {k['width']}x{k['height']}"


def arm_template(arm: str) -> dict:
    from studio.comfy import load_workflow
    return load_workflow(arm)[0]


def stage(path: str) -> str:
    from studio.comfy import stage_image
    return stage_image(Path(path))


def staged_px(name: str) -> tuple[int, int]:
    from PIL import Image
    from studio.comfy import COMFY_ROOT
    return Image.open(COMFY_ROOT / "input" / name).size


def assert_panel_fits(k: dict) -> None:
    """A staged panel must be the canvas's size: a 768 panel under a 992 canvas tests the wrong thing."""
    if k.get("panel_px"):
        assert k["panel_px"] == [k["width"], k["height"]], f"panel {k['panel_px']} under canvas {k['width']}x{k['height']}"


def build(job: dict) -> dict:
    shipped = json.loads(Path(job["graph"]).read_text("utf-8"))
    images = {node: stage(path) for node, path in job.get("stage", {}).items()}
    g = arm_graph(shipped, arm_template(job["arm"]), prefix=f"bench_{job['tag']}", seed=job.get("seed"),
                  canvas=tuple(job["canvas"]) if job.get("canvas") else None, images=images)
    k = knobs(g, sizer=staged_px)
    assert_knobs(k, job.get("expect", {}))
    assert_panel_fits(k)
    return g


def probe_size(video: Path) -> tuple[int, int]:
    """The rendered (w, h) off the first decoded frame (no ffprobe on this machine)."""
    from studio.take_zoom import probe_size as first_frame_size
    return first_frame_size(video)


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
            "video": str(dest), "ran_s": ran_for(rec), "size": list(probe_size(dest)),
            "collected": time.strftime("%Y-%m-%dT%H:%M:%S")}


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
            row["size_fault"] = size_fault(k, row["size"])
        except Exception as raised:  # one lost job costs only itself
            row = {"tag": job["tag"], "error": str(raised)}
        with (out_dir / "runs.jsonl").open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row) + "\n")
        print("done", row.get("tag"), row.get("ran_s"), row.get("error", ""), flush=True)


if __name__ == "__main__":
    if sys.argv[1] == "run":
        run(Path(sys.argv[2]), Path(sys.argv[3]))
