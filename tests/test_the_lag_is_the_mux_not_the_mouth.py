"""The take-vs-composite lag measures the MUX, and its name must say so.

MEASURED on episode 10's seven dialogue takes (analyst F): `av_sync.take_lag`
cross-correlates the take's soundtrack with the wav that drove it -- and the
take's soundtrack IS that wav re-encoded.  Normalised correlation 0.86-0.95 at
exactly HANDLE on every take; all seven read +0.000 or -0.010.  The number
cannot fail, and the verdict line printed it as "lip-sync lag".

By eye all seven mouths were on their words.  But the pipeline has no
instrument that would have said so if they were not.  Until one exists, the
field is `mux_lag_s` -- was the sound laid where we put it -- everywhere it is
written or printed, so nobody reads it as a measurement of the mouth.
"""
import importlib.util
from pathlib import Path

from studio import av_sync, take_verdict

ROOT = Path(__file__).resolve().parents[1]


def load(name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / "episode" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_the_sync_module_names_what_it_measures():
    assert av_sync.mux_lag is av_sync.take_lag
    assert "mux" in (av_sync.take_lag.__doc__ or "").lower()


def test_the_sidecar_key_is_mux_lag():
    dq = load("take_dq")
    got = dq.lag_verdict(0.010, dialogue=True)
    assert got["mux_lag_s"] == 0.01 and "lag_s" not in got


def test_the_verdict_line_says_mux_lag_not_lip_sync_lag():
    g = take_verdict.lip_gate("dialogue", {"mux_lag_s": 0.01, "lag_measured": True}, "")
    assert "mux lag" in g.note and "lip-sync lag" not in g.note


def test_an_old_sidecar_written_with_the_old_key_still_reads():
    """Episode 10's T*.dq.json on disk carry `lag_s`; a re-run of the verdict
    or the run cards must not read them as zero."""
    g = take_verdict.lip_gate("dialogue", {"lag_s": -0.5, "lag_measured": True}, "")
    assert not g.ok
    from studio import motion_gate
    assert motion_gate.attempt_score({"audio": {"lag_ok": True, "lag_s": 0.3}})[-1] == 0.3
