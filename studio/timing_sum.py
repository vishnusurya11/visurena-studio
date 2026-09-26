"""A unit's GPU seconds, from its clock (decision 2026-09-25, the Command Center).

`episodes/epNN/timing.jsonl` (studio/episode_clock) has one row per stage run,
under names the steps chose before the registry existed (`takes`, `grids`,
`lines` ...).  STAGES maps each name to the registry step that stamps it and
whether the run held the GPU -- the `gpu=` each step passes to
`ctx.run_script` -- so `gpu_seconds_of` can sum every pass of a GPU stage,
retries and failures included: a retry is GPU time too.  A name the table
does not know is REPORTED by `unmapped`, never summed and never guessed.

Nothing here writes: C7's tick reads these at unit end and settles the row.
"""
from __future__ import annotations

import json
from pathlib import Path

CLOCK = "timing.jsonl"

# name -> (registry step id or None for a name no step stamps today, held the GPU)
STAGES: dict[str, tuple[str | None, bool]] = {
    "bind": ("01", False),
    "places": ("03", True),
    "cast": ("04", True), "lines": ("04", True), "speaker_check": ("04", False),
    "respot": ("05", False), "timeline": ("05", False),
    "prompts": ("06", False), "no_last_frame": ("06", False),
    "grids": ("07", True), "frames": ("07", True),
    "panels": ("08", False), "panel_dq": ("08", False), "panel_content": ("08", True),
    "takes": ("09", True), "take_dq": ("09", True), "take_content": ("09", True),
    "strip": ("09", False),
    "title": ("10", True), "assemble": ("10", True),
    "qc": ("11", True), "dossier": ("11", False), "eye_review": ("11", False),
    # names from before refs and publish were departments of their own
    "sheets": (None, True), "publish": (None, False),
}


def rows(home_dir: Path) -> list[dict]:
    """Every row of the unit's clock; [] when it has none."""
    path = Path(home_dir) / CLOCK
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()]


def is_gpu(name: str) -> bool:
    """Whether a run under this name held the GPU; an unknown name did not."""
    return STAGES.get(name, (None, False))[1]


def gpu_seconds_of(home_dir: Path) -> float:
    """The sum of every GPU pass's seconds, retries and failures included."""
    return round(sum(float(r.get("seconds") or 0) for r in rows(home_dir) if is_gpu(r.get("stage", ""))), 1)


def unmapped(home_dir: Path) -> list[str]:
    """The names in the clock the table does not know, sorted, each once."""
    return sorted({r.get("stage", "") for r in rows(home_dir)} - set(STAGES))


def step_seconds_of(home_dir: Path) -> dict[str, float]:
    """Seconds per registry step, the clock's names folded to step ids; a name
    with no step today, and an unknown one, fold to nothing."""
    out: dict[str, float] = {}
    for r in rows(home_dir):
        step_id = STAGES.get(r.get("stage", ""), (None, False))[0]
        if step_id:
            out[step_id] = round(out.get(step_id, 0.0) + float(r.get("seconds") or 0), 1)
    return out
