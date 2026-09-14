#!/usr/bin/env python
"""G5 THE MASTER GATE: measure the delivered episode, never the intention.

    uv run python scripts/episode/qc.py <codex_id> <episode>

Read off `master.mp4`: it runs the planned length plus the chip; it sits at the
platform loudness; every cut the plan asked for is in the picture; every line
can be HEARD on the master -- Whisper reads each line's window of the final mix
back, because a line levelled correctly on its own can still be lost in the sum
(08-assemble names this failure); and the EDIT IS THE TAKES, frame for frame,
at the frames the plan names (studio.edit_gate).

Two roll-ups ride along so the iteration log names what the earlier rungs
caught: the take gate's verdicts (G5.7) and the sheet gate's, with what each
setup cost (G5.8).  Neither fails the master -- by the time a master exists the
GPU time and the money are spent; the cut still needs a picture.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from studio import edit_gate, episode_home, episode_seq_board as sq, voice_qc, youtube_publish as yp
from studio.episode_spec import Episode
from studio.trailer_assemble import clip_seconds, integrated, true_peak

LUFS_BAND = (-15.5, -12.5)
TP_CEILING = -1.0
CUT_TOLERANCE = 0.12
SCENE_THRESHOLD = 0.1
MAX_ERROR_RATE = voice_qc.MAX_ERROR_RATE
PTS = re.compile(r"pts_time:\s*([0-9.]+)")


def planned_cuts(placed: dict) -> list[float]:
    return [shot["t_start"] for shot in placed["shots"][1:]]


def seen_cuts(video: Path, threshold: float = SCENE_THRESHOLD) -> list[float]:
    result = subprocess.run(
        ["ffmpeg", "-i", str(video), "-vf", f"select='gt(scene,{threshold})',showinfo",
         "-f", "null", "-"], capture_output=True, text=True, errors="replace")
    return [round(float(m), 3) for m in PTS.findall(result.stderr)]


def missing_cuts(planned: list[float], seen: list[float], tol: float = CUT_TOLERANCE) -> list[float]:
    """Planned cuts with no detected cut within the tolerance."""
    return [cut for cut in planned if not any(abs(cut - s) <= tol for s in seen)]


def window(master: Path, at: float, seconds: float, out: Path) -> Path:
    """One line's stretch of the master's audio, mono 24 kHz, for the ear."""
    start, span = max(0.0, at - 0.2), seconds + 0.5
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{start:.3f}", "-t", f"{span:.3f}",
                    "-i", str(master), "-vn", "-ac", "1", "-ar", "24000", str(out)], check=True)
    return out


def heard_on_master(master: Path, lines: list[dict], work: Path, listen) -> list[dict]:
    out = []
    for line in lines:
        clip = window(master, line["at"], line["seconds"], work / f"qc_l{line['index']:02d}.wav")
        heard = listen(clip)
        rate = voice_qc.error_rate(heard, line["text"])
        out.append({"index": line["index"], "heard": heard, "error_rate": round(rate, 3),
                    "passed": rate <= MAX_ERROR_RATE})
    return out


def longest_gap(lines: list[dict], until: float) -> float:
    """The longest hole in speech, from the placed lines' measured windows."""
    ordered = sorted(lines, key=lambda line: line["at"])
    gaps, end = [], ordered[0]["at"] if ordered else 0.0
    for line in ordered:
        gaps.append(line["at"] - end)
        end = max(end, line["at"] + line["seconds"])
    gaps.append(until - end)
    return round(max(gaps), 2) if gaps else until


def internal_cuts(placed: dict, records: list[dict]) -> list[float]:
    """Cuts that fall INSIDE a take-run (engine r2v): the model makes them,
    the edit does not, so a soft one is reported, never failed."""
    by = {s["index"]: s for s in placed["shots"]}
    soft = [by[i]["t_start"] for r in records for i in (r.get("shots") or [])[1:]]
    soft += [c for r in records for i in (r.get("shots") or []) for c in by[i].get("cuts", [])]
    return soft


def takes_rollup(take_dir: Path) -> dict:
    """G5.7 -- what the take gate said, over every take that has been judged.  A take
    whose retake budget is spent is named and printed red; it does not fail the
    master, because the cut still needs a picture (owner's call)."""
    out = {"pass": 0, "of": 0, "fail": [], "budget_spent": [], "worst": None}
    for path in sorted(take_dir.glob("T??.dq.json")):
        row, take = json.loads(path.read_text(encoding="utf-8")), path.name.split(".")[0]
        out["of"] += 1
        out["pass"] += bool(row.get("passed"))
        if not row.get("passed"):
            out["fail"].append(take)
        if row.get("budget_spent"):
            out["budget_spent"].append(take)
        if out["worst"] is None or row.get("score", 100.0) < out["worst"][1]:
            out["worst"] = (take, row.get("score", 100.0))
    return out


def sheet_spend(book: Path) -> dict[str, float]:
    """USD per setup from the book's own ledger: every `storyboard seq_<setup>_N` row."""
    path = Path(book) / "spend.jsonl"
    if not path.exists():
        return {}
    out: dict[str, float] = {}
    for text in path.read_text(encoding="utf-8").splitlines():
        purpose = json.loads(text).get("purpose", "") if text.strip() else ""
        if "seq_" in purpose:
            setup = purpose.split("seq_", 1)[1].rsplit("_", 1)[0]
            out[setup] = round(out.get(setup, 0.0) + json.loads(text)["usd_estimate"], 2)
    return out


def sheets_rollup(boards: Path, book: Path) -> list[dict]:
    """G5.8 -- per setup: did the cell gate pass, how many STRICT redraws it took,
    which pairs were alike, and what the setup cost."""
    spend = sheet_spend(book)
    rows = []
    for path in sorted(Path(sq.sheets_in(boards)).glob("seq_*.dq.json")):
        d = json.loads(path.read_text(encoding="utf-8"))
        sheets = d.get("sheets", [])
        rows.append({"setup": d.get("setup", path.stem.split(".")[0][4:]), "passed": d.get("passed"),
                     "sheets": len(sheets), "strict_draws": sum(1 for s in sheets if s.get("strict")),
                     "duplicate_pairs": [p for s in sheets for p in s.get("duplicates", [])],
                     "usd": spend.get(d.get("setup", ""), 0.0)})
    return rows


def card_path(book: Path, number: int) -> Path | None:
    """The title card the tail is measured against, if one was rendered."""
    for path in (book / "title" / f"ep{number:02d}.mp4", book / "title" / "title.mp4"):
        if path.exists():
            return path
    return None


def cut_json(work: Path) -> dict | None:
    """The manifest `assemble.py` writes at cut time; provenance needs it (G5.6)."""
    path = work / "cut.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def edit_report(master: Path, placed: dict, records: list[dict], book: Path, number: int,
                work: Path) -> dict:
    """G5.1-5.6 -- the edit gate, or an honest 'not measured' when a take is gone."""
    missing = [r["rel_path"] for r in records if not (book / r["rel_path"]).exists()]
    if missing:
        return {"ok": True, "measured": False, "note": f"not measured: {len(missing)} take files missing"}
    out = edit_gate.edit_integrity(master, placed, records, book, card_path(book, number), cut_json(work))
    return out | {"measured": True}


def verdict(report: dict) -> bool:
    """Loudness, the planned cuts, every line heard, and the edit being the takes.
    The take and sheet roll-ups are printed, never failed on."""
    hard = [c for c in report["missing_cuts"] if c not in report.get("internal_cuts", [])]
    return (report["lufs_ok"] and report["tp_ok"] and not hard
            and all(row["passed"] for row in report["lines"])
            and report.get("edit", {}).get("ok", True))


def main(book_id: str, number: int, engine: str = "i2v") -> None:
    book = episode_home.book_dir(book_id)
    episode = episode_home.load_plan(book, number)
    master = episode_home.master_path(book, number, engine)
    work = episode_home.work_dir(book, number, engine)
    placed = episode_home.read_json(episode_home.home(book, number) / "placed.json")
    lines = placed["lines"]
    lufs, tp = integrated(master), true_peak(master)
    seen = seen_cuts(master)
    take_dir = episode_home.takes_dir(book, number, engine)
    records = episode_home.read_json(take_dir / "shots.json")
    report = {
        "master": episode_home.relative(book, master),
        # WHICH BYTES THIS REPORT MEASURED.  Without it a report can outlive the
        # cut it describes: ep03's qc measured f5ddd2a3 at 19:49, the master was
        # re-cut as f8bf7814 at 20:02, and the publish ladder read the stale
        # report. `youtube_publish.refusals` compares this and cannot be
        # overridden, because it is a fact and not a judgement.
        "sha8": yp.sha8(master),
        "seconds": clip_seconds(master), "planned_seconds": placed["duration_s"],
        "title_card": (book / "title" / f"ep{number:02d}.mp4").exists() or (book / "title" / "title.mp4").exists(),
        "lufs": lufs, "lufs_ok": LUFS_BAND[0] <= lufs <= LUFS_BAND[1],
        "true_peak": tp, "tp_ok": tp <= TP_CEILING,
        "planned_cuts": planned_cuts(placed), "seen_cuts": seen,
        "missing_cuts": missing_cuts(planned_cuts(placed), seen),
        "internal_cuts": internal_cuts(placed, records),
        "lines": heard_on_master(master, lines, work, voice_qc.any_transcriber()),
        # THE PICTURE'S END, not the last line's START.  With the start, the final
        # `until - end` is negative and the tail is thrown away by `max()`:
        # ep03 reported 2.03 s while a 3.26 s run-out sat at the end of the
        # episode with the bed at -45.6 LUFS.
        "longest_gap_s": longest_gap(lines, placed["duration_s"]),
        "speech_s": round(sum(line["seconds"] for line in lines), 1),
    }
    report["edit"] = edit_report(master, placed, records, book, number, work)
    report["takes"] = takes_rollup(take_dir)
    report["sheets"] = sheets_rollup(episode_home.boards_dir(book, number), book)
    report["passed"] = verdict(report)
    report_path = episode_home.home(book, number) / ("qc.json" if engine == "i2v" else f"qc_{engine}.json")
    episode_home.write_json(report_path, report)
    said = sum(row["passed"] for row in report["lines"])
    print(f"{report['seconds']:.2f}s | {lufs:.1f} LUFS {tp:.1f} dBTP | "
          f"cuts missing {len(report['missing_cuts'])}/{len(report['planned_cuts'])} "
          f"(soft inside take-runs: {len([c for c in report['missing_cuts'] if c in report['internal_cuts']])}) | "
          f"lines heard {said}/{len(report['lines'])} | speech {report['speech_s']}s, "
          f"longest gap {report['longest_gap_s']}s | {'PASS' if report['passed'] else 'FAIL'}")
    edit = report["edit"]
    print(f"edit: {'OK' if edit['ok'] else 'FAIL'}"
          + (f" ({edit.get('note')})" if not edit.get("measured") else
             f" | segments off {sum(not s['ok'] for s in edit['segments'])}/{len(edit['segments'])}"
             f" | cuts off {sum(not c['exact'] for c in edit['cuts'])}/{len(edit['cuts'])}"
             f" | pts holes {len(edit['timestamp_holes'])} | tail {edit['tail']['master_frames']}"
             f"/{edit['tail']['expected_frames']} | provenance "
             f"{edit['stale_takes'] if edit['provenance']['measured'] else 'not measured (no work/cut.json)'}"))
    takes = report["takes"]
    print(f"takes: {takes['pass']}/{takes['of']} pass | fail {takes['fail']} | "
          f"budget spent {takes['budget_spent']} | worst {takes['worst']}")
    for sheet in report["sheets"]:
        print(f"sheet {sheet['setup']}: {'PASS' if sheet['passed'] else 'FAIL'} | "
              f"{sheet['sheets']} draw(s), {sheet['strict_draws']} STRICT | alike "
              f"{sheet['duplicate_pairs']} | ${sheet['usd']:.2f}")
    print(f"-> {report_path}")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    main(args[0], int(args[1]) if len(args) > 1 else 1, episode_home.engine_arg(sys.argv))
