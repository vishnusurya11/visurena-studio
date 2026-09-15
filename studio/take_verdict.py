"""G4 -- ONE consolidated, numeric verdict per rendered take attempt.

Brick: a viewer judges a take segment by segment (a segment = the picture
between two pins), and every gate is a number read off the decoded frames of
that segment against the cell it was pinned to.  Everything here is free:
ffmpeg, numpy, PIL, studio.frame_match.

The measures live in their own modules and are called once each:
  studio.motion_gate   frozen at a segment start, frozen share  (G4.1-4.2)
  studio.cut_landing   where the cut landed, foreign pictures    (G4.3-4.4)
  studio.identity_gate who is on screen                          (G4.7, flagged)
This module adds drift to the END cell, lip sync (lag AND word error rate),
turns them into one score, ranks attempts, and owns the retake budget.
"""
from __future__ import annotations

import subprocess
from dataclasses import asdict, dataclass, field
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from studio import cut_landing as cl, frame_match as fm, identity_gate, motion_gate

FPS = 24
SHARE_HARD, SHARE_ADVISORY = 0.40, 0.20
"""CALIBRATION: frozen share of the placed seconds.  Iteration 3 (25 % mean) was
not called out by the owner, iteration 4 (55 %) was; 0.40 separates every take he
named from every take he did not."""
DRIFT_HARD, DRIFT_ADVISORY = 0.50, 0.75
"""CALIBRATION: similarity of a segment's last frame to its target cell.
docs/calibration/holds11.txt -- held segments measured 0.93-1.00, the ones the reviewer marked
DRIFT 0.28-0.60.  Hard only where an END cell was drawn (there is a target); a
hold without one is advisory, because a static camera the cab crosses
legitimately ends at 0.25-0.29 against its start cell."""
LAG_TOL = 0.042
"""CALIBRATION: one frame at 24 fps (studio/av_sync.py, take_dq LAG_TOLERANCE)."""
WER_CEIL = 0.20
"""CALIBRATION: voice_qc.MAX_ERROR_RATE.  Iteration 2's T11/T18/T21 measured
1.00-1.06 and were recorded passed:true -- the WER was read and never scored."""
END_TOKEN_FRAMES = 5
"""The end frame is read one token (4 frames) before the next pin: the model cuts
up to 3 frames early, so the last frame of a segment is not its own picture."""
SAMPLES = 6
RETAKE_BUDGET = 2
"""CALIBRATION: attempts beyond the first.  A take is 9 min of GPU at the median
and 37 min at the worst (19 takes of iteration 4 = 3.98 GPU-hours); three renders
of one take is ~35 min, and past that the best attempt is kept and the take is
reported FAIL (budget spent), never rendered again."""


@dataclass
class Gate:
    name: str
    value: float | None
    ok: bool
    hard: bool
    note: str = ""
    penalty: float = 0.0


@dataclass
class SegmentReport:
    cell: str
    target: str
    start_s: float
    end_s: float
    lead_in_s: float
    still_share: float
    kind: str
    start_sim: float
    end_sim: float
    landed: bool
    offset: int


@dataclass
class TakeVerdict:
    take: int
    attempt: int
    file: str
    seconds: float
    lane: str
    gates: list[Gate]
    segments: list[SegmentReport]
    frozen_spans: list = field(default_factory=list)
    energy_q: list[float] = field(default_factory=list)
    foreign: list[dict] = field(default_factory=list)
    score: float = 0.0
    passed: bool = False

    def line(self) -> str:
        parts = [f"T{self.take:02d} a{self.attempt} {'PASS' if self.passed else 'FAIL'} {self.score:.0f}/100"]
        for g in self.gates:
            if g.value is None and not g.note:
                parts.append(f"{g.name} n/m")
                continue
            flag = "" if g.ok else (" HARD" if g.hard else " adv")
            parts.append(f"{g.name} {g.note or g.value}{flag}")
        return " | ".join(parts)


# ---- the gates ---------------------------------------------------------------

def frozen_gates(v: TakeVerdict) -> list[Gate]:
    """G4.1 frozen at a segment start and G4.2 the take's frozen share.

    BOTH HARD, AND EPISODE 5 SETTLED THE ARGUMENT.

    Over every judged attempt to the end of episode 4 -- 97 of them -- neither
    rung had ever fired:

        frozen-at-start   wall 1.00 s   max observed 0.750   fired 0 of 97
        frozen-share      wall 0.40     max observed 0.340   fired 0 of 97

    I read that as walls protecting nothing and made both advisory.  The suite
    refused it in the same run: iteration 4's T17 ran 14.75 of its 15.0 seconds
    frozen -- a share of 0.98 -- and with the rungs advisory that take PASSES.
    Reverted.  Then episode 5's first DQ pass, ON THIS INSTRUMENT:

        T21  start 2.75 s  share 0.84      the bootprint filling with water
        T00  start 2.00 s  share 0.68      Watson lying awake on the sofa
        T02  start 2.25 s  share 0.29      the hand hanging off the cushion
        T19  start 1.25 s  share 0.21
        T22  start 1.25 s  share 0.19

    FIVE of 25 takes over a wall that had not been touched in 97.  Chapter V is a
    quiet chapter and the shots were written as still pictures; had the demotion
    stood, all five would have passed and shipped.

    "It never fires" and "it cannot fire" are different claims, and only the
    second would justify moving a wall.  A hard gate that has not fired lately
    may be a floor nobody has hit since the things upstream of it improved -- and
    the moment the writing got quieter, the floor was there.

    The old worry, that both walls were read on an instrument the repo has since
    replaced, is answered: they separate cleanly on the CURRENT one, with the
    passing takes at 0.00-0.75 s and the failures at 1.25-2.75 s.

    The SCORE PENALTY is what moves a take before the wall does -- episode 4's
    T12 lost two rolls to it at 30/100 and 45/100 -- and `motion_gate.STILL`
    (13 813 frame steps over 63 takes) is the constant underneath both."""
    lead = max((s.lead_in_s for s in v.segments), default=0.0)
    share = round(sum(b - a for a, b in v.frozen_spans) / v.seconds, 2) if v.seconds else 0.0
    start = Gate("frozen-at-start", lead, lead <= motion_gate.START_LIMIT_S, True, f"{lead}s",
                 min(40.0, 25.0 * max(0.0, lead - motion_gate.GRACE_S)))
    return [start, Gate("frozen-share", share, share <= SHARE_ADVISORY, share > SHARE_HARD,
                        f"{int(share * 100)}%", 60.0 * share)]


def foreign_gate(v: TakeVerdict) -> Gate:
    """G4.4 -- any sampled frame that is another take's cell or a location plate."""
    n = sum(bool(f.get("foreign")) for f in v.foreign)
    return Gate("foreign", n, n == 0, True, str(n), min(60.0, 30.0 * n))


def landing_gate(segments: list[SegmentReport], unplanned: list[float]) -> Gate:
    """G4.3 -- every segment opens on its own pin, and the take made no cut of its own."""
    missed = [s for s in segments if not s.landed]
    note = f"{len(segments) - len(missed)}/{len(segments)} on pin"
    note += f" +{len(unplanned)} unplanned" if unplanned else ""
    return Gate("cut-landing", len(missed), not missed and not unplanned, True, note,
                25.0 * len(missed) + min(30.0, 15.0 * len(unplanned)))


def drift_gate(segments: list[SegmentReport]) -> Gate:
    """G4.5 -- did the segment reach the picture it was supposed to end on?

    Scored over the segments that HAVE a target.  This gate used to take the
    minimum over EVERY segment and then ask `has_end` globally, so a take
    holding one END'd segment beside one ordinary segment was judged on the
    ordinary one -- and an ordinary segment legitimately measures 0.25-0.29
    against its own start cell, as the calibration above says.  Episode 2 lost
    T00, T05 and T19 to segments that had no target at all.
    """
    aimed = [s for s in segments if s.target != s.cell]
    every = min((s.end_sim for s in segments), default=1.0)
    end_sim = min((s.end_sim for s in aimed), default=every)
    # HARD belongs to the segments that HAVE a target -- a segment with none
    # cannot have failed to reach one, and legitimately reads 0.25-0.29 against
    # its own start cell. The ADVISORY still watches every segment, because a
    # hold that has wandered is worth printing even when nothing was aimed at.
    # THE PENALTY GETS THE SAME SCOPE AS THE HARD VERDICT.  It did not, and that
    # one asymmetry made the whole 0-100 number a stillness meter: measured over
    # ep03's 23 records, `drift` is the ONLY non-zero penalty among the 16 takes
    # that passed, so score == 70 + 40*end_sim -- and for 33 of 37 segments
    # `end_sim` compares the last frame to the segment's OWN FIRST FRAME.  A take
    # was losing up to 30 points for moving, and ep03's three 100/100 takes are
    # its three most nearly frozen.  A segment aimed at nothing cannot miss.
    penalty = 30.0 * max(0.0, DRIFT_ADVISORY - end_sim) / DRIFT_ADVISORY if aimed else 0.0
    # THE ROW NAMES BOTH NUMBERS WHEN THEY DIFFER.  It reported `end_sim` and
    # ruled `ok` on `every`, so a take could print "drift 0.95" and carry `adv`
    # because an unaimed segment elsewhere read 0.29 -- and an unaimed segment
    # legitimately reads 0.25-0.29 against its own start cell.  The number on the
    # line then explained nothing.  Latent while a take holds one shot, as
    # episodes 4 and 5 do; live again the moment one holds two.
    # ... and ONLY when it is the reason: naming it on a clean row is noise.
    blamed = every < DRIFT_ADVISORY <= end_sim
    note = f"{end_sim:.2f} (worst hold {every:.2f})" if blamed else f"{end_sim:.2f}"
    return Gate("drift", round(end_sim, 3), every >= DRIFT_ADVISORY,
                bool(aimed) and end_sim < DRIFT_HARD,
                note, penalty)


def word_error(audio: dict, line_text: str) -> float | None:
    """The WER of what Whisper heard against the line the plan wrote, or None."""
    if not line_text or audio.get("heard") is None:
        return None
    from studio import voice_qc
    return round(voice_qc.error_rate(audio["heard"], line_text), 2)


def lip_gate(lane: str, audio: dict | None, line_text: str) -> Gate:
    """G4.6 -- a dialogue take's lips are on the wav AND the words are the line's."""
    if lane != "dialogue":
        return Gate("lip-sync", 0.0, True, True, "n/a narration")
    if not audio or not audio.get("lag_measured", True):
        return Gate("lip-sync", None, True, True, "not measured")
    lag, wer = float(audio.get("lag_s", 0.0)), word_error(audio, line_text)
    ok = abs(lag) <= LAG_TOL and (wer is None or wer <= WER_CEIL)
    pen = min(40.0, 20.0 * max(0.0, abs(lag) - LAG_TOL) / LAG_TOL)
    pen += 50.0 * max(0.0, wer - WER_CEIL) if wer is not None else 0.0
    return Gate("lip-sync", lag, ok, True, f"lag {lag:+.3f}s" + (f" wer {wer:.2f}" if wer is not None else ""), pen)


def identity_gate_row(report: dict | None) -> Gate:
    """G4.7 -- STRANGER and DRIFT are hard; the gate is quiet when it is not measured."""
    report = report or dict(identity_gate.NOT_MEASURED)
    if not report.get("measured"):
        return Gate("identity", None, True, False, "not measured")
    hard = report.get("hard") or []
    note = "; ".join(hard) if hard else f"{len(report.get('present', {}))} cast on screen"
    return Gate("identity", len(hard), not hard, bool(hard), note, 0.0)


def gates(v: TakeVerdict, audio: dict | None, line_text: str, unplanned: list[float],
          identity: dict | None = None) -> list[Gate]:
    """Every gate of the take, in the order the verdict line prints them."""
    out = frozen_gates(v)
    out.append(foreign_gate(v))
    out.append(landing_gate(v.segments, unplanned))
    out.append(drift_gate(v.segments))
    out.append(lip_gate(v.lane, audio, line_text))
    out.append(identity_gate_row(identity))
    out.append(Gate("wardrobe", None, True, False, "not measured"))
    return out


# ---- one score, one rank, automatic best-of-N --------------------------------

def score(gates_: list[Gate]) -> tuple[float, bool]:
    """100 less the penalties, clamped at 0; PASS means every HARD gate is ok."""
    total = max(0.0, 100.0 - sum(g.penalty for g in gates_))
    return round(total, 1), all(g.ok for g in gates_ if g.hard)


def rank_key(v: TakeVerdict) -> tuple[bool, float]:
    """A PASS outranks any FAIL; among equals the higher score wins.  No eye."""
    return (v.passed, v.score)


def best_of(attempts: list[TakeVerdict]) -> TakeVerdict:
    """The attempt to keep as T<NN>.mp4."""
    return max(attempts, key=rank_key)


def needs_retake(attempts: list[TakeVerdict], budget: int = RETAKE_BUDGET) -> bool:
    """Render again only while the best attempt fails and the budget is unspent."""
    return not best_of(attempts).passed and len(attempts) <= budget


def to_json(v: TakeVerdict) -> dict:
    """The record written into T<NN>.dq.json."""
    return asdict(v) | {"verdict_line": v.line()}


# ---- measurement -------------------------------------------------------------

def segments_of(anchors: list, cells: Path, seconds: float,
                staged: list[str] | None = None, sizes: dict[str, str] | None = None) -> list[tuple]:
    """(start cell, target cell, start_s, end_s, start frame) per segment, END pins folded in."""
    starts = sorted(((f, n) for n, f in anchors if not n.endswith("E.png")), key=lambda x: x[0])
    seen, segs = set(), []
    for f, n in starts:
        if n not in seen:
            seen.add(n)
            segs.append((n, f))
    out = []
    for k, (n, f) in enumerate(segs):
        end_f = segs[k + 1][1] if k + 1 < len(segs) else int(seconds * FPS)
        end_name = n.replace(".png", "E.png")
        # THE JUDGE USES THE BUILDER'S RULE.  Existing on disk is not enough:
        # `takes_r2v.end_cells` stages only an END cell one camera move away, so
        # aiming at any other one fails the take for a picture it was never
        # given.  Measured on episode 2 iteration 3 -- nine re-staged cells were
        # dropped from the reference list and drift still failed T00, T05 and
        # T07 against exactly those three.
        from studio import episode_seq_board as sq

        # THE RECORD IS THE TRUTH, NOT THE DISK.  `takes_r2v --no-ends` withholds
        # every END picture while the cells stay on disk; reading disk aimed T08
        # at Q08_0E and hard-failed it on drift for missing a picture it was never
        # given.  `staged` is the take's own reference list -- None means "no
        # record available", and only then does disk get a say.
        if staged is not None:
            target = end_name if end_name in staged else n
        else:
            # WITH THE SIZE: `reaches` drops the END floor for a size whose
            # subject fills the frame, and without it an insert's END cell is
            # refused here for being different -- which is what an insert's END
            # cell is.  `sizes` is keyed by start-cell name.
            target = (end_name if sq.reaches(cells / n, cells / end_name,
                                             (sizes or {}).get(n, "")) else n)
        out.append((n, target, round(f / FPS, 3), round(min(end_f, int(seconds * FPS)) / FPS, 3), f))
    return out


def cell_signatures(cells: Path, names) -> dict[str, np.ndarray]:
    """A flat frame_match signature per named cell.

    A NAMED CELL THAT IS NOT THERE IS AN ERROR, not an omission.  This used to
    skip it -- `if (cells / n).exists()` -- and `take_dq.main` was passing
    `boards` where `cells` was wanted after cells moved to `boards/cells/`.  The
    dict came back empty, `measure` turned that into `per_frame = []` by its own
    `if own else []`, and every picture gate read an empty list as nothing
    wrong.  Episode 4's whole DQ run produced verdicts off zero frames of
    comparison and only surfaced because the report image, drawn last, raised on
    the same bad path.

    A gate may say a take is bad, and may say it could not read something.  It
    may not say nothing and be taken for a pass."""
    missing = [n for n in names if not (cells / n).exists()]
    if missing:
        raise FileNotFoundError(f"{len(missing)} named cells are not in {cells}: {', '.join(sorted(missing)[:4])}")
    return {n: fm.signature(fm.load(cells / n)).ravel() for n in names}


def opening_similarity(sigs: np.ndarray, cell: np.ndarray, first: int) -> float:
    """The best match to the pinned cell over the pin's own token (a pin smears over it)."""
    window = range(first, min(first + 4, len(sigs)))
    return round(max((float(sigs[i] @ cell) for i in window), default=0.0), 3)


def segment_rows(anchors: list, cells: Path, seconds: float, sigs: np.ndarray,
                 motion: dict, rows: list[dict], kinds: dict,
                 staged: list[str] | None = None) -> list[SegmentReport]:
    """One SegmentReport per segment: its freeze, its opening, its end, its cut.

    `staged` is the take's OWN reference list, so the judge aims only at pictures
    the render was actually given (see `segments_of`)."""
    segs = segments_of(anchors, cells, seconds, staged)
    cells = cell_signatures(cells, {n for seg in segs for n in seg[:2]})
    landed = {r["target"]: (r["delta"] is not None and -cl.MAX_EARLY <= r["delta"] <= cl.MAX_LATE) for r in rows}
    offsets = {r["target"]: (r["delta"] or 0) for r in rows}
    out = []
    for k, (cell, target, a, b, f) in enumerate(segs):
        m = motion["segments"][k] if k < len(motion["segments"]) else {"leading_still_s": 0.0, "still_share": 0.0}
        last = max(min(int(b * FPS) - END_TOKEN_FRAMES, len(sigs) - 1), f)
        opening = opening_similarity(sigs, cells[cell], min(f, len(sigs) - 1)) if cell in cells else 0.0
        want = cells.get(target, cells.get(cell))
        end_sim = round(float(sigs[last] @ want), 3) if want is not None else 1.0
        out.append(SegmentReport(cell, target, a, b, m["leading_still_s"], m["still_share"],
                                 kinds.get(cell, "hold"), opening, end_sim,
                                 landed.get(cell, True) and opening >= cl.LAND, offsets.get(cell, 0)))
    return out


def measure(video: Path, record: dict, cells: Path, seconds: float, attempt: int = 0,
            audio: dict | None = None, line_text: str = "", kinds: dict | None = None) -> TakeVerdict:
    """Decode the take once and read every gate off it."""
    frames = motion_gate.frames(video, seconds)
    anchors = record.get("anchors") or []
    motion = motion_gate.report(motion_gate.block_max(frames), anchors, kinds or {})
    sigs = cl.signatures(frames.astype(np.uint8))
    own = cell_signatures(cells, dict.fromkeys(n for n, _ in anchors))
    # cells/ and plates/ are siblings under the episode's boards/ by construction
    other = {n: fm.signature(fm.load(p)).ravel()
             for n, p in cl.foreign_pictures(cells, cells.parent / "plates", set(own)).items()}
    per_frame = cl.classify(sigs, own, other) if own else []
    rows = cl.landing(per_frame, anchors) if per_frame else []
    # The take's own reference list decides what it was AIMED at; the cells on
    # disk only say what was drawn. `--no-ends` withholds every END picture and
    # the cells stay on disk, so reading disk failed T08 on drift for missing a
    # picture it was never given.
    segs = segment_rows(anchors, cells, seconds, sigs, motion, rows, kinds or {},
                        record.get("refs"))
    v = TakeVerdict(record["index"], attempt, video.name, round(seconds, 2), record.get("lane", "narration"),
                    [], segs, motion["frozen_spans"], [round(float(x), 1) for x in motion["bins"]],
                    sampled_foreign(per_frame))
    identity = identity_gate.identity_dq(video, segs, record.get("faces", []), record.get("refs", []))
    v.gates = gates(v, audio, line_text, unplanned_from(rows), identity)
    v.score, v.passed = score(v.gates)
    return v


def sampled_foreign(per_frame: list[dict], samples: int = 8) -> list[dict]:
    """The foreign verdict at `samples` evenly spaced frames, for the record and the strip."""
    if not per_frame:
        return []
    idx = [min(int(round((len(per_frame) - 1) * k / (samples - 1))), len(per_frame) - 1) for k in range(samples)]
    return [{"at": round(i / FPS, 2), "own": per_frame[i]["own"], "score": round(per_frame[i]["own_s"], 3),
             "other": per_frame[i]["other"], "other_score": round(per_frame[i]["other_s"], 3),
             "foreign": per_frame[i]["foreign"]} for i in idx]


def unplanned_from(rows: list[dict]) -> list[float]:
    """Cuts the take made that the plan did not: a ping-pong back to an earlier cell."""
    return [round(r["pin"] / FPS, 2) for r in rows if r["pingpong"] > cl.MAX_PINGPONG]


# ---- the picture the owner reads ---------------------------------------------

TILE = (150, 262)
PAD = 4


def sparkline(d: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int, bins: list[float],
              spans: list, seconds: float) -> None:
    """Motion energy per quarter second, with the frozen spans shaded."""
    d.rectangle((x, y, x + w, y + h), fill="#222")
    for a, b in spans:
        d.rectangle((x + w * a / seconds, y, x + w * b / seconds, y + h), fill="#7a1a1a")
    n = max(len(bins), 1)
    for i, v in enumerate(bins):
        vh = min(h, v / 20.0 * h)
        d.line((x + w * i / n, y + h, x + w * i / n, y + h - vh),
               fill="#7cf" if v >= motion_gate.STILL else "#f66", width=2)
    d.line((x, y + h - motion_gate.STILL / 20.0 * h, x + w, y + h - motion_gate.STILL / 20.0 * h), fill="#888")


def sample_frame(video: Path, at: float) -> Image.Image | None:
    """One frame of the take at `at` seconds, already at strip size."""
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{at:.3f}", "-i", str(video), "-frames:v", "1",
                          "-vf", f"scale={TILE[0]}:{TILE[1]}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                         capture_output=True).stdout
    return Image.frombytes("RGB", TILE, raw) if len(raw) == TILE[0] * TILE[1] * 3 else None


def strip_row(page: Image.Image, d: ImageDraw.ImageDraw, s: SegmentReport, video: Path,
              cells: Path, v: TakeVerdict, y: int) -> int:
    """One segment's row: its START cell, its END cell, then SAMPLES frames of the take."""
    page.paste(Image.open(cells / s.cell).convert("RGB").resize(TILE), (4, y))
    d.text((6, y + 2), "START cell", fill="#ff0")
    if s.target != s.cell and (cells / s.target).exists():
        page.paste(Image.open(cells / s.target).convert("RGB").resize(TILE), (4 + TILE[0] + PAD, y))
        d.text((6 + TILE[0] + PAD, y + 2), "END cell", fill="#ff0")
    else:
        d.rectangle((4 + TILE[0] + PAD, y, 4 + 2 * TILE[0] + PAD, y + TILE[1]), outline="#555")
        d.text((10 + TILE[0] + PAD, y + 2), "hold: ends on START", fill="#aaa")
    for k in range(SAMPLES):
        at = s.start_s + (s.end_s - s.start_s) * (k + 0.5) / SAMPLES
        tile = sample_frame(video, at)
        if tile:
            page.paste(tile, (4 + (k + 2) * (TILE[0] + PAD), y))
        frozen = any(a <= at < b for a, b in v.frozen_spans)
        d.text((6 + (k + 2) * (TILE[0] + PAD), y + 2), f"{at:.1f}s" + (" FROZEN" if frozen else ""),
               fill="#f66" if frozen else "#fff")
    return y + TILE[1] + 24


def strip(v: TakeVerdict, video: Path, cells: Path, out: Path) -> Path:
    """The one page that says what this attempt is: cells, frames, energy, verdict."""
    cols = 2 + SAMPLES
    page = Image.new("RGB", (cols * (TILE[0] + PAD) + 8, len(v.segments) * (TILE[1] + 40) + 120), "black")
    d = ImageDraw.Draw(page)
    y = 6
    for s in v.segments:
        d.text((8, y), f"segment {s.cell} -> {s.target}  {s.start_s:.2f}-{s.end_s:.2f}s  lead-in {s.lead_in_s}s"
               f"  start {s.start_sim:.2f}  end {s.end_sim:.2f}  cut {'landed' if s.landed else 'MISSED'}"
               f" ({s.offset:+d}f)", fill="#fff")
        y = strip_row(page, d, s, video, cells, v, y + 16)
    sparkline(d, 8, y, page.width - 16, 40, v.energy_q, v.frozen_spans, v.seconds)
    d.text((10, y + 42), f"motion energy per 1/4 s (line = STILL {motion_gate.STILL}); red = frozen spans", fill="#aaa")
    d.text((8, y + 62), v.line(), fill="#5f5" if v.passed else "#f55")
    page.save(out)
    return out
