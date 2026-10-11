#!/usr/bin/env python
"""B-2 arm B1: restyle a take's Qwen panel with Krea2 + Cinematic_Artstyle at denoise 0.35
(`image_krea2_cinematic_2x_restyle_visurena`), then build the bench take with the restyled
panel staged in the panel's slot. Everything else in the ran graph is kept.

    uv run --no-sync python scripts/bench/restyle.py <ran graph> <out.png> [seed]
"""
from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

WORKFLOW = "image_krea2_cinematic_2x_restyle_visurena"
LEAD = ("A 3d, clean ultra hd, AAA game quality graphics, computer generated CGI image, great detail, high contrast, "
        "highly accurate character model and texture, realistic lighting. A heavily angular 3d art style with brush "
        "stroke colour texture. Cinematic film still of ")


def panel_of(graph: dict) -> tuple[str, str]:
    """(node id, staged name) of the storyboard panel the take was shown."""
    return next((k, n["inputs"]["image"]) for k, n in graph.items()
                if n.get("class_type") == "LoadImage" and n["inputs"]["image"].startswith("shot_"))


def scene_of(prompt: str) -> str:
    """The place clause of the take prompt ('... take of 1 shot in <place>. [Shot 1]')."""
    m = re.search(r"shot in (.+?)\.\s*(\[Shot|A |The )", prompt)
    return (m.group(1) if m else prompt[:300]).strip()


def with_panel(graph: dict, staged: str) -> dict:
    import json
    out = json.loads(json.dumps(graph))
    out[panel_of(out)[0]]["inputs"]["image"] = staged
    return out


def restyle(graph: dict, out: Path, seed: int = 0) -> Path:
    from studio.comfy import apply_inject, load_workflow, outputs_of, submit, wait_record
    _, panel = panel_of(graph)
    prompt = next(n for n in graph.values() if n.get("class_type") == "MiniMaxH3ReferenceToVideo")["inputs"]["prompt"]
    template, inject = load_workflow(WORKFLOW)
    g = apply_inject(template, inject, {"image": panel, "prompt": LEAD + scene_of(prompt), "seed": seed,
                                        "filename_prefix": f"bench_restyle_{out.stem}"})
    rec = wait_record(submit(g), timeout=1800)
    shutil.copyfile(next(p for p in outputs_of(rec) if p.suffix == ".png"), out)
    return out


if __name__ == "__main__":
    import json
    g = json.loads(Path(sys.argv[1]).read_text("utf-8"))
    print(restyle(g, Path(sys.argv[2]), int(sys.argv[3]) if len(sys.argv) > 3 else 0))
