"""Which comfy_studio workflow a submitted graph was filled from, and how it differs from a
recorded one (2026-10-21_ep02_proof DESIGN 2.2, package P3).

A workflow's FINGERPRINT is the multiset of its nodes' `class_type` plus its manifest's inject
map (name -> node, field).  Templates are READ, never written: comfy_studio owns them, and a new
technique is a new file there, never an edit.  A filled graph is IDENTIFIED by the template whose
node ids it carries with the same classes (a take grows anchor and reference nodes, so equality
of the multiset is not required), ties broken by the literals the inject map does not name.

A graph's FIELDS are every literal input, keyed `<node id>.<input>`, plus `classes`; a link
(`[node id, slot]`) is wiring, not a field.  The field diff of section 0 compares these."""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

WORKFLOWS = Path("D:/Projects/KingdomOfViSuReNa/alpha/comfy_studio/workflows")
MANIFEST_SUFFIX = ".manifest.json"
MIN_COVER = 0.8
"""A template is a candidate only when this share of its node ids sit in the graph with its class."""


def classes(graph: dict) -> list[list]:
    """The class_type multiset, sorted: [[class, count], ...]."""
    counted = Counter(n.get("class_type", "") for n in graph.values() if isinstance(n, dict))
    return [[name, n] for name, n in sorted(counted.items())]


def inject_items(inject: dict) -> list[list]:
    return sorted([name, str(spec["node"]), spec["field"]] for name, spec in inject.items())


def fingerprint(template: dict, inject: dict) -> str:
    """16 hex chars of the class multiset plus the inject map."""
    body = json.dumps([classes(template), inject_items(inject)], sort_keys=True)
    return hashlib.sha256(body.encode("utf-8")).hexdigest()[:16]


def multiset_fp(graph: dict) -> str:
    """16 hex chars of the bare class_type multiset: the recordings index's `workflow_fp` for a
    recorded graph (P2 `recordings.classes_fp`; a recorded graph carries no inject map)."""
    counted = sorted(Counter(n["class_type"] for n in graph.values() if isinstance(n, dict) and "class_type" in n).items())
    return hashlib.sha256(json.dumps(counted).encode()).hexdigest()[:16]


def template_paths(root: Path = WORKFLOWS) -> list[Path]:
    """Every template under `root/<modality>/` that has a manifest beside it (two levels, no walk)."""
    found = [p for p in sorted(Path(root).glob("*/*.json")) if not p.name.endswith(MANIFEST_SUFFIX)]
    return [p for p in found if p.with_name(p.stem + MANIFEST_SUFFIX).is_file()]


def read_template(path: Path) -> tuple[dict, dict]:
    """(template, inject map), both opened for reading only."""
    path = Path(path)
    with open(path, "r", encoding="utf-8") as fh:
        template = json.load(fh)
    with open(path.with_name(path.stem + MANIFEST_SUFFIX), "r", encoding="utf-8") as fh:
        inject = json.load(fh).get("inject", {})
    return template, inject


_INDEXES: dict[str, dict] = {}


def index(root: Path = WORKFLOWS, fresh: bool = False) -> dict[str, dict]:
    """name -> {fp, template, inject, path}; read once per root per process."""
    key = str(Path(root).resolve())
    if fresh or key not in _INDEXES:
        built = {}
        for path in template_paths(root):
            template, inject = read_template(path)
            built[path.stem] = {"fp": fingerprint(template, inject), "template": template,
                                "inject": inject, "path": str(path)}
        _INDEXES[key] = built
    return _INDEXES[key]


def is_link(value: Any) -> bool:
    return isinstance(value, list) and len(value) == 2 and isinstance(value[1], int) and isinstance(value[0], str)


def cover(graph: dict, template: dict) -> float:
    """The share of the template's node ids the graph holds with the same class."""
    nodes = [k for k, n in template.items() if isinstance(n, dict)]
    same = sum(1 for k in nodes if (graph.get(k) or {}).get("class_type") == template[k].get("class_type"))
    return same / len(nodes) if nodes else 0.0


def literal_agreement(graph: dict, entry: dict) -> int:
    """How many un-injected template literals the graph still carries unchanged."""
    injected = {(str(s["node"]), s["field"]) for s in entry["inject"].values()}
    agree = 0
    for node_id, node in entry["template"].items():
        for name, value in (node.get("inputs") or {}).items() if isinstance(node, dict) else ():
            if (node_id, name) not in injected and not is_link(value):
                agree += (graph.get(node_id) or {}).get("inputs", {}).get(name) == value
    return agree


def identify(graph: dict, idx: dict[str, dict]) -> str | None:
    """The template this graph was filled from, or None when no template covers it."""
    scored = [(cover(graph, e["template"]), literal_agreement(graph, e), len(e["template"]), name)
              for name, e in idx.items()]
    scored = [s for s in scored if s[0] >= MIN_COVER]
    return max(scored)[3] if scored else None


def class_cover(names: set, template: dict) -> float:
    """The share of the template's distinct classes found in `names`."""
    wanted = {n.get("class_type") for n in template.values() if isinstance(n, dict)}
    return len(wanted & names) / len(wanted) if wanted else 0.0


def identify_classes(names, idx: dict[str, dict]) -> str | None:
    """The template a recorded class SET (P2's section-0 `node_classes`, no node ids) was filled
    from: the best covered, ties to the larger template; None below MIN_COVER."""
    names = set(names or ())
    scored = [(class_cover(names, e["template"]), len(e["template"]), name) for name, e in idx.items()]
    scored = [s for s in scored if s[0] >= MIN_COVER]
    return max(scored)[2] if scored else None


def graph_fields(graph: dict) -> dict[str, Any]:
    """Every literal input as `<node>.<input>`, plus the class multiset under `classes`."""
    fields: dict[str, Any] = {"classes": classes(graph)}
    for node_id in sorted(graph, key=str):
        node = graph[node_id]
        for name, value in sorted((node.get("inputs") or {}).items()) if isinstance(node, dict) else ():
            if not is_link(value):
                fields[f"{node_id}.{name}"] = value
    return fields


def field_diff(asked: dict, recorded: dict) -> list[dict]:
    """Each field whose value differs (or exists on one side only), in key order."""
    return [{"field": k, "recorded": recorded.get(k), "asked": asked.get(k)}
            for k in sorted(set(asked) | set(recorded)) if asked.get(k) != recorded.get(k)]


def inject_values(graph: dict, inject: dict) -> dict[str, Any]:
    """name -> the value the graph holds at that inject point (absent points are left out)."""
    out = {}
    for name, spec in inject.items():
        inputs = (graph.get(str(spec["node"])) or {}).get("inputs", {})
        if spec["field"] in inputs:
            out[name] = inputs[spec["field"]]
    return out


def fields_inject(fields: dict, inject: dict) -> dict[str, Any]:
    """The inject values read back out of a fields dict (a recording's)."""
    keyed = {name: f"{spec['node']}.{spec['field']}" for name, spec in inject.items()}
    return {name: fields[k] for name, k in keyed.items() if k in fields}
