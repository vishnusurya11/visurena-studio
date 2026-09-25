"""One batched retake round per rung, with its reason on the argv.  The
renderer refuses a round of one take unless it is declared the last; the
ladder's round for a rung IS the last round for that cause, so a lone retake
carries `--last` and passes the same refusal every hand-typed round meets."""
from __future__ import annotations

from scripts.episode import takes_r2v
from studio import take_ladder
from studio.judges.verdict import Fault


def test_the_renderer_refuses_a_lone_retake_without_last_and_a_round_without_a_reason():
    assert "refused" in takes_r2v.retake_refusal([7], "lag", last=False)
    assert takes_r2v.retake_refusal([7], "lag", last=True) is None
    assert takes_r2v.retake_refusal([7, 9], "", last=False).startswith("a retake names its reason")
    assert takes_r2v.retake_refusal([7, 9], "seed: jump", last=False) is None
    assert takes_r2v.retake_refusal([], "", last=False) is None


def test_the_ladders_round_of_one_declares_itself_last_and_a_batch_does_not():
    one = take_ladder.retake_args([7], "seed: frozen-at-start")
    assert one == ["--retake=7", "--why=seed: frozen-at-start", "--last"]
    assert takes_r2v.retake_refusal(takes_r2v.retake_list(one), takes_r2v.retake_why(one), "--last" in one) is None
    two = take_ladder.retake_args([9, 7], "move_type: pass-through")
    assert two == ["--retake=7,9", "--why=move_type: pass-through"]
    assert takes_r2v.retake_refusal(takes_r2v.retake_list(two), takes_r2v.retake_why(two), "--last" in two) is None


def test_the_reason_names_the_rung_and_every_cause_it_answers():
    faults = [Fault(kind="jump", where="T07"), Fault(kind="cut-vote", where="T09"), Fault(kind="jump", where="T09")]
    assert take_ladder.why_of("seed", faults) == "seed: cut-vote, jump"
