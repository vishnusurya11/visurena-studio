"""The casebook: one row per (artefact, verdict source), the set every judge
is benched against.

    library/<book>/casebook/labels.jsonl   harvested, regenerable (harvest_labels.py)
    library/<book>/casebook/owner.jsonl    the casebook proper: append-only, the only
                                           file a person edits

A row names a fault from the CLOSED list below or it is no row; a pass row
carries no class.  `verdict_by` says who said so, and `weight` is how much
that is worth to the bench: owner 1, agent 0.75, publish-by-default 0.5.  A
synthetic row (a corruption drawn to test that a detector can see at all)
weighs nothing toward the owner bar and reports in its own column; an
unverified row (a prose hit nobody confirmed) is not counted at all.

Decision: architecture/decisions/2026-09-24_judges_replace_the_eye.md, section 1.4.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from pydantic import BaseModel, field_validator, model_validator

from studio import db

KINDS = ("sheet", "plan", "grid", "panel", "take", "master")
VERDICTS = ("pass", "fault")
BY = ("owner", "agent", "default", "synthetic", "unverified")
WEIGHTS = {"owner": 1.0, "agent": 0.75, "default": 0.5, "synthetic": 0.0, "unverified": 0.0}
LABELS, OWNER = "labels.jsonl", "owner.jsonl"
NEEDS_REJUDGE = "needs_rejudge.jsonl"
"""Owner rows noted on a file with no machine json of its own bytes: the bench cannot measure them yet."""
SNAPSHOT_KEYS = ("take_dq", "content", "panel_dq", "panel_content", "planned")
"""What an owner row keeps of the machine json: the judges' inputs, never the harvest's shipped-flagged stamp."""

CLASSES = (
    "frozen_start", "frozen_share", "foreign_picture", "cut_early", "off_board",
    "over_push", "face_out", "no_black_floor", "pulse", "lip_lag", "identity_drift",
    "wardrobe", "anchored_slide", "copies", "extra_people", "missing_people",
    "lettering", "stacked_pictures", "posture", "hour", "landform", "blur_warp",
    "orbit_repeat", "same_picture_repeat", "dead_body_moves", "wrong_letters",
    "plan_story", "plan_cast", "mix_levels", "cut_missing", "line_unheard",
    "invented_speech",
    "unknown",
)
"""The closed list, taken from what the sources actually name (research memo D
section 2), plus `unknown` for a rejected attempt whose reason no prose kept:
it counts for recall on "reject" alone, never per class."""


class Row(BaseModel):
    codex: str
    unit: str
    kind: str
    path: str
    sha8: str = ""
    verdict: str
    fault_class: str | None = None
    verdict_by: str
    verdict_at: str = ""
    after_publish: bool = False
    source: str = ""
    region: list[int] | None = None
    machine: dict = {}
    machine_version: str = ""
    stratum: str = ""
    p_select: float | None = None
    seen_by_owner: bool = False
    session_id: str = ""
    rubric_version: str = ""
    repeat_of: str = ""
    latency_ms: int | None = None
    """The label session's fields (fleet H ruling A6): the stratum an item was drawn from, its inclusion
    probability across every stratum it belongs to, whether the owner saw it, which sitting, which rubric,
    the item it repeats (test-retest), and how long he took."""

    @field_validator("kind")
    @classmethod
    def _kind(cls, v):
        if v not in KINDS:
            raise ValueError(f"kind {v!r} is not one of {KINDS}")
        return v

    @field_validator("verdict")
    @classmethod
    def _verdict(cls, v):
        if v not in VERDICTS:
            raise ValueError(f"verdict {v!r} is not one of {VERDICTS}")
        return v

    @field_validator("verdict_by")
    @classmethod
    def _by(cls, v):
        if v not in BY:
            raise ValueError(f"verdict_by {v!r} is not one of {BY}")
        return v

    @field_validator("path")
    @classmethod
    def _relative(cls, v):
        if v.startswith(("/", "\\")) or (len(v) > 1 and v[1] == ":"):
            raise ValueError(f"path {v!r} is absolute; a row names a file relative to its book")
        return v.replace("\\", "/")

    @field_validator("p_select")
    @classmethod
    def _probability(cls, v):
        if v is not None and not 0.0 < v <= 1.0:
            raise ValueError(f"p_select {v} is not an inclusion probability in (0, 1]")
        return v

    @field_validator("region")
    @classmethod
    def _box(cls, v):
        if v is not None and len(v) != 4:
            raise ValueError("region is [x, y, w, h]")
        return v

    @model_validator(mode="after")
    def _class_matches_verdict(self):
        if self.verdict == "fault" and self.fault_class not in CLASSES:
            raise ValueError(f"fault_class {self.fault_class!r} is not in the closed list")
        if self.verdict == "pass" and self.fault_class is not None:
            raise ValueError("a pass row carries no fault_class")
        return self


def sha8_of(path: Path) -> str:
    """The first eight hex digits of the file's sha256; '' when it is gone."""
    path = Path(path)
    if not path.is_file():
        return ""
    return hashlib.sha256(path.read_bytes()).hexdigest()[:8]


def weight(row: Row) -> float:
    return WEIGHTS[row.verdict_by]


def is_shipped(row: Row) -> bool:
    """A kept take that went out: its state is the gate's own, so it is nobody's label."""
    return str(row.machine.get("label_source", "")).startswith("shipped-flagged")


def counted(row: Row) -> bool:
    """Unverified candidates and a flagged shipped take (the gate grading itself) stay out of every metric."""
    return row.verdict_by != "unverified" and not is_shipped(row)


def read_rows(path: Path) -> list[Row]:
    """Every row of one jsonl file; a missing file is no rows."""
    path = Path(path)
    if not path.is_file():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    return [Row.model_validate(json.loads(line)) for line in lines if line.strip()]


def write_rows(path: Path, rows: list[Row]) -> Path:
    """The regenerable file (`labels.jsonl`), written whole."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r.model_dump(), ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    return path


def shadowed(rows: list[Row], overlay: list[Row]) -> list[Row]:
    """Harvested rows minus the default rows an owner (or agent) row overrides on the same path."""
    spoken_for = {(r.kind, r.path) for r in overlay}
    return [r for r in rows if not (r.verdict_by == "default" and (r.kind, r.path) in spoken_for)]


def snapshot(machine: dict | None) -> dict:
    """The judges' inputs out of a machine dict; the harvest's label stamp left behind."""
    return {k: v for k, v in (machine or {}).items() if k in SNAPSHOT_KEYS}


def borrowed(overlay: list[Row], harvested: list[Row]) -> list[Row]:
    """An overlay row with no machine takes the harvested row's on the same artefact -- same bytes only."""
    twins = {(r.kind, r.path, r.sha8): r.machine for r in harvested if r.sha8 and r.machine}
    return [r if r.machine else r.model_copy(update={"machine": snapshot(twins.get((r.kind, r.path, r.sha8)))})
            for r in overlay]


def load(casebook_dir: Path) -> list[Row]:
    """The bench's rows: labels + owner overlay, unverified dropped, defaults
    shadowed by the overlay's rows on the same artefact, an old overlay row given
    the harvested machine of its own bytes."""
    folder = Path(casebook_dir)
    harvested = read_rows(folder / LABELS)
    overlay = borrowed([r for r in read_rows(folder / OWNER) if counted(r)], harvested)
    return shadowed([r for r in harvested if counted(r)], overlay) + overlay


def append_owner(casebook_dir: Path, row: Row) -> Path:
    """One row onto the end of owner.jsonl.  Never rewrites; never takes a candidate."""
    if not counted(row):
        raise ValueError("an unverified row does not belong in the owner overlay: confirm it first")
    target = Path(casebook_dir) / OWNER
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row.model_dump(), ensure_ascii=False) + "\n")
    return target


KINDS_BY_PATH = (("storyboard/grids", "grid"), ("storyboard/shot_", "panel"), ("/takes/", "take"),
                 ("/cut/", "master"), ("/review/", "master"), ("refs/", "sheet"), ("plan", "plan"))
"""The first match names the kind; the grids row sits before the panels' folder."""


def kind_of(artefact: str) -> str:
    """An artefact's casebook kind, read off its book-relative path."""
    path = artefact.replace("\\", "/")
    for needle, kind in KINDS_BY_PATH:
        if needle in path:
            return kind
    raise ValueError(f"{artefact}: not a sheet, plan, grid, panel, take or master path")


def owner_row(codex: str, unit: str, artefact: str, cls: str, words: str, book: Path,
              machine: dict | None = None) -> Row:
    """The owner's row: a fault of the named class, or a pass; the file's sha8 when it is there, and the
    snapshot of the machine json that judged those bytes."""
    today = db.utc_now().strftime("%Y-%m-%d")
    if cls != "pass" and cls not in CLASSES:
        raise ValueError(f"{cls!r} is not a fault class; one of pass, {', '.join(CLASSES)}")
    return Row(codex=codex, unit=unit, kind=kind_of(artefact), path=artefact,
               sha8=sha8_of(Path(book) / artefact),
               verdict="pass" if cls == "pass" else "fault", fault_class=None if cls == "pass" else cls,
               verdict_by="owner", verdict_at=today, source=f"owner note {today}: {words.strip()}",
               machine=snapshot(machine))


def append_needs_rejudge(casebook_dir: Path, row: Row) -> Path:
    """An owner row the bench cannot measure yet, onto the casebook's needs-rejudge list."""
    target = Path(casebook_dir) / NEEDS_REJUDGE
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({"path": row.path, "kind": row.kind, "unit": row.unit, "sha8": row.sha8,
                             "noted_at": row.verdict_at}) + "\n")
    return target


def note_owner(book: Path, codex: str, unit: str, artefact: str, cls: str, words: str,
               machine: dict | None = None) -> Path:
    """One finding of the owner's onto the end of the book's owner.jsonl -- the
    one door for scripts/audit/note.py and for a redo order's note.  A row with
    no machine snapshot also goes on the needs-rejudge list."""
    if not words.strip():
        raise ValueError("say what was seen: the words may not be empty")
    row = owner_row(codex, unit, artefact, cls, words, book, machine)
    if not row.machine:
        append_needs_rejudge(Path(book) / "casebook", row)
    return append_owner(Path(book) / "casebook", row)
