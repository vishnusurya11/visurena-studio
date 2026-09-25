"""The sheet ladder: what refs/04 does with a sheet the LOOK judge faulted.

    redraw_seed           x1   the same words on a bumped seed                     ~2.5 GPU min
    defining_state_first  x1   the sentences carrying the missing nouns moved to the
                               front of the prompt -- a noun 55 words in is not drawn
                               (scripts/refs/places.py) -- else the design's silhouette
                               line prepended                                        ~2.5 GPU min
    keep_best             the terminal: of every try of a sheet, the one with the
                          fewest hard faults is restored; a lookalike pair stays
                          BOUND, flagged, and the take identity judge catches the
                          consequence

A redraw goes through the pack's own manifest values (refs_pack.values_for)
and is logged to refs/pack.jsonl, so the verdict signed afterwards binds to
it; the picture it replaces is kept beside it under superseded/.  `run=` is
comfy.run and is injectable.  The refs context has no budget of its own: the
ladder climbs on one of its own (LADDER_CEILING_SECONDS) and every rung's
seconds land in the learning judged_gate writes.
"""
from __future__ import annotations

import importlib
import json
import re
import shutil
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from studio import refs_pack
from studio.judges.verdict import Fault, Verdict
from studio.ladder import Ladder, Rung
from studio.run_budget import Budget

REDRAW_SECONDS = 150
"""One sheet on the local image model, 2x upscaled: ~2.5 GPU min (decision §2)."""
LADDER_CEILING_SECONDS = 3600
"""One GPU hour of redraws per pack; past it the terminal keeps what it has."""
LADDERS = "ladders"
LADDER = Ladder([Rung("redraw_seed", REDRAW_SECONDS), Rung("defining_state_first", REDRAW_SECONDS)],
                terminal="keep_best")
SUPERSEDED = "superseded"
SHEET_SIZE = (1536, 1024)
"""The size every refs_pack job draws at; a row without a job is drawn the same."""
PACK = "refs/pack.jsonl"
HARD = frozenset({"must_noun", "lettering", "extra_limb", "lookalike", "identity"})
BOUND_NOTE = "bound flagged: the take identity judge catches the consequence"
SENTENCE = re.compile(r"[^.!?]+[.!?]*")


def budget(clock: Callable[[], float] | None = None) -> Budget:
    """The ladder's own clock share, for a context that has none."""
    return Budget(LADDER_CEILING_SECONDS, {LADDERS: 1.0}, clock or time.monotonic)


# ---- the pack ---------------------------------------------------------------------

def pack_rows(book_dir: Path | str) -> list[dict]:
    path = Path(book_dir) / PACK
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def latest(rows: list[dict], paths: list[str]) -> list[dict]:
    """The last row per path, in the order `paths` gives."""
    last = {}
    for row in rows:
        last[row["path"]] = row
    return [last[p] for p in paths if p in last]


def append_row(book_dir: Path | str, row: dict) -> None:
    with (Path(book_dir) / PACK).open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def jobs_of(book_dir: Path | str) -> dict[str, refs_pack.Job]:
    """Every job build_pack would draw, by its relpath."""
    bp = importlib.import_module("scripts.refs.build_pack")
    return {refs_pack.relpath(j): j for j in bp.all_jobs(Path(book_dir), bp.KINDS, None)}


def job_from_row(path: str, row: dict) -> refs_pack.Job:
    """A pack row with no design behind it (a place drawn per episode from the
    plan's words): its own workflow and prompt, at the pack's sheet size."""
    kind, entity, name = path.split("/")[1:4]
    return refs_pack.Job(kind, entity, Path(name).stem, row.get("workflow") or refs_pack.T2I,
                         row["prompt"], *SHEET_SIZE)


def silhouette_of(book_dir: Path | str, job: refs_pack.Job) -> str:
    """The design's one-line silhouette: the defining state in the dossier's own words."""
    card = Path(book_dir) / "analysis" / job.kind / f"{job.entity}.json"
    if not card.exists():
        return ""
    design = (json.loads(card.read_text(encoding="utf-8")).get("profile") or {}).get("design") or {}
    return str(design.get("silhouette") or "").strip()


# ---- the prompt rule ----------------------------------------------------------------

def sentences(prompt: str) -> list[str]:
    return [s.strip() for s in SENTENCE.findall(prompt or "") if s.strip()]


def state_first(prompt: str, nouns: list[str], silhouette: str = "") -> str:
    """The sentences that carry any of `nouns` moved to the front, in their own
    order; with no noun naming a sentence, the silhouette prepended (if any)."""
    parts = sentences(prompt)
    carry = [s for s in parts if any(re.search(rf"\b{re.escape(n)}s?\b", s, re.I) for n in nouns)]
    if carry:
        return " ".join(carry + [s for s in parts if s not in carry])
    if silhouette:
        lead = silhouette if silhouette.endswith((".", "!", "?")) else silhouette + "."
        return " ".join([lead] + parts)
    return prompt


def faulted(verdict: Verdict) -> dict[str, list[Fault]]:
    """The hard faults per sheet path, in first-fault order."""
    out: dict[str, list[Fault]] = {}
    for f in verdict.faults:
        if f.kind in HARD:
            out.setdefault(f.where, []).append(f)
    return out


def nouns_missing(faults: list[Fault]) -> list[str]:
    out: list[str] = []
    for f in faults:
        out += [n for n in f.evidence.get("missing", []) if n not in out]
    return out


# ---- the redraw ---------------------------------------------------------------------

def supersede(book_dir: Path | str, path: str, n: int) -> Path:
    """The live picture copied aside as try `n`; the live file stays for the redraw to replace."""
    live = Path(book_dir) / path
    aside = live.parent / SUPERSEDED / f"{live.stem}_try{n}{live.suffix}"
    aside.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(live, aside)
    return aside


def redraw(book_dir: Path | str, job: refs_pack.Job, prompt: str, seed: int, run: Callable) -> Path:
    """One picture through the pack's manifest values with these words and this seed."""
    values = {**refs_pack.values_for(job), "prompt": refs_pack.styled(prompt), "seed": seed}
    out = run(job.workflow, values)[0]
    target = Path(book_dir) / refs_pack.relpath(job)
    shutil.copyfile(out, target)
    return target


@dataclass
class Try:
    file: Path
    faults: list[Fault]
    prompt: str
    seed: int
    workflow: str = refs_pack.T2I


@dataclass
class SheetLadder:
    """One pack's climb: `take` is the Rungs' take, `keep_best` its terminal."""
    book_dir: Path
    run: Callable | None = None
    tries: dict[str, list[Try]] = field(default_factory=dict)
    jobs: dict[str, refs_pack.Job] | None = None

    def job(self, path: str, row: dict) -> refs_pack.Job:
        """The design's job for this path, else one built from the row itself."""
        if self.jobs is None:
            self.jobs = jobs_of(self.book_dir)
        return self.jobs.get(path) or job_from_row(path, row)

    def words(self, rung: Rung, row: dict, job: refs_pack.Job, faults: list[Fault]) -> tuple[str, int]:
        """(prompt, seed) this rung draws with: the row's seed bumped; the
        prompt as it was, or with the defining state first."""
        seed = int(row.get("seed", 0)) + 1
        if rung.name == "defining_state_first":
            return state_first(row["prompt"], nouns_missing(faults), silhouette_of(self.book_dir, job)), seed
        return row["prompt"], seed

    def retry(self, rung: Rung, path: str, faults: list[Fault]) -> None:
        row = latest(pack_rows(self.book_dir), [path])[0]
        job = self.job(path, row)
        tries = self.tries.setdefault(path, [])
        aside = supersede(self.book_dir, path, len(tries) + 1)
        tries.append(Try(aside, faults, row["prompt"], int(row.get("seed", 0)), job.workflow))
        prompt, seed = self.words(rung, row, job, faults)
        started = time.monotonic()
        redraw(self.book_dir, job, prompt, seed, self.run or _comfy_run())
        append_row(self.book_dir, {"path": path, "workflow": job.workflow, "prompt": prompt, "seed": seed,
                                   "seconds": round(time.monotonic() - started, 1), "rung": rung.name})

    def take(self, rung: Rung, i: int, verdict: Verdict) -> None:
        """Every sheet the verdict faulted hard is redrawn for this rung."""
        for path, faults in faulted(verdict).items():
            self.retry(rung, path, faults)

    def keep_best(self, verdict: Verdict) -> Verdict:
        """The terminal: per climbed sheet, the try with the fewest hard faults
        is what stays on disk (the latest on a tie); the verdict lists that
        try's faults, a pair bound flagged."""
        faults = list(verdict.faults)
        for path, tries in self.tries.items():
            live = Try(Path(self.book_dir) / path, [f for f in faults if f.where == path], "", 0)
            best = best_of(tries + [live])
            if best is not live:
                faults = [f for f in faults if f.where != path] + best.faults
                self.restore(path, best, len(tries) + 1)
        return verdict.model_copy(update={"faults": [bound(f) for f in faults]})

    def restore(self, path: str, best: Try, n: int) -> None:
        supersede(self.book_dir, path, n)
        shutil.copyfile(best.file, Path(self.book_dir) / path)
        append_row(self.book_dir, {"path": path, "workflow": best.workflow, "prompt": best.prompt,
                                   "seed": best.seed, "seconds": 0.0, "rung": "keep_best", "kept": best.file.name})


def best_of(tries: list[Try]) -> Try:
    """The fewest hard faults; on a tie the latest try, which is what is on disk."""
    return min(reversed(tries), key=lambda t: sum(f.kind in HARD for f in t.faults))


def bound(fault: Fault) -> Fault:
    """A lookalike or identity fault at the terminal: both sheets stay, flagged."""
    if fault.kind in ("lookalike", "identity") and not fault.note:
        return fault.model_copy(update={"note": BOUND_NOTE})
    return fault


def _comfy_run() -> Callable:
    from studio import comfy
    return comfy.run
