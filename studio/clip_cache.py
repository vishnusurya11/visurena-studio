"""Is this clip still the clip the plan asks for?

`is_complete` answers whether a file is finished and readable, which is a good
question and not this one.  It was used as the skip condition, so when both
trailer plans were rebuilt from scratch -- new shot selection, new order, new
prompts -- every beat was skipped as "exists" because the beat IDs were still
B00..B08.  Nine of nine Scarlet clips and eleven of fourteen Jekyll clips were
the OLD renders wearing the new plan's names.  The render reported success.

A clip's identity is its recipe, not its slot.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

SIDECAR = ".recipe.json"


def digest_of(path: Path) -> str:
    """A content hash of a reference sheet, so regenerating one invalidates
    every clip bound to it -- which is the whole point when a colliding cast
    is about to be rebuilt."""
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


def fingerprint(recipe: dict) -> str:
    """A stable hash of everything that decides what the model draws.

    `sort_keys` because a dict is unordered and a recipe is not a document;
    the LIST order inside `refs` is preserved on purpose, since <Subject 1>
    and <Subject 2> bind positionally.
    """
    canonical = json.dumps(recipe, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def sidecar_for(video: Path) -> Path:
    return video.with_suffix("").with_suffix(SIDECAR) if video.suffix \
        else video.with_name(video.name + SIDECAR)


def record(video: Path, recipe: dict) -> Path:
    """Write the recipe beside the clip it produced."""
    path = sidecar_for(video)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"fingerprint": fingerprint(recipe)}, indent=2),
                    encoding="utf-8")
    return path


def is_current(video: Path, recipe: dict) -> bool:
    """True only when this clip was rendered from THIS recipe.

    A missing sidecar is not current.  Every clip rendered before this module
    existed re-renders once, which is correct: we cannot tell what made them.
    """
    path = sidecar_for(video)
    if not path.exists():
        return False
    try:
        stored = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return False
    return stored.get("fingerprint") == fingerprint(recipe)
