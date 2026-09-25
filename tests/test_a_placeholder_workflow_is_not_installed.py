"""A workflow whose node is still a TODO placeholder is not installed.

ep12, 2026-09-25: `image_embed.json` exists but its one node class reads
"TODO verify node class: DINOv3 ViT-L image embedding (no installed pack
exposes one; see manifest notes)". take_dq's embedder() checked only that the
file loads, handed the placeholder to ComfyUI, and every take died on
missing_node_type -- where the design says the leak row reads 'not measured'.
"""
from scripts.episode import take_dq
from studio import comfy


def test_a_todo_node_class_means_not_installed(monkeypatch):
    template = {"2": {"class_type": "TODO verify node class: DINOv3", "inputs": {}}}
    monkeypatch.setattr(comfy, "load_workflow", lambda name: (template, {"image_1": ["1", "image"]}))
    assert take_dq.embedder() == (None, None)


def test_a_real_node_class_is_installed(monkeypatch):
    template = {"2": {"class_type": "DINOv3Embed", "inputs": {}}}
    monkeypatch.setattr(comfy, "load_workflow", lambda name: (template, {"image_1": ["1", "image"]}))
    embed, inputs = take_dq.embedder()
    assert embed is not None and inputs is not None
