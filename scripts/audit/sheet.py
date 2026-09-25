#!/usr/bin/env python
"""The audit sheet: every flagged artefact of a unit on one page, the judge's
numbers beside the wall, and three passed artefacts per gate for the owner's eye.

    uv run python scripts/audit/sheet.py <codex_id> [<unit>]

Writes library/<book>/audit/<unit>.html (and index.html) from the rows every
terminal rung appends to library/<book>/audit/rows.jsonl.  Each flagged
artefact is shown with its faults -- kind, where, every number the judge
measured, the wall it was measured against -- beside the unit's contact sheet,
its take strips and its master.  Under them, a random sample of three PASSED
artefacts per gate, seeded by the unit's sha8 so the same page shows the same
three tomorrow: a judge that approves slop consistently is found here, not in
its own numbers.

NO STEP READS THIS PAGE OR ITS ROWS (a test greps).  The owner does, whenever
he likes, and writes what he finds with scripts/audit/note.py.  Free: reads
json, writes html.  The page style is the dossier's.
"""
from __future__ import annotations

import hashlib
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.episode.dossier import CSS, esc  # noqa: E402
from studio import audit_rows, episode_home  # noqa: E402
from studio.audit_rows import AuditRow  # noqa: E402

SAMPLE = 3
GATE_GLOBS = {
    "EYE_PANELS": "episodes/{unit}/storyboard/shot_*.png",
    "EYE_TAKES": "episodes/{unit}/takes/r2v/T??.mp4",
    "PLAN": "episodes/{unit}/plan.json",
    "MASTER": "episodes/{unit}/cut/master*.mp4",
    "LOOK": "refs/**/*.png",
}
"""Where each gate's artefacts live, relative to the book; the sample is drawn
from these minus the ones a row flagged."""
PICTURES = (("the contact sheet", "episodes/{unit}/storyboard/contact.png"),
            ("the master's contact sheet", "episodes/{unit}/review/contact_*.png"),
            ("the strips", "episodes/{unit}/reports/strip_*.png"),
            ("the master", "episodes/{unit}/cut/master_r2v.mp4"),
            ("the master", "episodes/{unit}/cut/master.mp4"))


# ---- the rows ---------------------------------------------------------------------------

def unit_of(arg: str) -> str:
    """`4`, `04` and `ep04` are one unit: the runner passes the number."""
    return f"ep{int(arg):02d}" if arg.isdigit() else arg


def units_of(rows: list[AuditRow]) -> list[str]:
    return sorted({row.unit for row in rows})


def rows_for(rows: list[AuditRow], unit: str) -> list[AuditRow]:
    return [row for row in rows if row.unit == unit]


def unit_seed(unit: str, rows: list[AuditRow]) -> str:
    """The sha8 the sample is seeded by: the master's, when a MASTER row
    carries one, else the sha8 of the unit's name."""
    for row in rows:
        if row.gate == "MASTER" and row.sha8:
            return row.sha8
    return hashlib.sha256(unit.encode("utf-8")).hexdigest()[:8]


# ---- one flagged artefact --------------------------------------------------------------

def href(artefact: str) -> str:
    """The page sits in audit/; every artefact is one folder up."""
    return "../" + artefact.lstrip("/")


def picture(artefact: str, sha8: str = "") -> str:
    """The artefact as a picture: a png, a video, or a rubric with its contact sheet."""
    low = artefact.lower()
    if low.endswith(".png"):
        return f"<img src='{esc(href(artefact))}' alt='{esc(artefact)}'>"
    if low.endswith(".mp4"):
        return f"<video controls preload=metadata src='{esc(href(artefact))}'></video>"
    if "review/eye_" in low and sha8:
        contact = artefact.rsplit("/", 1)[0] + f"/contact_{sha8}.png"
        return f"<img src='{esc(href(contact))}' alt='{esc(contact)}'>"
    return ""


def evidence_html(evidence: dict) -> str:
    """Every number the judge measured, the wall in bold beside them."""
    if not evidence:
        return "<span class=tag>no evidence</span>"
    bits = []
    for key, value in evidence.items():
        cell = f"<b>{esc(key)}: {esc(value)}</b>" if key == "wall" else f"{esc(key)}: {esc(value)}"
        bits.append(f"<span class=tag>{cell}</span>")
    return " ".join(bits)


def fault_table(faults: list[dict]) -> str:
    rows = "".join(
        f"<tr><td class=bad>{esc(f.get('kind'))}</td><td>{esc(f.get('where'))}</td>"
        f"<td>{evidence_html(f.get('evidence') or {})}</td>"
        f"<td>{esc(f.get('severity', 'normal'))}</td><td>{esc(f.get('note', ''))}</td></tr>"
        for f in faults)
    return ("<table><tr><th>fault</th><th>where</th><th>measured, beside the wall</th>"
            f"<th>severity</th><th>note</th></tr>{rows}</table>")


def flag_card(row: AuditRow) -> str:
    return (f"<div class=card><h3>{esc(row.gate)} <span class=tag>{esc(row.judge)}</span>"
            f"<span class=tag>terminal {esc(row.terminal)}</span><span class=tag>{esc(row.ts)}</span></h3>"
            f"<div class=row><div class=pic>{picture(row.artefact, row.sha8)}</div><div class=txt>"
            f"<dl><dt>artefact</dt><dd><a href='{esc(href(row.artefact))}'>{esc(row.artefact)}</a>"
            f"{' sha8 ' + esc(row.sha8) if row.sha8 else ''}</dd></dl>"
            f"{fault_table(row.faults)}</div></div></div>")


def flagged(rows: list[AuditRow]) -> str:
    out = [f"<h2>Flagged <small>{len(rows)} terminal rung(s); every fault with its numbers</small></h2>"]
    out += [flag_card(row) for row in rows] or ["<div class=card>nothing was flagged</div>"]
    return "".join(out)


# ---- the unit's pictures ----------------------------------------------------------------

def found(book: Path, pattern: str) -> list[str]:
    """Relative posix paths under the book matching one glob, sorted."""
    return sorted(p.relative_to(book).as_posix() for p in Path(book).glob(pattern) if p.is_file())


def gallery(title: str, paths: list[str]) -> str:
    if not paths:
        return ""
    figs = "".join(f"<figure>{picture(p)}<figcaption><a href='{esc(href(p))}'>{esc(p)}</a></figcaption></figure>"
                   for p in paths)
    return f"<h3>{esc(title)}</h3><div class=cells>{figs}</div>"


def pictures_of(book: Path, unit: str) -> str:
    out = ["<h2>The unit <small>the contact sheet, the strips, the master</small></h2><div class=card>"]
    out += [gallery(title, found(book, pattern.format(unit=unit))) for title, pattern in PICTURES]
    return "".join(out) + "</div>"


# ---- the seeded sample of passed artefacts ---------------------------------------------

def flagged_names(rows: list[AuditRow]) -> set[str]:
    """Every name a row points at: its artefact's path and stem, each fault's `where`."""
    names = set()
    for row in rows:
        names.add(row.artefact)
        names.add(Path(row.artefact).stem)
        names.update(str(f.get("where", "")) for f in row.faults)
    return names


def passed_pool(book: Path, unit: str, gate: str, rows: list[AuditRow]) -> list[str]:
    """This gate's artefacts on disk that no row flagged."""
    names = flagged_names(rows)
    return [p for p in found(book, GATE_GLOBS[gate].format(unit=unit))
            if p not in names and Path(p).stem not in names]


def sample(book: Path, unit: str, rows: list[AuditRow], seed: str, n: int = SAMPLE) -> dict[str, list[str]]:
    """Three passed artefacts per gate, the same three for the same seed."""
    out = {}
    for gate in GATE_GLOBS:
        pool = passed_pool(book, unit, gate, rows)
        if pool:
            out[gate] = sorted(random.Random(f"{seed}:{gate}").sample(pool, min(n, len(pool))))
    return out


def sampled(picked: dict[str, list[str]], seed: str) -> str:
    out = [f"<h2>Passed, sampled <small>{SAMPLE} per gate, seeded by {esc(seed)}</small></h2><div class=card>"]
    out += [gallery(gate, paths) for gate, paths in picked.items()] or ["nothing passed on disk"]
    return "".join(out) + "</div>"


# ---- the pages ---------------------------------------------------------------------------

def page(book: Path, unit: str, rows: list[AuditRow]) -> str:
    seed = unit_seed(unit, rows)
    return (f"<!doctype html><meta charset=utf-8>"
            f"<meta name=viewport content='width=device-width,initial-scale=1'>"
            f"<title>{esc(book.name)} {esc(unit)} audit</title><style>{CSS}</style>"
            f"<header><h1>{esc(unit)} audit</h1><div class=sub>{esc(book.name)} &middot; "
            f"<a href='index.html' style='color:#b9b2a6'>index</a></div>"
            f"<div class=num><b>{len(rows)}</b> flagged &middot; seed <b>{esc(seed)}</b></div></header>"
            f"<main>{flagged(rows)}{pictures_of(book, unit)}{sampled(sample(book, unit, rows, seed), seed)}</main>")


def index_page(book: Path, rows: list[AuditRow]) -> str:
    items = "".join(f"<tr><td><a href='{esc(u)}.html'>{esc(u)}</a></td>"
                    f"<td class=n>{len(rows_for(rows, u))}</td></tr>" for u in units_of(rows))
    return (f"<!doctype html><meta charset=utf-8><title>{esc(book.name)} audit</title><style>{CSS}</style>"
            f"<header><h1>{esc(book.name)} audit</h1></header><main><div class=card>"
            f"<table><tr><th>unit</th><th>flagged</th></tr>{items}</table></div></main>")


def write(book: Path, unit: str) -> Path:
    rows = audit_rows.load(book)
    out = Path(book) / "audit" / f"{unit}.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page(Path(book), unit, rows_for(rows, unit)), encoding="utf-8")
    index = out.parent / "index.html"
    index.write_text(index_page(Path(book), rows), encoding="utf-8")
    return out


def main(argv: list[str]) -> int:
    args = [a for a in argv[1:] if not a.startswith("--")]
    if not args:
        raise SystemExit("usage: sheet.py <codex_id> [<unit>]")
    book = episode_home.book_dir(args[0])
    units = [unit_of(args[1])] if len(args) > 1 else units_of(audit_rows.load(book))
    for unit in units:
        print(write(book, unit))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
