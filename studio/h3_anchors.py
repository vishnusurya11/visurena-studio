"""Add pixel-frame anchors to an H3 graph: MiniMaxH3AddGuide chained on the
base node's conditioning, one per anchored image, then one for the audio.

The base node (`MiniMaxH3ReferenceToVideo` or `MiniMaxH3ImageToVideo`) is
found by class; the guider is rewired to the last guide; the latent always
comes from the base.  Pure dict work, so the chain can be tested without a
server.
"""
from __future__ import annotations

BASES = ("MiniMaxH3ReferenceToVideo", "MiniMaxH3ImageToVideo")


def _find(graph: dict, class_type: str, title_hint: str = "") -> str:
    hits = [k for k, n in graph.items() if n["class_type"] == class_type
            and (not title_hint or title_hint in n.get("_meta", {}).get("title", ""))]
    if not hits:
        raise KeyError(f"no {class_type} in the graph")
    return hits[0]


def next_id(graph: dict) -> str:
    """One past the highest NUMERIC node id.

    A workflow's node keys are not all numbers: the Singularity take workflow
    (2026-09-19) names its second stacked turbo LoRA `lora_second`, and
    `int(k)` over every key raised on the first take of WotW ep04, after the
    whole run had been queued.  Non-numeric keys are skipped, and the digit
    test is `isdigit` rather than a try/except so a key like `12a` is skipped
    too instead of being silently counted as 12."""
    numbered = [int(k) for k in graph if str(k).isdigit()]
    return str(max(numbered, default=0) + 1)


def anchored(graph: dict, anchors: list[tuple[str, int]], audio: tuple[str, int] | None) -> dict:
    """`anchors` = (staged image filename, frame_idx); `audio` = (staged wav, frame_idx)."""
    base = _find(graph, BASES[0]) if any(n["class_type"] == BASES[0] for n in graph.values()) \
        else _find(graph, BASES[1])
    vaes = [k for k, n in graph.items() if n["class_type"] == "VAELoader"]
    video_vae, audio_vae = vaes[0], vaes[-1]
    head = [base, 0]
    for image, frame in anchors:
        loader = next_id(graph)
        graph[loader] = {"class_type": "LoadImage", "inputs": {"image": image, "upload": "image"},
                         "_meta": {"title": f"anchor {image} @ {frame}"}}
        guide = next_id(graph)
        graph[guide] = {"class_type": "MiniMaxH3AddGuide",
                        "inputs": {"positive": head, "latent": [base, 1], "vae": [video_vae, 0],
                                   "image": [loader, 0], "frame_idx": frame},
                        "_meta": {"title": f"anchor image @ {frame}"}}
        head = [guide, 0]
    if audio:
        wav, frame = audio
        loader = next_id(graph)
        graph[loader] = {"class_type": "LoadAudio", "inputs": {"audio": wav}, "_meta": {"title": "anchored audio"}}
        guide = next_id(graph)
        graph[guide] = {"class_type": "MiniMaxH3AddGuide",
                        "inputs": {"positive": head, "latent": [base, 1], "audio_vae": [audio_vae, 0],
                                   "audio": [loader, 0], "frame_idx": frame},
                        "_meta": {"title": f"anchor audio @ {frame}"}}
        head = [guide, 0]
    graph[_find(graph, "BasicGuider")]["inputs"]["conditioning"] = head
    return graph
