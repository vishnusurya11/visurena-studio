"""The judge's contract: what every judge returns, and what the signers accept.

A judge LISTS faults and code judges the list; no model is ever asked "is this
right".  Its confidence is the share of reads that were readable -- a count,
never a feeling.  A judge signs `pass` or, at a terminal rung, `flagged`,
and never `fault`: a fault is the ladder's work, not a file for the next step
to refuse on.  The owner's own hand writes the same files it always did; the
signature fields below are added only when a judge holds the pen.
"""
from __future__ import annotations

from pydantic import BaseModel, Field

OWNER = "owner"
TERMINALS = ("keep_best", "still", "flag", "defer")


class Fault(BaseModel):
    kind: str            # "clones" | "lettering" | "hat" | "identity" | "pass_through" | "story" | "unread" | ...
    where: str           # "shot_07" | "T07" | "00:45.0" | "refs/sheets/x.png"
    evidence: dict = Field(default_factory=dict)   # {"cosine": 0.81, "wall": 0.75, "frames": [12, 40]}
    severity: str = "normal"   # "high" on a dialogue / turn / button shot at a terminal rung
    note: str = ""


class Verdict(BaseModel):
    judge: str
    version: str
    passed: bool
    faults: list[Fault] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)      # share of reads that were readable
    reads: int = 0
    terminal: str = ""   # "" | "keep_best" | "still" | "flag" | "defer"
    signed_at: str = ""

    @property
    def signer(self) -> str:
        return signer(self.judge, self.version)

    def summary(self) -> str:
        return summary(self)


def signer(judge: str, version: str) -> str:
    """`judge:<name>@<version>` -- distinguishable from the owner in every ledger."""
    return f"judge:{judge}@{version}"


def confidence(readable: int, reads: int) -> float:
    """The share of reads that were readable; no reads is no confidence."""
    if readable > reads or readable < 0:
        raise ValueError(f"{readable} readable of {reads} reads is not a share")
    return readable / reads if reads else 0.0


def summary(v: Verdict) -> str:
    """The non-empty note the signers insist on: what was read, or every fault
    by kind and place, and the rung that ended the climb."""
    if v.passed:
        text = f"no fault named in {v.reads} read(s)"
    else:
        text = "; ".join(fault_line(f) for f in v.faults) or "faulted with no fault named"
    return f"{text} -> {v.terminal}" if v.terminal else text


def fault_line(f: Fault) -> str:
    """`kind at where`, and the note when the judge wrote one: a learning that
    says 'battery at plan' five times teaches nothing."""
    return f"{f.kind} at {f.where}: {f.note}" if f.note else f"{f.kind} at {f.where}"


def word(v: Verdict) -> str:
    """The verdict word a judge may sign: pass, or flagged at a terminal rung."""
    if v.passed:
        return "pass"
    if v.terminal:
        return "flagged"
    raise SystemExit("a judge signs a pass or a flag; a fault climbs the ladder")


def signature(signed_by: str = OWNER, faults: list[dict] | None = None, **more) -> dict:
    """The fields a judge's signature adds to a verdict file.  Nothing for the
    owner's own hand, so the file a person signs is the file it always was."""
    if signed_by == OWNER and not faults and not any(more.values()):
        return {}
    return {"signed_by": signed_by, "faults": list(faults or []), **more}
