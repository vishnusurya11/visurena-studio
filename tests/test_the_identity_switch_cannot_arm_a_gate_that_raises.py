r"""`enabled()` may not go True while `observe()` is still a NotImplementedError.

    studio/identity_gate.py:156   return os.environ.get(SWITCH, "").lower() != "off" and _backend() is not None
    studio/identity_gate.py:161   raise NotImplementedError("identity measuring needs facenet-pytorch; ...")

`enabled()` becomes True the moment `facenet_pytorch` imports. `observe()` --
the only thing that actually measures a face -- raises. So the documented
install, on its own, converts every `take_dq` run in the repo from a quiet
"identity: not measured" into a crash, across every take of every episode.

Nothing would catch it first: `tests/test_identity_gate.py:127` monkeypatches
`observe` away, so all sixteen of its tests stay green over a gate that cannot
run. That is the same shape as the two faults found earlier today -- a test that
supplies the thing it is testing for -- and here it is armed to fire on whoever
installs a dependency.

The switch is now the conjunction it always claimed to be: the backend imports
AND there is something to run. Writing `observe()` is the work; when it is
written, this test's second case is what says so, and `enabled()` follows by
itself with no edit here.

(Recorded while I am at it, because I had it backwards and repeated it: the
thresholds in this module ARE facenet-calibrated, and the docstring is right.
MATCH 0.60 / STRANGER 0.45 are VGGFace2 cosines -- SFace's same-person line is
0.363 -- and the measured cast matrix holds negative values, which SFace's
non-zero-centred 128-d embeddings do not produce. The SFace numbers belong to a
different, retired gate that asked the opposite question: whether two men in the
cast are too ALIKE.)
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from studio import identity_gate as g


def test_the_switch_is_off_while_the_measurer_raises(monkeypatch):
    """Even with a backend present and the switch not set to off."""
    monkeypatch.setattr(g, "_backend", lambda: object())
    monkeypatch.delenv(g.SWITCH, raising=False)
    assert g.enabled() is False, (
        "enabled() armed a gate whose observe() raises; installing facenet would "
        "crash take_dq on every take of every episode")


def test_the_switch_follows_observe_once_it_is_written(monkeypatch):
    """No edit to `enabled()` is needed when the measurer lands -- this is what
    makes the guard self-retiring rather than another thing to remember."""
    monkeypatch.setattr(g, "_backend", lambda: object())
    monkeypatch.delenv(g.SWITCH, raising=False)
    monkeypatch.setattr(g, "observe", lambda video, segments, sheets, samples=8: [])
    assert g.enabled() is True


def test_off_still_wins_over_a_working_measurer(monkeypatch):
    monkeypatch.setattr(g, "_backend", lambda: object())
    monkeypatch.setattr(g, "observe", lambda video, segments, sheets, samples=8: [])
    monkeypatch.setenv(g.SWITCH, "off")
    assert g.enabled() is False


def test_no_backend_is_still_off(monkeypatch):
    monkeypatch.setattr(g, "_backend", lambda: None)
    monkeypatch.setattr(g, "observe", lambda video, segments, sheets, samples=8: [])
    monkeypatch.delenv(g.SWITCH, raising=False)
    assert g.enabled() is False


def test_the_measurer_is_still_unwritten_and_says_so():
    """When this fails, `observe()` has been written and the gate can be turned on."""
    import pytest

    with pytest.raises(NotImplementedError):
        g.observe(None, [], {})
