"""The eye instrument's calibration gate (2026-10-21_ep02_proof DESIGN 4.2, R6).

`face_eye`'s cel score agreed with the eye on 4 of 15 on the face debate bench.  A row measured
with an instrument that fails calibration is not weak evidence; it is no evidence.  So an eye
instrument is CALIBRATED only when its agreement with the OWNER's labels has a Wilson 95 % lower
bound of at least 0.70 over at least 30 labelled faces (26 of 30 passes at 0.703, 25 of 30 fails at
0.664).  Below that every eye_cel row it wrote is stamped INSTRUMENT FAILED, and Q1-Q3 are REAL-RUN.

Ground truth is the owner's labels and nothing else: the `owner` field of a
`review/face_labels_<sha8>.json` file (written by the owner from the face strip).  The production
EYE judge's `eye` field is a VLM read with no measured agreement with the owner; it may be MEASURED
here as a second candidate (`eye_judge_reads`), never used as a label (calibrating one instrument on
another uncalibrated one is circular; DESIGN 8, R6).

The cel candidate's word is its own zero line, pre-registered and never tuned on labels:
face_eye says "0 is no drawn eye", so a score above 0 reads `good`."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Callable, Iterable

from studio import intervals

MIN_N = 30
MIN_LOWER = 0.70
Z95 = 1.959964
CALIBRATED = "CALIBRATED"
FAILED = "INSTRUMENT FAILED"
LABELS = ("good", "bad")
LABEL_FILE = re.compile(r"^face_labels_[0-9a-f]{8}\.json$")
CEL_ZERO = 0.0
"""face_eye.eye_score's own line: 0 is no drawn eye (pre-registered, never fitted to labels)."""
KINDS = ("quality", "mechanism", "compliance")


def wilson_lower(k: int, n: int, z: float = Z95) -> float:
    """The Wilson score interval's lower bound for k agreements in n (studio.intervals); 0 when nothing was counted."""
    return intervals.wilson(k, n, z)[0] if n > 0 else 0.0


def gate(agree: int, n: int) -> dict:
    """The gate's verdict on one candidate: its counts, its lower bound, CALIBRATED or FAILED."""
    lower = round(wilson_lower(agree, n), 3)
    passed = n >= MIN_N and lower >= MIN_LOWER
    return {"agree": agree, "n": n, "lower": lower, "passed": passed, "state": CALIBRATED if passed else FAILED,
            "min_n": MIN_N, "min_lower": MIN_LOWER}


def owner_labels(doc: dict) -> dict[str, str]:
    """crop -> the owner's word; a blank or an off-vocabulary `owner` is no label.  No other field
    (the EYE judge's `eye`, a model's guess) is ever read here."""
    vocab = tuple(doc.get("labels") or LABELS)
    return {c["crop"]: c["owner"].strip() for c in doc.get("crops") or []
            if isinstance(c.get("owner"), str) and c["owner"].strip() in vocab}


def read_labels(paths: Iterable[Path]) -> list[tuple[Path, dict]]:
    """Each named owner label file and its doc; anything not a review/face_labels_<sha8>.json is refused."""
    out = []
    for path in map(Path, paths):
        if not LABEL_FILE.match(path.name) or path.parent.name != "review":
            raise ValueError(f"{path}: labels are read only from review/face_labels_<sha8>.json (the owner's file)")
        out.append((path, json.loads(path.read_text(encoding="utf-8"))))
    return out


def eye_judge_reads(doc: dict, _root: Path | None = None) -> dict[str, str]:
    """The production EYE judge as a CANDIDATE: `clear` reads good, `soft`/`warped` bad, `none` unread."""
    words = {"clear": "good", "soft": "bad", "warped": "bad"}
    return {c["crop"]: words[c["eye"]] for c in doc.get("crops") or [] if c.get("eye") in words}


def cel_word(score: float | None) -> str | None:
    """The cel candidate's word for one score: above its zero line good, at it bad, unread None."""
    if score is None:
        return None
    return "good" if score > CEL_ZERO else "bad"


def cel_reads(doc: dict, root: Path, score: Callable[[Path], float | None]) -> dict[str, str]:
    """The cel candidate over every crop of the strip (`score` reads one crop picture)."""
    out = {}
    for c in doc.get("crops") or []:
        if (word := cel_word(score(Path(root) / c["crop"]))) is not None:
            out[c["crop"]] = word
    return out


def agreement(labels: dict[str, str], reads: dict[str, str]) -> tuple[int, int]:
    """(agreements, crops both labelled and read)."""
    both = [k for k in labels if k in reads]
    return sum(labels[k] == reads[k] for k in both), len(both)


def calibrate(paths: Iterable[Path], candidates: dict[str, Callable]) -> dict[str, dict]:
    """candidate -> its gate over every named owner label file (a candidate reads (doc, folder))."""
    counts = {name: [0, 0] for name in candidates}
    for path, doc in read_labels(paths):
        labels = owner_labels(doc)
        for name, reader in candidates.items():
            k, n = agreement(labels, reader(doc, path.parent))
            counts[name][0] += k
            counts[name][1] += n
    return {name: gate(k, n) for name, (k, n) in counts.items()}


def stamp(rows: list[dict], verdict: dict) -> list[dict]:
    """Every eye_cel row carries the instrument's state; the numbers stay, their standing does not."""
    return [{**r, "instrument_state": verdict["state"]} for r in rows]


def proof_row(check: str, question: str, passed: bool, n_points: int, n_distinct: int, evidence: list[str],
              match_classes: list | dict, instrument: str, instrument_state: str, kind: str) -> dict:
    """One row of the proof report (DESIGN 5): every suite writes these and nothing else."""
    if kind not in KINDS:
        raise ValueError(f"kind {kind!r} is not one of {KINDS}")
    return {"check": check, "question": question, "passed": bool(passed), "n_points": int(n_points),
            "n_distinct": int(n_distinct), "evidence": [str(e) for e in evidence], "match_classes": match_classes,
            "instrument": instrument, "instrument_state": instrument_state, "kind": kind}
