#!/usr/bin/env python
"""Step 11 -- qc: measure the judged cut, the master eye judges it, then the ONE upscale.

    uv run python scripts/episode/step_11_qc.py <codex_id> <n> [--engine=r2v]

Wraps scripts/episode/qc.py --engine=r2v --at-cut, which measures the finished picture at the
cut's own scale (cut/cut_<engine>.mp4, step 10's) and stamps the sha8 it measured into
qc_<engine>_cut.json.  A FAIL on its hard rows is a refusal, as it always was.  A PASS is read
by studio.judges.master_eye: the rubric review/eye_<sha8>.json is filled in the judge's pen --
every field answered from a measure, an `n` carrying `flagged_by` and `evidence`, never a
waiver -- and a measured fault climbs studio.master_ladder (a retake, then a recut AT CUT
SCALE) before the terminal rung signs it flagged.  Then the judged cut is upscaled once
(assemble --upscale; owner 2026-10-18: upscale last, once -- Jekyll ep03 paid the 4x on every
master round), and its QC report and rubric are carried to the master's sha8 (qc_<engine>.json,
the pair studio/youtube_publish.MASTERS names) while cut/upscaled.json traces those master bytes
to the judged cut.  The face strip (log only) is cut from the upscaled master, what the viewer
sees.  Nobody is asked to watch anything.  Then the dossier, and the unit's audit sheet.
A master from before the cut-scale judge (no cut on disk) is its own judged file, as it was.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.episode import eye_review, face_refine as refine_step  # noqa: E402
from studio import comfy, episode_home, face_strip as fs, judged_gate, master_ladder, panel_content as pc  # noqa: E402
from studio import ceiling, gate_policy, master_upscale, step_cli, youtube_publish as yp  # noqa: E402
from studio.judges import master_eye  # noqa: E402

STEP_ID = "11"
NAME = "qc"
GPU = False
ENGINE = "r2v"
GATE = "MASTER"
WORKFLOW = "image_qwen3vl_caption"
ASK = (pc.ASK + '\n"framing": how much of the main person the frame holds, one of '
       "extreme_close, close, medium_close, medium, full, wide.\n"
       '"action": what the main person is DOING, as one or two plain verbs.\n'
       '"parts": the body parts of the main person that are visible, a list from head, torso, arm, hand, leg, foot.')
"""The panel vocabulary plus the two fields the story field is answered from."""


def engine_of(extra: list[str]) -> str:
    """`--engine=` when typed, else the house engine."""
    return next((a.split("=", 1)[1] for a in extra if a.startswith("--engine=")), ENGINE)


def engine_flags(extra: list[str]) -> list[str]:
    return [f"--engine={engine_of(extra)}", *[a for a in extra if not a.startswith("--engine=")]]


QC_MEASURES = ("scripts/episode/qc.py", "studio/edit_gate.py", "studio/episode_sound.py",
               "studio/speech_gap.py", "studio/master_loudness.py", "studio/line_laid.py",
               "studio/take_inputs.py")
"""The code a QC report is measured by: a change here re-measures the master."""


def qc_measures_sha8() -> str:
    """The QC code's fingerprint (line endings normalised)."""
    import hashlib
    root = Path(__file__).resolve().parents[2]
    body = b"".join((root / rel).read_bytes().replace(b"\r\n", b"\n") for rel in QC_MEASURES)
    return hashlib.sha256(body).hexdigest()[:8]


def pair(home: Path, engine: str) -> tuple[Path, Path]:
    """(master, qc report) for one engine, where qc.py and the publish ladder agree they are."""
    for name, master, qc in yp.MASTERS:
        if name == engine:
            return Path(home) / "cut" / master, Path(home) / qc
    raise SystemExit(f"unknown engine {engine!r}; one of {[n for n, _m, _q in yp.MASTERS]}")


def judged_pair(home: Path, engine: str) -> tuple[Path, Path]:
    """(the file the judges read, its QC report): the judged cut and qc_<engine>_cut.json; a master
    from before the cut-scale judge (no cut on disk) is its own judged file, with its own report."""
    master, qc = pair(home, engine)
    cut = master_upscale.cut_of(master)
    return (cut, qc.with_name(f"{qc.stem}_cut.json")) if cut.exists() else (master, qc)


def is_cut(path: Path) -> bool:
    return Path(path).name.startswith("cut")


def rubric_signed(home: Path, sha8: str) -> bool:
    """Whether review/eye_<sha8>.json exists and clears eye_review's refusals:
    a judge's `n` with its flag and evidence clears; a bare `n` does not."""
    path = eye_review.rubric_path(home, sha8)
    if not path.exists():
        return False
    return not eye_review.refusals(episode_home.read_json(path), sha8, path)


def done(ctx) -> bool:
    engine = engine_of(getattr(ctx, "extra", None) or [])
    master, qc = pair(ctx.home, engine)
    if not (master.exists() and qc.exists()):
        return False
    report = episode_home.read_json(qc)
    if not (report.get("passed") and report.get("sha8") == yp.sha8(master) and rubric_signed(ctx.home, report["sha8"])):
        return False
    if not master_upscale.cut_of(master).exists():
        return True                                  # a master judged itself, before the cut-scale judge
    return traced(ctx.home, engine, report)


def traced(home: Path, engine: str, report: dict) -> bool:
    """A carried verdict holds only while cut/upscaled.json says these master bytes were upscaled from
    the cut it names, that cut is the one on disk, and its own report and rubric stand."""
    master, _qc = pair(home, engine)
    cut, cut_qc = judged_pair(home, engine)
    want = report.get("cut_sha8", "")
    if not (want and master_upscale.made_from(master) == want and yp.sha8(cut) == want and cut_qc.exists()):
        return False
    return episode_home.read_json(cut_qc).get("sha8") == want and rubric_signed(home, want)


# ---- the real tools: ffmpeg, the local vision model, facenet ------------------------------

def grab_frames(work: Path):
    """`frames=`: the sampled frames of the master as RGB arrays, via ffmpeg."""
    from PIL import Image

    def frames(master: Path, times: list[float]) -> list[np.ndarray]:
        return [np.asarray(Image.open(p).convert("RGB")) for p in eye_review.grab(master, times, work)]
    return frames


def vlm_reader(work: Path, ask: str = ASK):
    """`reader=`: one frame staged as a picture and read by the local VLM, asked `ask`."""
    from PIL import Image

    def reader(frame: np.ndarray) -> str:
        path = Path(work) / "read.png"
        path.parent.mkdir(parents=True, exist_ok=True)
        Image.fromarray(np.asarray(frame).astype(np.uint8)).save(path)
        # cached_text (five-hour plan fix 5): an unchanged master's re-read is
        # free, and the answer cache keys on the frame's own bytes.
        said = comfy.cached_text(WORKFLOW, {"image_1": comfy.stage_image(path), "prompt": ask,
                                            "seed": 11, "max_new_tokens": 1024},
                                 readable=lambda text: bool(text and text.strip()))
        return said if isinstance(said, str) else str(said)
    return reader


def face_embed():
    """`embed=`: every face in a frame, its box height as a share and its facenet vector."""
    from studio.measure import faces as fz
    detect, embed = fz.embedder()

    def faces(frame: np.ndarray) -> list[dict]:
        rgb = np.asarray(frame).astype(np.uint8)
        return [{"h": (f["box"][3] - f["box"][1]) / rgb.shape[0], "vec": embed(rgb, f["box"])}
                for f in detect(rgb)]
    return faces


def face_boxes():
    """`detect=`: the face boxes in one master frame, by the eye's own CPU detector (MTCNN)."""
    from studio.measure import faces as fz
    detect, _embed = fz.embedder()
    return lambda frame: [f["box"] for f in detect(np.asarray(frame).astype(np.uint8))]


def tools(home: Path) -> dict:
    work = Path(home) / "review" / "work" / "eye"
    return {"frames": grab_frames(work), "reader": vlm_reader(work), "embed": face_embed(),
            "detect": face_boxes(), "face_reader": vlm_reader(work, master_eye.FACE_ASK)}


EYE_KIT = ("frames", "reader", "embed", "cache")
"""The kit master_eye.read takes; `detect` is the strip's, `face_reader` is passed by name."""


def face_strip(home: Path, master: Path, placed: dict, kit: dict) -> list[dict]:
    """The face contact strip for THESE master bytes (studio/face_strip; CPU: ffmpeg + the detector),
    tiered by step 09's face list; [] when the kit carries no detector."""
    if "detect" not in kit:
        return []
    room = Path(home) / "takes" / "r2v"
    records = episode_home.read_json(room / "shots.json") if (room / "shots.json").exists() else []
    dead_path = Path(home) / "takes" / "work" / "dead_cuts.json"
    dead = episode_home.read_json(dead_path) if dead_path.exists() else None
    return fs.build(home, master, yp.sha8(master), refine_step.read_face_list(room), placed, records,
                    kit["frames"], kit["detect"], dead)


def read_master(home: Path, master: Path, plan: dict, placed: dict, tools_: dict | None = None):
    """(verdict, measures) from the master eye over the real tools unless given; the face strip is
    cut first, read by the eye, and its reads kept in the owner's labels file."""
    kit = tools_ or {**tools(home), "cache": master_eye.EyeCache(home, WORKFLOW, master_eye.sha8_text(ASK))}
    strip = [] if is_cut(master) else face_strip(home, master, placed, kit)   # the strip is the master's
    eye = {k: v for k, v in kit.items() if k in EYE_KIT}
    verdict, m = master_eye.read(home, master, plan, placed, **eye, strip=strip, face_reader=kit.get("face_reader"))
    if strip:
        fs.write_labels(home, yp.sha8(master), (m.get("face_strip") or {}).get("crops") or strip)
    return verdict, m


def contact_sheet(home: Path, master: Path, sha8: str) -> Path:
    """review/contact_<sha8>.png for the audit sheet (eye_review's grid; ffmpeg)."""
    return eye_review.build(home, master, sha8)[0]


# ---- the judged gate ------------------------------------------------------------------------

def qc_report(ctx, extra: list[str]) -> dict:
    """qc.py over the master; a FAIL on its hard rows is a refusal.

    A report that already measured THESE EXACT BYTES is reused, pass or fail
    (five-hour plan fix 3, 2026-09-30): qc ran 8x on ep14 at ~9 min a pass,
    and a failed report on an unchanged master was thrown away and re-measured
    with no assemble in between.  A recut changes the sha8 and qc runs again."""
    master, qc = judged_pair(ctx.home, engine_of(extra))
    spent = clock_spent(ctx)
    if qc.exists() and master.exists():
        report = episode_home.read_json(qc)
        # the same bytes AND the same measuring code (ep24 03:45Z: a FAIL by a
        # rule fixed since was reused on an identical recut, forever)
        same_code = report.get("measures_sha8") == qc_measures_sha8()
        if report.get("sha8") == yp.sha8(master) and report.get("passed") and checks_cut(ctx) and not same_code:
            # a PASS on these bytes stands under moved code only when the re-measure
            # would eat the reserve (owner 2026-10-14); a FAIL is measured again below
            ctx.log(f"qc: {qc.name} passed sha8 {report['sha8']} under older code; it stands (spent clock)")
            return report
        if report.get("sha8") == yp.sha8(master) and same_code:
            if report.get("passed"):
                ctx.log(f"qc: {qc.name} already measured sha8 {report['sha8']}; reused")
                return report
            if spent:
                return past_ceiling(ctx, qc, report)
            raise SystemExit(f"REFUSED: qc FAIL in {qc.name} for these exact bytes ({fail_words(report)}); "
                             f"fix the cut before anyone watches it")
    ctx.run_script("scripts/episode/qc.py", *engine_flags(extra), *(["--at-cut"] if is_cut(master) else []),
                   *(["--ceiling-spent"] if spent else []), gpu=GPU, clock="qc")
    if not qc.exists():
        raise SystemExit(f"REFUSED: qc.py left no report at {qc.name}")
    report = episode_home.read_json(qc)
    if master.exists() and report.get("sha8") != yp.sha8(master):
        raise SystemExit(f"REFUSED: {qc.name} still measures {report.get('sha8')}, not the master's "
                         f"bytes; qc.py did not finish")
    if not report.get("passed") and spent:
        return past_ceiling(ctx, qc, report)
    if not report.get("passed"):
        raise SystemExit(f"REFUSED: qc FAIL in {qc.name} ({fail_words(report)}); fix the cut before anyone watches it")
    return report


def fail_words(report: dict) -> str:
    """`failed: loudness, gap` -- the rows a qc FAIL failed, kept in the refusal (and so in the
    events table) because the report is overwritten on the next pass (timeline debate P3)."""
    from scripts.episode import qc as qc_rows
    try:
        rows = qc_rows.failed_rows(report)
    except Exception:                                   # noqa: BLE001 -- an old report shape
        rows = []
    rows = [unmeasured(r, report) for r in rows]
    return "failed: " + (", ".join(rows) if rows else "unknown rows")


def unmeasured(row: str, report: dict) -> str:
    """`line_unheard` on a report whose ear never ran says so: QC hears the lines only once the cheap
    rows pass (C3_verdict #2), so it follows another row's fail (ep04 2026-10-27: the edit row)."""
    if row == "line_unheard" and not report.get("lines_measured", True):
        return "line_unheard (not measured: the ear runs only after the cheap rows pass)"
    return row


def clock_spent(ctx) -> bool:
    budget = getattr(ctx, "budget", None)
    return bool(budget is not None and budget.ceiling_spent())


QC_PASS_SECONDS = 420.0
"""A full qc.py re-measure, priced (Jekyll HEL ep01: 403 s)."""


def checks_cut(ctx) -> bool:
    """Whether re-measuring the master would eat the downstream reserve (run_budget.checks_cut)."""
    budget = getattr(ctx, "budget", None)
    return bool(budget is not None and budget.checks_cut(STEP_ID, QC_PASS_SECONDS))


def past_ceiling(ctx, path: Path, report: dict) -> dict:
    """At a spent clock (C3_verdict #5 (v), D3): a fail on a SAFETY row stops
    the episode; any other fail ships, the report flagged and one audit row."""
    from scripts.episode import qc as qc_rows
    failed = qc_rows.failed_rows(report)
    if stop := [name for name in failed if name in gate_policy.SAFETY]:
        raise SystemExit(f"SAFETY: {', '.join(stop)}: {path.name} fails {stop} at a spent clock; "
                         f"only the closed SAFETY list stops the episode")
    report = ceiling.flag_qc(ctx.book_dir, getattr(ctx, "unit", ""), path, report, failed)
    ctx.log(f"qc: the clock is spent; {path.name} ships flagged on {failed}")
    return report


def judge_master(ctx, memo: dict):
    """The master as it stands, read; the measures kept for the rubric's y
    fields.  The whole read runs in ONE VL window (five-hour plan fix 5:
    ~36 frames a master, each read was reloading the judge's weights)."""
    from studio import episode_clock
    master, _qc = judged_pair(ctx.home, engine_of(getattr(ctx, "extra", None) or []))
    plan = episode_home.read_json(ctx.home / "plan.json")
    placed = episode_home.read_timeline(ctx.home)
    with episode_clock.timed(ctx.book_dir, ctx.number, "master_eye"), comfy.model_kept():
        verdict, measures = read_master(ctx.home, master, plan, placed)
    memo.update(verdict=verdict, measures=measures)
    if not is_cut(master):
        ctx.log(fs.line((measures or {}).get("face_strip") or {}, yp.sha8(master)), step_id=STEP_ID)
    return verdict


def face_list_note(ctx) -> None:
    """Step 09's face list said at QC (retro 2026-10-20 item 2): a WARNING line, never a qc fail."""
    if said := refine_step.face_list_line(refine_step.read_face_list(ctx.home / "takes" / "r2v")):
        ctx.log(said, step_id=STEP_ID, level="WARNING")


def sign_master(ctx, memo: dict, verdict) -> Path:
    """The rubric for THESE bytes (the judged cut), in the judge's pen, beside its contact sheet."""
    master, _qc = judged_pair(ctx.home, engine_of(getattr(ctx, "extra", None) or []))
    sha8 = yp.sha8(master)
    contact = contact_sheet(ctx.home, master, sha8)
    return master_eye.write_rubric(ctx.home, sha8, verdict, memo.get("measures"),
                                   master=master.name, contact=contact.name, every=eye_review.EVERY_S)


def recut(ctx, extra: list[str]) -> None:
    """After a retake: the take eye re-signed for the moved take set, then the judged cut assembled
    again (no upscale) and its new bytes qc'd."""
    resign_takes(ctx)
    ctx.run_script("scripts/episode/assemble.py", f"--engine={engine_of(extra)}", "--at-cut", clock="assemble")
    qc_report(ctx, extra)


def resign_takes(ctx):
    """The take eye for the takes now on disk: G-DEAD admits a kept take flagged only through the
    eye of the CURRENT set, and a retake moves it (Jekyll ep02 T13, ep05 T00/T11/T16 refused as
    failed).  An eye already signed for these bytes is kept, unread.  Loaded when asked."""
    from scripts.episode import step_09_shoot
    return step_09_shoot.judge_takes(ctx, step_09_shoot.approved(gate_policy.of(ctx.stage, "RENDER")))


def judged(ctx, extra: list[str]) -> Path:
    memo: dict = {}
    first, moved = judge_master(ctx, memo), master_ladder.Round()
    return judged_gate.clear(
        ctx, GATE, judge=master_ladder.once(first, lambda: judge_master(ctx, memo), moved),
        sign=lambda v: sign_master(ctx, memo, v),
        ladder=master_ladder.rungs(first, recut=lambda: recut(ctx, extra), moved=moved,
                                   seconds=master_ladder.retake_seconds(ctx.home),
                                   retake=lambda shot, v: master_ladder.retake_through_take_ladder(ctx, shot, v)),
        terminal=master_ladder.flag)


# ---- the one upscale, and the verdicts carried to its bytes ---------------------------------------

def deliver_master(ctx, extra: list[str]) -> Path:
    """The judged cut upscaled ONCE (assemble --upscale) and its QC report and rubric carried to the
    master's sha8; a master already traced to the judged cut is left as it is."""
    engine = engine_of(extra)
    master, qc = pair(ctx.home, engine)
    cut, _cut_qc = judged_pair(ctx.home, engine)
    if not is_cut(cut):                                  # a master judged itself: nothing to carry
        return master
    if qc.exists() and traced(ctx.home, engine, episode_home.read_json(qc)) and qc_carried_to(qc, master):
        return master
    if master_upscale.made_from(master) != yp.sha8(cut):
        ctx.run_script("scripts/episode/assemble.py", f"--engine={engine}", "--upscale", gpu=True, clock="assemble")
    return carry(ctx, engine)


def qc_carried_to(qc: Path, master: Path) -> bool:
    return master.exists() and episode_home.read_json(qc).get("sha8") == yp.sha8(master)


def carry(ctx, engine: str) -> Path:
    """The cut's QC report and rubric onto the master's sha8, the master's face strip beside them;
    refused when cut/upscaled.json does not trace the master to the judged cut."""
    master, qc = pair(ctx.home, engine)
    cut, cut_qc = judged_pair(ctx.home, engine)
    if why := carry_refusal(ctx.home, master, cut, cut_qc):
        raise SystemExit(f"REFUSED: {why}")
    report = episode_home.read_json(cut_qc)
    strip = strip_on_master(ctx, master)
    episode_home.write_json(qc, carried_report(ctx, report, master, cut))
    carry_rubric(ctx.home, report["sha8"], master, strip)
    ctx.log(f"carried: {cut_qc.name} and eye_{report['sha8']}.json -> {master.name} {yp.sha8(master)}", step_id=STEP_ID)
    return master


def carry_refusal(home: Path, master: Path, cut: Path, cut_qc: Path) -> str:
    """Why the cut's verdicts may not go onto this master, '' when they may: the master must be traced
    to the judged cut's bytes, and that cut measured, passed and signed."""
    digest = yp.sha8(cut)
    if not master.exists() or master_upscale.made_from(master) != digest:
        return f"{master.name} was not made from the judged cut {cut.name} ({digest}); the upscale left no traced master"
    report = episode_home.read_json(cut_qc) if cut_qc.exists() else {}
    if report.get("sha8") != digest or not report.get("passed"):
        return f"{cut_qc.name} has not passed these cut bytes ({digest}); measure the cut first"
    if not rubric_signed(home, digest):
        return f"no signed rubric for the judged cut {digest}; the master eye judges the cut first"
    return ""


def carried_report(ctx, report: dict, master: Path, cut: Path) -> dict:
    """The cut's report about the master's bytes: what was judged (`cut_sha8`) and what upscaled it."""
    from scripts.episode import qc as qc_rows
    work = ctx.home / "takes" / "work"
    return {**report, "sha8": yp.sha8(master), "master": episode_home.relative(ctx.book_dir, master),
            "cut_sha8": report["sha8"], "judged_on": cut.name, "at_cut": False,
            "upscale": qc_rows.upscale_block(work)}


def carry_rubric(home: Path, cut_sha8: str, master: Path, strip: dict) -> Path:
    """review/eye_<master sha8>.json: the judged cut's rubric, its file and sha8 named; a rubric a
    person answered is never written over."""
    target = eye_review.rubric_path(home, yp.sha8(master))
    if target.exists() and master_eye.owner_answered(episode_home.read_json(target)):
        return target
    doc = episode_home.read_json(eye_review.rubric_path(home, cut_sha8))
    doc.update(sha8=yp.sha8(master), master=master.name,
               judged_on={"file": master_upscale.cut_of(master).name, "sha8": cut_sha8})
    if strip.get("crops"):
        doc["face_strip"] = strip                      # log only: beside the fields, never one of them
    return episode_home.write_json(target, doc)


def strip_on_master(ctx, master: Path) -> dict:
    """The face strip from the upscaled master (what the viewer sees), each crop read by the eye and
    kept in the owner's labels file: log only, never a fault."""
    work = Path(ctx.home) / "review" / "work" / "eye"
    kit = {"frames": grab_frames(work), "detect": face_boxes()}
    with comfy.model_kept():
        rows = master_eye.read_strip(ctx.home, face_strip(ctx.home, master, episode_home.read_timeline(ctx.home), kit),
                                     vlm_reader(work, master_eye.FACE_ASK))
    measure = master_eye.strip_measure(rows)
    if rows:
        fs.write_labels(ctx.home, yp.sha8(master), rows)
    ctx.log(fs.line(measure, yp.sha8(master)), step_id=STEP_ID)
    return measure


def run(ctx) -> None:
    extra = getattr(ctx, "extra", None) or []
    report = qc_report(ctx, extra)
    face_list_note(ctx)
    if not rubric_signed(ctx.home, report["sha8"]):
        judged(ctx, extra)
    deliver_master(ctx, extra)
    ctx.run_script("scripts/episode/dossier.py", clock="dossier")
    ctx.run_script("scripts/audit/sheet.py")


if __name__ == "__main__":
    raise SystemExit(step_cli.main(sys.modules[__name__], sys.argv))
