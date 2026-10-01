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

A framing or posture fault takes no rung (REDRAW_CANNOT_CURE): it goes to
keep_best, flagged, since no rung ever moved one on ep13.

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

from studio import episode_home, grid_layout, grid_room, judged_gate, panel_dq
from studio.judges.verdict import Fault, Verdict
from studio.ladder import Ladder, Rung

GRID_SECONDS = 102.0
"""One grid render: 1.7 GPU minutes (decision §2, EYE-panels)."""
RUNG_SECONDS = 1900.0
"""What a rung COSTS, measured on ep13 (2026-09-27): the redraw, the rebuild
with its content read (1107-1224 s) and the eye's read of every panel (~740 s).
Priced at one grid, the gate climbed into rungs it could not finish and
deferred after the work was spent (speed plan #3)."""
CAP = 2
"""Distinct grids that may climb per episode."""
SUPERSEDED = "superseded"
REDRAW_CANNOT_CURE = frozenset({"framing", "posture", "place"})
"""MEASURED on ep13 (speed plan #4): nine climbs, and no seed or reprose rung
ever moved a framing or posture fault; a prompt fix (9cb4609) and judge fixes
did.  Such a fault goes to keep_best, flagged, at no GPU cost."""
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
    "copy": "The same room as the staged place picture, seen closer, with the same walls, furniture, windows and light.",
    "repeat": "The same room as the other shots of this place, with its own subject and framing.",
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


def write_cured(plan: Path, doc: dict) -> Path:
    """A frame-only cure written AND re-signed for the new bytes (step 03's
    resign pattern).  ep14 (five-hour plan, 2026-09-30): a reprose left the
    plan's signature on the old sha8, so every restart between the reprose and
    the first take re-ran the whole plan ladder and redrew the grids -- 3.5 h.
    A reprose edits only `frame`, which the timing contract does not read, so
    the judged verdict still covers the plan."""
    from studio import plan_verdict
    out = episode_home.write_plan(Path(plan), doc)
    if previous := plan_verdict.read(Path(plan)):
        kw = {"signed_by": previous["signed_by"]} if previous.get("signed_by") else {}
        plan_verdict.sign(Path(plan), f"{previous.get('note', '')} · reprose (08)".strip(" ·"),
                          faults=previous.get("faults"), flagged=bool(previous.get("flagged", False)), **kw)
    return out


# ---- the climb remembered on disk (five-hour plan fix 2, 2026-09-30) -------------

LADDER_FILE = "ladder.json"
"""storyboard/ladder.json, mirroring takes/r2v/ladder.json: which grids have
climbed, ACROSS RESUMES.  `Climb.redrawn` was process memory, and ep14 redrew
waterloo_station 9 times against a cap of 2."""


def _ladder_path(home: Path) -> Path:
    return Path(home) / "storyboard" / LADDER_FILE


def load_climbed(home: Path) -> list[str]:
    path = _ladder_path(home)
    if not path.exists():
        return []
    import json
    return list(json.loads(path.read_text(encoding="utf-8")).get("climbed", []))


def remember_climbed(home: Path, name: str) -> None:
    import json
    import time
    path = _ladder_path(home)
    doc = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    if name not in doc.setdefault("climbed", []):
        doc["climbed"].append(name)
        doc.setdefault("at", {})[name] = round(time.time(), 1)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(doc, indent=1), encoding="utf-8")


def merge_content_rows(old: list[dict], fresh: list[dict]) -> list[dict]:
    """A partial content read lands beside the untouched rows (fix 2c: a
    redraw re-reads only its own panels), replacing by shot, never wiping."""
    by = {int(r["shot"]): r for r in old}
    by.update({int(r["shot"]): r for r in fresh})
    return [by[k] for k in sorted(by)]


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

    def draw(self, row: dict) -> None:
        bump = supersede(self.home / "storyboard", grid_layout.name_of(self.ctx.number, row))
        self.ctx.run_script("scripts/episode/grids.py", *grid_layout.argv(row), f"--seed-bump={bump}",
                            gpu=True, clock="grids")

    def redraw(self, row: dict) -> None:
        """A redrawn ANCHOR re-cuts its setup's room and redraws the siblings
        that stage it (one room per setup, 2026-09-28); any other grid alone."""
        self.draw(row)
        rows = grid_layout.read(self.home)
        name = grid_layout.name_of(self.ctx.number, row)
        mine = next((r for r in rows if grid_layout.name_of(self.ctx.number, r) == name), None)
        cells = episode_home.read_json(self.home / "plan.json").get("shots") or []
        kin = grid_room.siblings(rows, mine, cells) if mine else []
        if kin:
            grid = self.home / "storyboard" / "grids" / f"{name}.png"
            grid_room.cut_room(grid, mine, grid_room.anchor_shot(cells, mine["setup"]),
                               grid_room.room_path(self.home, mine["setup"]))
            for r in kin:
                self.draw(r)

    def cure_prose(self, rows: list[dict], faults: list[Fault]) -> None:
        plan = self.home / "plan.json"
        doc = episode_home.read_json(plan)
        for row in rows:
            for index in row.get("shots") or []:
                if index in shots_of(faults):
                    doc = reprose(doc, int(index), faults)
        write_cured(plan, doc)      # written AND re-signed: a resume must not re-open the plan

    def take(self, rung: Rung, i: int, verdict: Verdict) -> None:
        """One rung: the climbing grids reprosed (that rung only) and ALL
        redrawn back to back (the grid model stays resident), then ONE rebuild
        scoped to the redrawn shots.  Only the faults a redraw can cure choose
        the grids; each climb is remembered on disk so the cap survives a
        resume."""
        faults = cured_by_redraw(verdict)
        rows = self.climbing(grid_layout.read(self.home), shots_of(faults))
        if rung.name == "reprose":
            self.cure_prose(rows, faults)
        for row in rows:
            remember_climbed(self.home, grid_layout.name_of(getattr(self.ctx, "number", 0), row))
            self.redraw(row)
        touched = sorted({int(i) for r in rows for i in r.get("shots") or []})
        try:
            self.rebuild(touched or None)
        except TypeError:           # an older caller's rebuild takes no scope
            self.rebuild()

    def keep_best(self, verdict: Verdict) -> Verdict:
        """The terminal: the panels stand; each fault says whether its grid climbed."""
        rows = grid_layout.read(self.home)
        kept = {int(i) for r in self.kept(rows, shots_of(verdict.faults)) for i in r.get("shots") or []}
        faults = [f.model_copy(update={"evidence": {**f.evidence, "climbed": not (set(shots_of([f])) & kept)}})
                  for f in verdict.faults]
        return verdict.model_copy(update={"faults": faults})

    def curable(self, verdict: Verdict) -> bool:
        """A redraw could move a fault AND the machine gates still fail a panel."""
        return curable(verdict) and not machine_clean(self.home)

    @property
    def rungs(self) -> judged_gate.Rungs:
        return judged_gate.Rungs(ladder(), self.take, curable=self.curable)


def cured_by_redraw(verdict: Verdict) -> list[Fault]:
    return [f for f in verdict.faults if f.kind not in REDRAW_CANNOT_CURE]


def curable(verdict: Verdict) -> bool:
    """Whether a redraw can move any of these faults."""
    return bool(cured_by_redraw(verdict))


MACHINE = ("panel_dq.json", "panel_content.json")


def machine_clean(home: Path) -> bool:
    """Both machine gates pass every panel the plan names.  A RUNG MAY NOT UNDO A
    CLEAN BOARD: ep14 (2026-09-28) -- the seed rung left 30/30 panels clean, the
    eye's OCR lettering still read curable, the reprose rung redrew the Waterloo
    grid, lettering came back on shot 5 and keep_best kept it; the takes refused.
    Past this point the eye's faults are signed flagged, not climbed."""
    board, plan = Path(home) / "storyboard", Path(home) / "plan.json"
    shots = [int(s["index"]) for s in episode_home.read_json(plan).get("shots") or []] if plan.exists() else []
    panels = sorted(board.glob("shot_*.png"))
    return bool(shots) and not any(panel_dq.panel_refusal(board / name, panels, shots) for name in MACHINE)


def ladder() -> Ladder:
    return Ladder([Rung("redraw_grid_seed", RUNG_SECONDS), Rung("reprose", RUNG_SECONDS)], "keep_best")


def climb(ctx, rebuild: Callable[[], None], cap: int = CAP) -> Climb:
    return Climb(ctx, Path(ctx.home), rebuild, cap, redrawn=load_climbed(Path(ctx.home)))


def rungs(ctx, rebuild: Callable[[], None], cap: int = CAP) -> judged_gate.Rungs:
    """The rungs alone, for a caller that keeps the default terminal."""
    return climb(ctx, rebuild, cap).rungs


def keep_best(verdict: Verdict) -> Verdict:
    """The climb-less terminal: the panels stand as drawn."""
    return verdict
