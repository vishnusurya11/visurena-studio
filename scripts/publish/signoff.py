#!/usr/bin/env python
"""review/director_signoff.md, rendered from measures and nothing else.

    uv run python scripts/publish/signoff.py <codex_id> <n> [--engine=r2v]

The sign-off used to be typed, and a typed sign-off can claim a watch nobody
took -- the family fault since 2026-09-16, when `--watched` was satisfied by a
six-frame glance.  This module has NO free-text parameter: every sentence is
a template slot filled from a parsed number or verdict string -- the
judge-filled eye rubric, the QC report that measured THESE bytes, every
take's dq/content verdict and roll count off the attempts room, the ladder's
terminals out of learnings.jsonl, the voice check, and the wardrobe report
when one was measured.

G-SIGNOFF-MEASURED, HARD: write() raises SystemExit listing every missing or
stale input before a byte reaches disk, so an unmeasured claim is
unrepresentable.  The output clears studio/publish_lock.signoff_stops by
construction (the sha8 named in the header, the four SECTIONS each written);
the lock itself is UNCHANGED -- only the file that satisfies it stops being
typed.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.episode import eye_review  # noqa: E402
from studio import episode_home, judged, publish_lock  # noqa: E402
from studio import youtube_publish as yp  # noqa: E402
from studio.learnings import load  # noqa: E402

ENGINE = "r2v"
SIGNER = "judge:signoff@v1"


def report_pair(home: Path, engine: str) -> tuple[Path, Path]:
    """(master, qc report) where the publish ladder agrees they are."""
    for name, master, qc in yp.MASTERS:
        if name == engine:
            return Path(home) / "cut" / master, Path(home) / qc
    raise SystemExit(f"unknown engine {engine!r}; one of {[n for n, _m, _q in yp.MASTERS]}")


def missing(home: Path, engine: str, sha8: str) -> list[str]:
    """Every absent or stale input -- ALL of them, before anything is written."""
    out = []
    eye = eye_review.rubric_path(home, sha8)
    if not eye.exists():
        out.append(f"{eye.name} is missing: no eye rubric describes this cut")
    else:
        out += eye_review.refusals(episode_home.read_json(eye), sha8, eye)
    _master, qc = report_pair(home, engine)
    if not qc.exists():
        out.append(f"{qc.name} is missing: nothing measured this cut")
    elif episode_home.read_json(qc).get("sha8") != sha8:
        out.append(f"{qc.name} measured {episode_home.read_json(qc).get('sha8')}, "
                   f"this cut is {sha8}")
    out += [f"take {name} has no current dq/content verdict" for name in
            judged.unjudged_takes(episode_home.takes_under(home, engine), kinds=("dq", "content"))]
    if not (Path(home) / "learnings.jsonl").exists():
        out.append("learnings.jsonl is missing: the ladder's history is unmeasured")
    return out


def take_rows(folder: Path) -> list[dict]:
    """Per take: the dq score, both verdicts and how many rolls it took."""
    out = []
    for entry in episode_home.read_json(folder / "shots.json"):
        name = f"T{entry['index']:02d}"
        dq = episode_home.read_json(folder / f"{name}.dq.json")
        content = episode_home.read_json(folder / f"{name}.content.json")
        out.append({"name": name, "score": dq.get("score"), "dq_passed": bool(dq.get("passed")),
                    "content_passed": bool(content.get("passed")),
                    "faults": content.get("faults") or [],
                    "rolls": len(episode_home.attempts_of(folder, entry["index"]))})
    return out


def wardrobe_rows(home: Path, sha8: str) -> list[dict] | None:
    """The measured drift rows, or None when no wardrobe check ran (advisory)."""
    path = Path(home) / "review" / f"wardrobe_{sha8}.json"
    if not path.exists():
        return None
    said = episode_home.read_json(path)
    return said if isinstance(said, list) else said.get("rows", [])


def gather(home: Path, engine: str, sha8: str) -> dict:
    """Every measured input, or the G-SIGNOFF-MEASURED refusal listing all gaps."""
    if gaps := missing(home, engine, sha8):
        raise SystemExit("REFUSED, the sign-off would claim the unmeasured:\n  "
                         + "\n  ".join(gaps))
    _master, qc = report_pair(home, engine)
    speakers = Path(home) / "review" / "speaker_check.json"
    return {"sha8": sha8, "engine": engine, "qc_name": qc.name,
            "eye": episode_home.read_json(eye_review.rubric_path(home, sha8)),
            "qc": episode_home.read_json(qc),
            "takes": take_rows(episode_home.takes_under(home, engine)),
            "terminals": publish_lock.last_by_gate(load(Path(home) / "learnings.jsonl")),
            "speakers": episode_home.read_json(speakers) if speakers.exists() else {},
            "wardrobe": wardrobe_rows(home, sha8)}


# ---- the four sections, every slot a parsed value ---------------------------------

def watched_lines(m: dict) -> list[str]:
    """The eye rubric, field by field, the judge's numbers beside each answer."""
    eye = m["eye"]
    out = [f"{eye.get('frames')} frames every {eye.get('frames_every_s')} s of "
           f"{eye.get('master')}, read by {eye.get('reviewed_by')}."]
    for field, cell in (eye.get("rubric") or {}).items():
        said = ", ".join(f"{k} {v}" for k, v in (cell.get("evidence") or {}).items()
                         if not isinstance(v, (dict, list)))
        out.append(f"- {field}: {cell.get('answer')}" + (f" ({said})" if said else ""))
    return out


def strips_lines(m: dict) -> list[str]:
    """Every take's verdict pair and roll count; every ladder terminal beside."""
    out = []
    for t in m["takes"]:
        line = (f"- {t['name']}: dq {t['score']} {'pass' if t['dq_passed'] else 'FAIL'}, "
                f"content {'pass' if t['content_passed'] else 'FAIL'}, {t['rolls']} roll(s)")
        if t["faults"]:
            line += " -- " + "; ".join(str(f) for f in t["faults"])[:120]
        out.append(line)
    out += [f"- {gate} ended {row.action} (terminal): {row.note}"
            for gate, row in m["terminals"].items() if row.terminal]
    return out


def coverage_lines(m: dict) -> list[str]:
    """The QC report's numbers and the voice check's worst pairs."""
    qc = m["qc"]
    out = [f"{m['qc_name']}: passed={qc.get('passed')}; {qc.get('seconds')} s cut of "
           f"{qc.get('planned_seconds')} s planned; {qc.get('lufs')} LUFS, true peak "
           f"{qc.get('true_peak')}; longest silent gap {qc.get('longest_gap_s')} s."]
    for who, row in m["speakers"].items():
        if isinstance(row, dict) and "ok" in row:
            out.append(f"- {who}: one voice {row.get('ok')} (worst pair {row.get('worst')})")
    return out


def flags_lines(m: dict) -> list[str]:
    """Every open flag with its evidence: judge n's, terminals, wardrobe drift."""
    out = []
    for field, cell in eye_review.flags(m["eye"]).items():
        said = ", ".join(f"{k} {v}" for k, v in cell["evidence"].items()
                         if not isinstance(v, (dict, list)))
        out.append(f"- eye {field}: {cell['flagged_by']}" + (f" ({said})" if said else ""))
    out += [f"- {gate} ended {row.action} (terminal): {row.note}"
            for gate, row in m["terminals"].items() if row.terminal]
    for row in m["wardrobe"] or []:
        out.append(f"- wardrobe at {row.get('at')}s: {row.get('character')} expected "
                   f"{', '.join(row.get('expected', []))}; seen {', '.join(row.get('seen', []))}")
    return out or ["- none measured open."]


def signed_line(m: dict) -> str:
    """Who signed and from what: the generator and its inputs, never a person."""
    inputs = [f"eye_{m['sha8']}.json", m["qc_name"],
              f"{len(m['takes'])} dq/content reports", "learnings.jsonl"]
    if m["wardrobe"] is not None:
        inputs.append(f"wardrobe_{m['sha8']}.json")
    return f"Signed: {SIGNER} from {', '.join(inputs)}"


def render(m: dict) -> str:
    """The markdown publish_lock reads: sha8 in the header, the four SECTIONS."""
    lines_by = {"Watched": watched_lines(m), "Take strips": strips_lines(m),
                "Coverage": coverage_lines(m), "Flags": flags_lines(m)}
    parts = [f"# Director sign-off — cut {m['sha8']} ({m['engine']})", "",
             "Generated from measures; no sentence here was typed.", ""]
    for name in publish_lock.SECTIONS:
        parts += [f"## {name}", *lines_by[name], ""]
    parts.append(signed_line(m))
    return "\n".join(parts) + "\n"


def write(home, sha8: str, engine: str = ENGINE) -> Path:
    """The sign-off for THIS cut, or SystemExit naming every unmeasured input."""
    m = gather(Path(home), engine, sha8)
    path = Path(home) / "review" / "director_signoff.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render(m), encoding="utf-8")
    return path


def main(argv: list[str]) -> int:
    args = [a for a in argv[1:] if not a.startswith("--")]
    book = episode_home.book_dir(args[0])
    home = episode_home.home(book, int(args[1]))
    engine = next((a.split("=", 1)[1] for a in argv if a.startswith("--engine=")), "")
    engine, master, _qc = yp.deliverable(home, engine)
    print(write(home, yp.sha8(master), engine))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
