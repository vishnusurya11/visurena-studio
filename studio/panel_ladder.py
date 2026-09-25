"""The panel ladder: what EYE_PANELS climbs when the panel eye lists a fault.

    redraw_grid_seed x1  -> the grid holding the faulted shot is moved to
                            storyboard/superseded/ and drawn again on a bumped
                            seed (grids.py); the panels and both machine gates
                            are rebuilt so the judge reads fresh rows
    reprose          x1  -> the faulted shot's CELL PROSE (`frame`) is led by
                            the cure for its fault (the skill's cure table),
                            through write_plan -- never a beat, a coda or a
                            line, so placed.json stays current -- and the grid
                            is drawn again (its inputs changed, so it was stale)
    keep_best            -> the terminal: the panels stand as drawn, the
                            verdict is signed flagged with every fault listed

At most CAP distinct grids climb per episode (gates.yaml `max_grids`); a
third faulted grid is kept as drawn and flagged.  Each rung is priced at one
grid render (GRID_SECONDS, 1.7 GPU min); the judged gate refuses a rung the
episode ceiling cannot pay for.
"""
from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from studio import episode_home, grid_layout, judged_gate
from studio.judges.verdict import Fault, Verdict
from studio.ladder import Ladder, Rung

GRID_SECONDS = 102.0
"""One grid render: 1.7 GPU minutes (decision §2, EYE-panels)."""
CAP = 2
"""Distinct grids that may climb per episode."""
SUPERSEDED = "superseded"
CURES = {
    "clones": "Each person in the picture is a different man with his own face, build and dress.",
    "clone": "Each person in the picture is a different man with his own face, build and dress.",
    "people": "Only the named people stand in the picture and everything else is the place.",
    "missing": "The named subject stands large at the CENTRE of the frame.",
    "text": "Every surface in the picture is plain, wordless paint.",
    "lettering": "Every surface in the picture is plain, wordless paint.",
    "stacked": "One single picture fills the whole frame edge to edge.",
    "tiled": "One single picture fills the whole frame edge to edge.",
    "blur": "Every edge in the picture is crisp and sharp.",
    "hat": "The hat sits on his head and both his hands are empty.",
    "landmark": "The skyline is the plain skyline of this place.",
    "posture": "The person is {asked} in the picture.",
    "framing": "The frame is cut as a {planned} shot.",
    "copy": "A freshly composed view, closer in than the place picture and turned from it.",
    "repeat": "A view of its own, composed differently from every other shot of this place.",
    "hour": "The light is the hour the place describes.",
    "landform": "The ground runs flat to the horizon.",
    "banned": "The picture holds only the things of this place and its time.",
    "unread": "One clear main subject fills the frame.",
}
"""kind -> the affirmative phrase that leads the cell prose (the skill: put the
defining detail FIRST; a detail buried mid-sentence is dropped)."""


def cure(kind: str, evidence: dict) -> str:
    """The phrase for one fault kind, filled from its evidence."""
    phrase = CURES.get(kind, CURES["unread"])
    return phrase.format(asked=evidence.get("asked", "as the shot says"),
                         planned=str(evidence.get("planned", "")).replace("_", " ") or "the planned")


def shots_of(faults: list[Fault]) -> list[int]:
    """The distinct shots the faults name, in order."""
    out = []
    for f in faults:
        tail = str(f.where).rsplit("_", 1)[-1]
        if tail.isdigit() and int(tail) not in out:
            out.append(int(tail))
    return out


def reprose(doc: dict, index: int, faults: list[Fault]) -> dict:
    """The plan with shot `index`'s frame led by the cures for its faults,
    each written once; every other field and shot untouched."""
    out = {**doc, "shots": [dict(s) for s in doc.get("shots") or []]}
    for shot in out["shots"]:
        if int(shot["index"]) != index:
            continue
        phrases = [cure(f.kind, f.evidence) for f in faults if f.where == f"shot_{index:02d}"]
        lead = [p for p in dict.fromkeys(phrases) if p not in shot["frame"]]
        if lead:
            shot["frame"] = " ".join(lead + [shot["frame"]])
    return out


def reprose_plan(path: Path, doc: dict, index: int, faults: list[Fault]) -> Path:
    """The cured plan written through the contract (write_plan refuses a plan
    the contract does not accept and leaves the file as it was)."""
    return episode_home.write_plan(Path(path), reprose(doc, index, faults))


def supersede(board: Path, name: str) -> int:
    """Move the grid's png/json/txt to superseded/<name>_v<k>.*; k is the seed bump."""
    room = Path(board) / SUPERSEDED
    room.mkdir(parents=True, exist_ok=True)
    k = len(list(room.glob(f"{name}_v*.png"))) + 1
    for ext in ("png", "json", "txt"):
        source = Path(board) / "grids" / f"{name}.{ext}"
        if source.exists():
            shutil.move(str(source), str(room / f"{name}_v{k}.{ext}"))
    return k


@dataclass
class Climb:
    """One episode's climb: which grids have climbed, under the cap."""
    ctx: object
    home: Path
    rebuild: Callable[[], None]
    cap: int = CAP
    redrawn: list[str] = field(default_factory=list)

    def grids_of(self, rows: list[dict], shots: list[int]) -> list[dict]:
        """The layout rows holding the faulted shots, in layout order."""
        return [r for r in rows if set(r.get("shots") or []) & set(shots)]

    def climbing(self, rows: list[dict], shots: list[int]) -> list[dict]:
        """The faulted grids allowed to climb: those already climbing, then new
        ones while the cap allows."""
        out = []
        for row in self.grids_of(rows, shots):
            name = grid_layout.name_of(getattr(self.ctx, "number", 0), row)
            if name in self.redrawn or len(self.redrawn) < self.cap:
                out.append(row)
                self.redrawn += [] if name in self.redrawn else [name]
        return out

    def kept(self, rows: list[dict], shots: list[int]) -> list[dict]:
        """The faulted grids the cap keeps as drawn."""
        names = {grid_layout.name_of(getattr(self.ctx, "number", 0), r): r for r in self.grids_of(rows, shots)}
        return [r for name, r in names.items() if name not in self.redrawn]

    def redraw(self, row: dict) -> None:
        bump = supersede(self.home / "storyboard", grid_layout.name_of(self.ctx.number, row))
        self.ctx.run_script("scripts/episode/grids.py", *grid_layout.argv(row), f"--seed-bump={bump}",
                            gpu=True, clock="grids")

    def cure_prose(self, rows: list[dict], faults: list[Fault]) -> None:
        plan = self.home / "plan.json"
        doc = episode_home.read_json(plan)
        for row in rows:
            for index in row.get("shots") or []:
                if index in shots_of(faults):
                    doc = reprose(doc, int(index), faults)
        episode_home.write_plan(plan, doc)

    def take(self, rung: Rung, i: int, verdict: Verdict) -> None:
        """One rung: the climbing grids reprosed (that rung only) and redrawn;
        the panels and rows rebuilt for the judge's next read."""
        rows = self.climbing(grid_layout.read(self.home), shots_of(verdict.faults))
        if rung.name == "reprose":
            self.cure_prose(rows, verdict.faults)
        for row in rows:
            self.redraw(row)
        self.rebuild()

    def keep_best(self, verdict: Verdict) -> Verdict:
        """The terminal: the panels stand; each fault says whether its grid climbed."""
        rows = grid_layout.read(self.home)
        kept = {int(i) for r in self.kept(rows, shots_of(verdict.faults)) for i in r.get("shots") or []}
        faults = [f.model_copy(update={"evidence": {**f.evidence, "climbed": not (set(shots_of([f])) & kept)}})
                  for f in verdict.faults]
        return verdict.model_copy(update={"faults": faults})

    @property
    def rungs(self) -> judged_gate.Rungs:
        return judged_gate.Rungs(ladder(), self.take)


def ladder() -> Ladder:
    return Ladder([Rung("redraw_grid_seed", GRID_SECONDS), Rung("reprose", GRID_SECONDS)], "keep_best")


def climb(ctx, rebuild: Callable[[], None], cap: int = CAP) -> Climb:
    return Climb(ctx, Path(ctx.home), rebuild, cap)


def rungs(ctx, rebuild: Callable[[], None], cap: int = CAP) -> judged_gate.Rungs:
    """The rungs alone, for a caller that keeps the default terminal."""
    return climb(ctx, rebuild, cap).rungs


def keep_best(verdict: Verdict) -> Verdict:
    """The climb-less terminal: the panels stand as drawn."""
    return verdict
