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

from studio.episode_home import episode_arg
from studio import judged
from studio import edit_gate, episode_home, gap_owner, episode_seq_board as sq, voice_qc, youtube_publish as yp
from studio import episode_takes as tk
from studio.episode_spec import Episode
from studio.trailer_assemble import clip_seconds, integrated, true_peak

LUFS_BAND = (-15.5, -12.5)
TP_CEILING = -1.0
CUT_TOLERANCE = 0.12
"""How far an EDIT-MADE cut may sit from its plan. A cut the model makes inside
a take-run is judged at its grid frame instead (`grid_cut`)."""
MAX_GAP_S = 6.0
"""The longest hole in speech a delivered master may carry (ep10 synthesis
B6/F6): Scarlet ep05 4.4 s, ep07 4.5 s, ep09 3.25 s pass; ep10's 11.25 s
wordless tail after the button fails. The plan gate's twin, read off the file.

THE STATED REASON WAS WRONG, and it nearly cost a rewrite.  This docstring
said ep10 failed because of "the bed dying at 166 s into the only voiceless
stretch", which reads as a rule -- a hole is a fault when there is nothing to
HEAR in it -- and invites replacing the wall with a loudness floor.  MEASURED
2026-09-20 on the delivered masters, integrated over each episode's own
longest hole:

    Scarlet ep10  11.25 s  -26.1 LUFS   FAILS
    Scarlet ep07   4.46 s  -28.0 LUFS   ships
    WotW    ep01   5.83 s  -28.5 LUFS   ships
    WotW    ep02   5.50 s  -35.9 LUFS   ships
    WotW    ep03   5.52 s  -31.9 LUFS   ships
    WotW    ep04   5.26 s  -27.4 LUFS   ships
    WotW    ep05   7.05 s  -26.8 LUFS   fails this wall

The failing hole is the LOUDEST of them, and two shipped holes are 5 and 9 dB
quieter than it.  The -45.6 LUFS in the old note was the BED FILE, not the
master, so loudness does not separate the fault from the holds at all.  Any
gate built on that reading would pass ep10 and fail ep02.

What the table does separate is WHERE the hole sits.  Every hole that ships is
between two lines, with picture running through it; ep10's is a run-out after
the last word, at 159.8 s of a 171 s episode.  A held beat and a dead tail are
different objects and this one number folds them together -- `longest_gap`
appends `until - end` and takes the max.  That is a hypothesis with one failing
case behind it, NOT a calibration, so nothing here acts on it yet.

WotW ep05 sits 1.2 s past the longest hold the owner has ever shipped: 7.05 s
of the mast rising out of the pit, on "Something down there put up an eye".
It is reported, not excused.  The wall is not moved to fit a cut of mine."""
FPS = 24
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


def missing_cuts(planned: list[float], seen: list[float], tol: float = CUT_TOLERANCE,
                 proven: list[dict] | None = None, fps: int = 24) -> list[float]:
    """Planned cuts that neither the scene metric saw nor the edit gate proved.

    `seen` is ffmpeg's `select=gt(scene,0.1)`, a content-difference heuristic, and
    two shots of the SAME ROOM at the same lens and the same light score under it
    -- so a real cut reads as one that never happened, and `verdict` hard-fails
    the delivered master for it.

    `proven` is `edit_gate`'s own per-cut answer, which is not a heuristic: the
    frame before the cut IS the previous take's last placed frame and the frame
    at it IS the next take's first, within SAME_FRAME = 4.0 where encoder noise
    measures 0.16-0.59 and another picture 32-63.  A cut it proved exact is
    present whatever the scene metric saw.

    Episode 5 is where this stops being theoretical: five of its six setups are
    the 221B sitting room from five corners, most of them at the same gaslight
    and the same fire."""
    exact = [row["at"] / fps for row in (proven or []) if row.get("exact")]
    return [cut for cut in planned
            if not any(abs(cut - s) <= tol for s in seen)
            and not any(abs(cut - s) <= tol for s in exact)]


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


def internal_pairs(placed: dict, records: list[dict]) -> list[tuple[float, float]]:
    """(cut, start of its take) for every cut INSIDE a take-run (engine r2v):
    the shot boundaries after the run's first, and each shot's own sub-cuts."""
    by = {s["index"]: s for s in placed["shots"]}
    pairs = []
    for r in records:
        shots = r.get("shots") or []
        start = by[shots[0]]["t_start"] if shots else 0.0
        pairs += [(by[i]["t_start"], start) for i in shots[1:]]
        pairs += [(c, start) for i in shots for c in by[i].get("cuts", [])]
    return pairs


def internal_cuts(placed: dict, records: list[dict]) -> list[float]:
    """Cuts that fall INSIDE a take-run: the model makes them, the edit does
    not, so one the picture lacks is reported, never failed."""
    return [cut for cut, _ in internal_pairs(placed, records)]


def grid_cut(planned: float, take_frame: int, seen: list[float], fps: int = FPS,
             tol: float = CUT_TOLERANCE) -> dict:
    """One cut inside a take-run, judged where the model CAN land it.

    The pin is snapped forward to the token grid (`episode_takes.grid_frame`,
    17k + {0,1,5,9,13}) by `takes_r2v.on_grid`, and the model obeys the snapped
    frame.  Episode 10's four internal cuts landed at take frames 85, 77, 145,
    85 against planned 84, 74, 144, 84 -- each exactly its grid frame -- and the
    3-frame snap is 0.125 s, 5 ms past CUT_TOLERANCE, so cut 22 was "missing".
    It is late by three frames and on the grid, which is what this says."""
    grid = tk.grid_frame(take_frame)
    expect = planned + (grid - take_frame) / fps
    near = min(seen, key=lambda s: abs(s - expect), default=None)
    found = near is not None and abs(near - expect) <= tol
    return {"at": planned, "take_frame": take_frame, "grid_frame": grid,
            "seen": near if found else None,
            "late_frames": round((near - planned) * fps) if found else None,
            "on_grid": found, "missing": not found}


def internal_cut_rows(placed: dict, records: list[dict], seen: list[float], fps: int = FPS) -> list[dict]:
    """`grid_cut` for every cut inside a take-run; the take frame is the cut's
    distance from the run's first shot, since take frame 0 IS that shot's start."""
    return [grid_cut(cut, round((cut - start) * fps), seen, fps)
            for cut, start in internal_pairs(placed, records)]


def drop_on_grid(missing: list[float], rows: list[dict]) -> list[float]:
    """A cut found at its grid frame is present; it leaves the missing list."""
    present = {row["at"] for row in rows if row.get("on_grid")}
    return [cut for cut in missing if cut not in present]


def takes_rollup(take_dir: Path) -> dict:
    """G5.7 -- what the take gate said, over every take that has been judged.  A take
    whose retake budget is spent is named and printed red; it does not fail the
    master, because the cut still needs a picture (owner's call)."""
    # THE UNIVERSE IS THE TAKES THE RENDER RECORDED, not the reports on disk:
    # a take nobody judged was simply not counted (audit 2026-09-22, item 6).
    out = {"pass": 0, "of": 0, "fail": [], "budget_spent": [], "worst": None,
           "unjudged": judged.unjudged_takes(take_dir)}
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
        # NOT ok.  This returned `ok: True` and `verdict` read it as a pass --
        # `migrate_layout.repoint`'s own docstring names the fault and then fixed
        # only the records, not the reader.  A gate that could not read the takes
        # has not approved the master.
        return {"ok": False, "measured": False,
                "note": f"not measured: {len(missing)} take files missing"}
    out = edit_gate.edit_integrity(master, placed, records, book, card_path(book, number), cut_json(work),
                                   heads=edit_gate.heads_in(episode_home.home(book, number)))
    return out | {"measured": True}


def verdict(report: dict) -> bool:
    """Loudness, the planned cuts, every line heard, and the edit being the takes.
    The take and sheet roll-ups are printed, never failed on."""
    hard = [c for c in report["missing_cuts"] if c not in report.get("internal_cuts", [])]
    return (report["lufs_ok"] and report["tp_ok"] and not hard
            and report.get("longest_gap_s", 0.0) <= MAX_GAP_S
            and all(row["passed"] for row in report["lines"])
            # AN ABSENT EDIT BLOCK IS NOT A PASS.  `.get("edit", {}).get("ok", True)`
            # made a missing measurement clean twice over.
            and bool(report.get("edit", {}).get("ok", False))
            and bool(report.get("edit", {}).get("measured", False))
            # A TAKE NOBODY JUDGED IS NOT A PASS -- the same rule as the edit
            # block above. A take that FAILED and spent its retake budget still
            # does not fail the master (owner's call): that one was measured.
            and not report.get("takes", {}).get("unjudged"))


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
        "missing_cuts": [],          # filled below, once the edit gate has spoken
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
    # AFTER the edit gate, because a cut it PROVED frame-exact is present whatever
    # ffmpeg's scene metric saw.  Episode 5 plays five of its six setups in one
    # room, where a real cut between two corners can score under the threshold.
    report["internal_cut_rows"] = internal_cut_rows(placed, records, seen)
    report["missing_cuts"] = drop_on_grid(
        missing_cuts(planned_cuts(placed), seen, proven=report["edit"].get("cuts")),
        report["internal_cut_rows"])
    report["takes"] = takes_rollup(take_dir)
    report["sheets"] = sheets_rollup(episode_home.boards_dir(book, number), book)
    report["passed"] = verdict(report)
    report_path = episode_home.home(book, number) / ("qc.json" if engine == "i2v" else f"qc_{engine}.json")
    episode_home.write_json(report_path, report)
    said = sum(row["passed"] for row in report["lines"])
    grid = report["internal_cut_rows"]
    late = [r["late_frames"] for r in grid if r["on_grid"]]
    print(f"{report['seconds']:.2f}s | {lufs:.1f} LUFS {tp:.1f} dBTP | "
          f"cuts missing {len(report['missing_cuts'])}/{len(report['planned_cuts'])} "
          f"(inside take-runs: {len(late)}/{len(grid)} on grid, late up to {max(late, default=0)} f) | "
          f"lines heard {said}/{len(report['lines'])} | speech {report['speech_s']}s, "
          f"longest gap {report['longest_gap_s']}s (wall {MAX_GAP_S}) | {'PASS' if report['passed'] else 'FAIL'}")
    # A gap is not a number, it is a SHOT. ep08 reported 6.81 s and nothing
    # else, so the cure aimed at the neighbours' codas and froze one of them
    # twice; the gap belonged to the silent shot lying inside it.
    if report["longest_gap_s"] > MAX_GAP_S:
        begins, ends = gap_owner.longest_span(lines, placed["duration_s"])
        silent = [s["index"] for s in placed["shots"]
                  if not any(l["shot"] == s["index"] for l in lines)]
        print(f"  gap: {gap_owner.owner(placed['shots'], begins, ends, silent).said}")
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
    main(args[0], episode_arg(sys.argv), episode_home.engine_arg(sys.argv))
