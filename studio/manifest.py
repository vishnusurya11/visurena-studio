"""The unit manifest: what crosses a department boundary.

A department's last step writes ONE `manifest.json` at the unit's home
(decision 2026-09-25, the Command Center): the inputs and outputs the registry
declares (`in:` / `out:` in stages.yaml) matched on disk with their sha8, every
verdict file with who signed it and the word as it stands, the steps' latest
events and the cost.  A requires is satisfied by the upstream manifest's row,
never by a sentence.  Every path is book-relative posix; the absolute root is
the caller's `book_dir` and is never stored.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath

from pydantic import BaseModel, Field

from studio import db, registry
from studio.judges import verdict as jv

FILE = "manifest.json"
VERDICTS: dict[str, tuple[tuple[str, str, str], ...]] = {
    "episode": (("PLAN", "02", "episodes/{unit}/plan.verdict.json"),
                ("EYE_PANELS", "08", "episodes/{unit}/storyboard/eye_*.json"),
                ("EYE_TAKES", "09", "episodes/{unit}/takes/r2v/eye_*.json"),
                ("MASTER", "11", "episodes/{unit}/review/eye_*.json")),
    "refs": (("LOOK", "04", "refs/verdict.json"),),
}
"""Where each judged gate signs, by stage: (gate, the step answerable for it, the
file).  The gate names are gates.yaml's; the file is that step's `out:` in the
registry (a test holds them together); the step id is what the Command Center
reads when the step completes (C3)."""


def gates_of(stage: str, step_id: str) -> list[tuple[str, str]]:
    """The (gate, file pattern) pairs one step signs; [] for a step that signs nothing."""
    return [(gate, pattern) for gate, step, pattern in VERDICTS.get(stage, ()) if step == step_id]


class Input(BaseModel):
    path: str
    sha8: str


class Output(BaseModel):
    kind: str            # the step that wrote it, by name: plan, shoot, edit ...
    path: str
    sha8: str


class VerdictRow(BaseModel):
    gate: str
    path: str
    signed_by: str       # judge:<name>@<version> or owner
    word: str            # APPROVE | pass | flagged | "" -- as the file says it
    terminal: str = ""   # the rung a judge ended on, when it did


class Cost(BaseModel):
    wall_seconds: float = 0.0
    gpu_seconds: float = 0.0     # C5 fills it from the clock's stage map; zero until then
    usd: float = 0.0


class UnitManifest(BaseModel):
    codex_id: str
    stage: str
    unit: str
    inputs: list[Input] = Field(default_factory=list)
    outputs: list[Output] = Field(default_factory=list)
    verdicts: list[VerdictRow] = Field(default_factory=list)
    cost: Cost = Field(default_factory=Cost)
    steps: dict[str, str] = Field(default_factory=dict)


def sha8_of(path: Path) -> str:
    """The first 8 hex of the file's sha256, read in blocks: the same word the
    plan, pack and master verdicts already bind to."""
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()[:8]


def home_of(stage: str, unit: str) -> str:
    """The unit's home: the folder its deliverable lives in."""
    deliverable = registry.deliverable_of(stage, unit)
    if deliverable is None:
        raise ValueError(f"stage {stage!r} declares no deliverable, so no home")
    return PurePosixPath(deliverable).parent.as_posix()


def manifest_path(book_dir: Path, home: str) -> Path:
    return Path(book_dir) / home / FILE


def write_manifest(book_dir: Path, home: str, manifest: UnitManifest, extra: dict | None = None) -> Path:
    """The manifest at the unit's home; a step's own keys (`extra`) sit beside
    the contract's, and the contract's win on a clash."""
    path = manifest_path(book_dir, home)
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = {**(extra or {}), **manifest.model_dump()}
    path.write_text(json.dumps(doc, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def read_manifest(book_dir: Path, home: str) -> UnitManifest | None:
    path = manifest_path(book_dir, home)
    if not path.exists():
        return None
    return UnitManifest.model_validate_json(path.read_text(encoding="utf-8"))


def matched(book_dir: Path, patterns: list[str]) -> list[str]:
    """Every file under the book a pattern names, book-relative posix, sorted, once."""
    book = Path(book_dir)
    found: set[str] = set()
    for pattern in patterns:
        found.update(p.relative_to(book).as_posix() for p in book.glob(pattern) if p.is_file())
    return sorted(found)


def inputs_for(book_dir: Path, stage: str, unit: str) -> list[Input]:
    patterns = [p for s in registry.steps(stage) for p in registry.inputs_of(stage, s["id"], unit)]
    return [Input(path=rel, sha8=sha8_of(Path(book_dir) / rel)) for rel in matched(book_dir, patterns)]


def outputs_for(book_dir: Path, stage: str, unit: str) -> list[Output]:
    """One row per output file, kind = the first step that declares it; the
    manifest never names itself."""
    own = PurePosixPath(home_of(stage, unit), FILE).as_posix()
    rows: dict[str, Output] = {}
    for step in registry.steps(stage):
        for rel in matched(book_dir, registry.outputs_of(stage, step["id"], unit)):
            if rel != own and rel not in rows:
                rows[rel] = Output(kind=step["name"], path=rel, sha8=sha8_of(Path(book_dir) / rel))
    return [rows[k] for k in sorted(rows)]


def read_verdict(book_dir: Path, gate: str, rel: str) -> VerdictRow:
    """The verdict file's own words: who signed (the owner when no judge did),
    the verdict word and the terminal rung, as they are."""
    doc = json.loads((Path(book_dir) / rel).read_text(encoding="utf-8"))
    signed_by = doc.get("signed_by") or doc.get("reviewed_by") or jv.OWNER
    return VerdictRow(gate=gate, path=rel, signed_by=str(signed_by),
                      word=str(doc.get("verdict") or ""), terminal=str(doc.get("terminal") or ""))


def verdicts_for(book_dir: Path, stage: str, unit: str) -> list[VerdictRow]:
    rows = []
    for gate, _step, pattern in VERDICTS.get(stage, ()):
        rows += [read_verdict(book_dir, gate, rel) for rel in matched(book_dir, [pattern.replace("{unit}", unit)])]
    return rows


def cost_for(book_dir: Path, home: str) -> Cost:
    """Wall seconds off the unit's timing.jsonl when it keeps one; zeros otherwise."""
    path = Path(book_dir) / home / "timing.jsonl"
    if not path.exists():
        return Cost()
    rows = [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
    return Cost(wall_seconds=round(sum(float(r.get("seconds", 0.0)) for r in rows), 1))


def manifest_for(ctx, stage: str) -> UnitManifest:
    """The manifest of the context's unit as the disk and the ledger stand now."""
    unit = ctx.unit or "book"
    home = home_of(stage, unit)
    return UnitManifest(codex_id=ctx.codex_id, stage=stage, unit=unit,
                        inputs=inputs_for(ctx.book_dir, stage, unit),
                        outputs=outputs_for(ctx.book_dir, stage, unit),
                        verdicts=verdicts_for(ctx.book_dir, stage, unit),
                        cost=cost_for(ctx.book_dir, home),
                        steps=db.unit_status(ctx.conn, ctx.codex_id, stage, unit))
