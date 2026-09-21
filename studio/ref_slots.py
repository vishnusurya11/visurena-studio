"""Stage exactly the references the prompt names, and nothing else.

A LoadImage node left in the graph is not an empty slot. It holds ComfyUI's
default `example.png`, and a multi-reference text encoder reads it like any
other reference.
"""
from __future__ import annotations


def load_slots(graph: dict) -> list[str]:
    """Every LoadImage node id in the graph, in slot order."""
    return sorted((k for k, v in graph.items()
                   if v.get("class_type") == "LoadImage"), key=int)


def stage_only(graph: dict, slots: dict[str, str], encoder: str = "5") -> dict:
    """Keep the named slots, drop every other LoadImage and its encoder link.

    `slots` maps a LoadImage node id to the staged image name. A slot the
    graph does not have is a caller's mistake, not something to ignore.
    """
    have = load_slots(graph)
    if missing := [k for k in slots if k not in have]:
        raise KeyError(f"graph has no LoadImage {missing}, only {have}")
    for node, image in slots.items():
        graph[node]["inputs"]["image"] = image
    for node in have:
        if node not in slots:
            graph.pop(node)
            graph[encoder]["inputs"].pop(f"images.image_{int(node) - 100}", None)
    return graph
