"""Every hand-back point drive.py has today (repo integrator §4, H1-H25) is a
line in a log; `classify` is the ordered regex table that turns the line into
one of {completed, retry, cure, wait, brain, park} and a work order the desk
already accepts.  The tails are the real wordings from the step scripts, the
first one from ep19's drive_run01.log (2026-10-06, the $3 wall)."""
from __future__ import annotations

import pytest

from studio import autopilot as ap

EP19_TAIL = (
    '  File "D:\\Projects\\KingdomOfViSuReNa\\alpha\\visurena_studio\\studio\\llm.py", line 148, in guard_spend\n'
    '    raise OverBudget(f"episode {_SPEND[\'unit\']} has spent ${spent:.2f} of its ${cap:.2f} "\n'
    "studio.llm.OverBudget: episode ep19 has spent $3.10 of its $3.00 ceiling; "
    "this call would cross it, so it was not sent")
SIGNED, UNSIGNED, RENDERED = {"plan.json"}, {"plan.json", "plan.deferred.json"}, {"plan.json", "placed.json", "takes"}

CASES = [
    ("H4 over budget (ep19)", EP19_TAIL, UNSIGNED, ("park", "over_budget", None)),
    ("completed", "step 13 ...\n=== EPISODE completed | ep18 ===", SIGNED, ("completed", "completed", None)),
    ("H1 dirty tree", "ep20: REFUSED to start: the working tree is dirty; commit the code first (fix #2)", set(),
     ("wait", "tree_dirty", None)),
    ("H2 title card", "ep20: REFUSED: ep20's title card could not be baked (titles_batch)", set(),
     ("brain", "title_card", None)),
    ("H3 plan deferred", "DEFERRED PLAN | ep19 | battery at plan: CONTRACT -> defer | aside: episodes/ep19/plan.deferred.json",
     UNSIGNED, ("retry", "plan_deferred", None)),
    ("H5 cast unbound", "DEFERRED PLAN | ep20 | CAST BOUND: no sheet for the curate | aside: episodes/ep20/plan.deferred.json",
     UNSIGNED, ("cure", "cast_unbound", ("refs", "04"))),
    ("H6 speech gap, not rendered", "SystemExit: REFUSED: speech gap of 7.2 s over 6.0 s after trim", {"plan.json", "placed.json"},
     ("cure", "speech_gap", ("redo", "02"))),
    ("H6 speech gap, rendered", "SystemExit: REFUSED: speech gap of 7.2 s over 6.0 s after trim", RENDERED,
     ("park", "speech_gap_rendered", None)),
    ("H7 no shots", "SystemExit: REFUSED: the plan has no shots to lay out into storyboard/layout.json", SIGNED,
     ("park", "no_shots", None)),
    ("H7 no panels", "SystemExit: REFUSED: no panels under storyboard/ after panels.py", SIGNED,
     ("retry", "no_render_output", None)),
    ("H7 no takes", "SystemExit: REFUSED: no takes under takes/r2v/ after the render", SIGNED,
     ("retry", "no_render_output", None)),
    ("H8 takes wait on panels", "SystemExit: REFUSED: the takes wait on the panels: eye_01.json is older than panel 03",
     SIGNED, ("cure", "takes_wait_on_panels", ("redo", "08"))),
    ("H9 ceiling refuses the render", "SystemExit: REFUSED: the takes want 4000 s and the episode ceiling leaves 900 s; a run over the ceiling takes terminal rungs, not renders",
     SIGNED, ("retry", "ceiling_refused_render", None)),
    ("H11 qc FAIL", "SystemExit: REFUSED: qc FAIL in qc_r2v.json for these exact bytes; fix the cut", RENDERED,
     ("brain", "qc_fail", None)),
    ("H12 qc no report", "SystemExit: REFUSED: qc.py left no report at qc_r2v.json", RENDERED,
     ("retry", "qc_no_report", None)),
    ("H13 invalid verdict", "SystemExit: INVALID VERDICT: EYE_TAKES's judge returned the same fault 13 times -- a broken measure",
     SIGNED, ("park", "invalid_verdict", None)),
    ("H14 queue busy", "SystemExit: REFUSED: ComfyUI's queue stayed busy for 7200 s; another job holds the GPU", SIGNED,
     ("cure", "queue_busy", ("comfy_restart", None))),
    ("H15 engine transient", "studio.comfy.EngineLost: abc123 vanished: the engine restarted", SIGNED,
     ("retry", "engine_transient", None)),
    ("H15 other traceback", "Traceback (most recent call last):\n  File x\nKeyError: 0", SIGNED,
     ("brain", "failed: KeyError: 0", None)),
    ("H17 held", "SystemExit: HELD: RENDER_HOLD is set; ep20 stops before step 09", SIGNED, ("wait", "held", None)),
    ("H18 owner gate", "OWNER G-STANDING | ep20 | the channel has no standing approval | sign: publish/standing.json",
     RENDERED, ("park", "escalated: G-STANDING", None)),
    ("H19 not public", "SystemExit: https://youtu.be/abc is NOT public; fix the channel, re-run", RENDERED,
     ("retry", "not_public", None)),
    ("H19 no ledger row", "SystemExit: the upload left no ledger row for book/ep20/a7345be8", RENDERED,
     ("retry", "no_ledger_row", None)),
    ("other DEFERRED", "RuntimeError: DEFERRED: EYE_TAKES needs 528 s for its rung", RENDERED,
     ("brain", "deferred: DEFERRED: EYE_TAKES needs 528 s for its rung", None)),
    ("other REFUSED", "SystemExit: REFUSED: the plan fails the battery twice", SIGNED,
     ("brain", "refused: REFUSED: the plan fails the battery twice", None)),
    ("empty log", "", SIGNED, ("brain", "unclassified: the log is empty", None)),
]


@pytest.mark.parametrize("label,tail,home,want", CASES, ids=[c[0] for c in CASES])
def test_classify_every_handback(label, tail, home, want):
    assert ap.classify(tail, home) == want, label


def test_classify_kinds_are_the_six_of_the_table():
    kinds = {ap.classify(tail, home)[0] for _, tail, home, _ in CASES}
    assert kinds <= ap.KINDS and ap.KINDS == {"completed", "retry", "cure", "wait", "brain", "park"}


def test_the_last_line_names_the_fault_not_the_frame():
    assert ap.last_line("a\n  File x\n\nKeyError: 0\n") == "KeyError: 0"
    assert ap.last_line("") == ""
