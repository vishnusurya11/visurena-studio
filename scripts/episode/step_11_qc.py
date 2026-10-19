#!/usr/bin/env python
"""Step 11 -- qc: measure the delivered master, then the master eye judges it.

    uv run python scripts/episode/step_11_qc.py <codex_id> <n> [--engine=r2v]

Wraps scripts/episode/qc.py --engine=r2v, which stamps the sha8 it measured
into the report beside the master (episodes/epNN/qc_<engine>.json, the pair
studio/youtube_publish.MASTERS names).  A FAIL on its hard rows is a refusal,
as it always was.  A PASS is read by studio.judges.master_eye: the rubric
review/eye_<sha8>.json is filled in the judge's pen -- every field answered
from a measure, an `n` carrying `flagged_by` and `evidence`, never a waiver --
and a measured fault climbs studio.master_ladder (recut x2, retake x1) before
the terminal rung signs it flagged.  Nobody is asked to watch anything.  Then
the dossier, and the unit's audit sheet for the owner's after-the-fact look.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.episode import eye_review  # noqa: E402
from studio import comfy, episode_home, judged_gate, master_ladder, panel_content as pc  # noqa: E402
from studio import ceiling, gate_policy, step_cli, youtube_publish as yp  # noqa: E402
from studio.judges import master_eye  # noqa: E402

STEP_ID = "11"
NAME = "qc"
GPU = False
ENGINE = "r2v"
GATE = "MASTER"
WORKFLOW = "image_qwen3vl_caption"
ASK = (pc.ASK + '\n"framing": how much of the main person the frame holds, one of '
       "extreme_close, close, medium_close, medium, full, wide.\n"
       '"action": what the main person is DOING, as one or two plain verbs.')
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


def rubric_signed(home: Path, sha8: str) -> bool:
    """Whether review/eye_<sha8>.json exists and clears eye_review's refusals:
    a judge's `n` with its flag and evidence clears; a bare `n` does not."""
    path = eye_review.rubric_path(home, sha8)
    if not path.exists():
        return False
    return not eye_review.refusals(episode_home.read_json(path), sha8, path)


def done(ctx) -> bool:
    master, qc = pair(ctx.home, engine_of(getattr(ctx, "extra", None) or []))
    if not (master.exists() and qc.exists()):
        return False
    report = episode_home.read_json(qc)
    return (bool(report.get("passed")) and report.get("sha8") == yp.sha8(master)
            and rubric_signed(ctx.home, report["sha8"]))


# ---- the real tools: ffmpeg, the local vision model, facenet ------------------------------

def grab_frames(work: Path):
    """`frames=`: the sampled frames of the master as RGB arrays, via ffmpeg."""
    from PIL import Image

    def frames(master: Path, times: list[float]) -> list[np.ndarray]:
        return [np.asarray(Image.open(p).convert("RGB")) for p in eye_review.grab(master, times, work)]
    return frames


def vlm_reader(work: Path):
    """`reader=`: one frame staged as a picture and read by the local VLM."""
    from PIL import Image

    def reader(frame: np.ndarray) -> str:
        path = Path(work) / "read.png"
        path.parent.mkdir(parents=True, exist_ok=True)
        Image.fromarray(np.asarray(frame).astype(np.uint8)).save(path)
        # cached_text (five-hour plan fix 5): an unchanged master's re-read is
        # free, and the answer cache keys on the frame's own bytes.
        said = comfy.cached_text(WORKFLOW, {"image_1": comfy.stage_image(path), "prompt": ASK,
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


def tools(home: Path) -> dict:
    work = Path(home) / "review" / "work" / "eye"
    return {"frames": grab_frames(work), "reader": vlm_reader(work), "embed": face_embed()}


def read_master(home: Path, master: Path, plan: dict, placed: dict, tools_: dict | None = None):
    """(verdict, measures) from the master eye over the real tools unless given."""
    kit = tools_ or {**tools(home), "cache": master_eye.EyeCache(home, WORKFLOW, master_eye.sha8_text(ASK))}
    return master_eye.read(home, master, plan, placed, **kit)


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
    master, qc = pair(ctx.home, engine_of(extra))
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
    ctx.run_script("scripts/episode/qc.py", *engine_flags(extra), *(["--ceiling-spent"] if spent else []),
                   gpu=GPU, clock="qc")
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
    return "failed: " + (", ".join(rows) if rows else "unknown rows")


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
    master, _qc = pair(ctx.home, engine_of(getattr(ctx, "extra", None) or []))
    plan = episode_home.read_json(ctx.home / "plan.json")
    placed = episode_home.read_timeline(ctx.home)
    with episode_clock.timed(ctx.book_dir, ctx.number, "master_eye"), comfy.model_kept():
        verdict, measures = read_master(ctx.home, master, plan, placed)
    memo.update(verdict=verdict, measures=measures)
    return verdict


def sign_master(ctx, memo: dict, verdict) -> Path:
    """The rubric for THESE bytes, in the judge's pen, beside its contact sheet."""
    master, _qc = pair(ctx.home, engine_of(getattr(ctx, "extra", None) or []))
    sha8 = yp.sha8(master)
    contact = contact_sheet(ctx.home, master, sha8)
    return master_eye.write_rubric(ctx.home, sha8, verdict, memo.get("measures"),
                                   master=master.name, contact=contact.name, every=eye_review.EVERY_S)


def recut(ctx, extra: list[str]) -> None:
    """The free rung: assemble again from the takes on disk, then qc the new bytes."""
    ctx.run_script("scripts/episode/assemble.py", f"--engine={engine_of(extra)}", clock="assemble")
    qc_report(ctx, extra)


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


def run(ctx) -> None:
    extra = getattr(ctx, "extra", None) or []
    report = qc_report(ctx, extra)
    if not rubric_signed(ctx.home, report["sha8"]):
        judged(ctx, extra)
    ctx.run_script("scripts/episode/dossier.py", clock="dossier")
    ctx.run_script("scripts/audit/sheet.py")


if __name__ == "__main__":
    raise SystemExit(step_cli.main(sys.modules[__name__], sys.argv))
