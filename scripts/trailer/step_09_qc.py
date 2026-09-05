"""Step 09 -- qc: measure the DELIVERED master, gate on the floor, recut or flag.

The floor (loudness, true peak, every shot bound, no line clipped, the bed
stopped before the card) fails the run; the targets -- how much of the
runtime is music alone, where the loudest moment sits, whether act 3 lifts
over act 2, the per-act beat lock -- only flag it.  A floor fail buys two
recuts at a longer walk stretch -- step 08 owns the cut, step 06 the walk, so this step only asks --
and after that the master ships flagged: qc.json says so, and the retrospect
reads it, but nobody is asked a question.
"""
from __future__ import annotations

import json

from scripts.trailer import qc
from studio.ladder import Ladder, Rung, climb
from studio.trailer_stage_spec import QCReport

STEP_ID = "09"
NAME = "qc"
RECUT_SECONDS = 120.0
LADDER = Ladder([Rung("measure", 0.0), Rung("recut", RECUT_SECONDS, tries=2)],
                terminal="ship_flagged")


def measure(ctx) -> QCReport:
    """The seam tests replace: qc.qc shells out to ffmpeg and runs the tracker."""
    return qc.qc(ctx.out_dir)


def recut(ctx, attempt: int) -> None:
    """Step 08's recut, imported here so step 09 loads without ffmpeg's callers."""
    from scripts.trailer import step_08_assemble
    step_08_assemble.recut(ctx, attempt)


def verdict(report: QCReport) -> tuple[bool, str, str]:
    """The floor is damage, not taste: a level outside delivery range, a shot
    whose face never bound, a picture already seen, a line that CLIPPED, and a
    bed that faded into the card instead of stopping before it."""
    measured = (f"{report.integrated_lufs:.1f} LUFS, TP {report.true_peak:.1f}, "
                f"{report.unbound_shots} unbound, "
                f"{'clean' if report.lines_are_clean else 'CLIPPED'} lines, "
                f"{'hard out' if report.hard_out else 'NO hard out'}")
    return report.floor_pass, measured, ("-15.5..-12.5 LUFS, TP <= -1.0, 0 unbound, "
                                         "no clipped line, the bed stops before the card")


def flag_shipped(ctx) -> None:
    """A sidecar key, not a model field: the report stays what was measured."""
    path = ctx.out_dir / "qc.json"
    written = json.loads(path.read_text(encoding="utf-8"))
    path.write_text(json.dumps(written | {"shipped_flagged": True}, indent=2), encoding="utf-8")
    ctx.tracker.log("master shipped FLAGGED: the floor failed after two recuts",
                    level="WARNING", step_id=STEP_ID)


def run(codex_id: str, ctx) -> None:
    def attempt(rung, i):
        if rung.name == "recut":
            recut(ctx, i + 1)
        return measure(ctx)

    outcome = climb(LADDER, STEP_ID, attempt, verdict, ctx.budget, ctx.learn, gate_name="floor")
    if outcome.terminal:
        flag_shipped(ctx)
    report = QCReport.model_validate_json((ctx.out_dir / "qc.json").read_text(encoding="utf-8"))
    print(f"[{STEP_ID}] {'floor pass' if report.floor_pass else 'FLAGGED'}: "
          f"{report.cuts} cuts, {report.integrated_lufs:.1f} LUFS, "
          f"{report.music_only_fraction:.0%} music-only, "
          f"speech {report.speech_occupancy:.0%} of {report.speech_target:.0%}, "
          f"peak at {report.peak_position:.0%}, act3 {report.act3_over_act2_lu:+.1f} LU; "
          f"flags: {', '.join(report.flags) or 'none'}")
