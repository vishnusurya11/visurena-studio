"""No test may ask the real compute router, or write its decisions under the real library.

MEASURED 2026-10-21 (window 2 of the ep02 rehearsal): 21 `rtx master` rows, reason
`VISURENA_DEVICE=cpu`, 15 s apart over exactly WAIT_S=300, landed in the REAL
`library/.device/decisions.jsonl` at 21:02:41-21:07:41 PDT, and again from 21:11:59,
each 3 min into a full `pytest -q`.  `test_the_rtx_master_keeps_every_frame_from_zero_without_holes`
swaps `Rtx` for a CPU stand-in but passes no `upscaler`, so `settled_for_card` asked the
live router; under VISURENA_DEVICE=cpu it answered cpu every poll, the test slept five real
minutes and then measured the LANCZOS path, not the RTX one it names.  Without the variable
the same call reads the live ComfyUI queue and nvidia-smi.

The trap points the router's log and claims at a session folder, makes its default probe
trip (device_for turns that into a cpu answer naming the trap), and makes `card_free`
without an injected route raise.
"""
from pathlib import Path

import pytest

from studio import compute_device as cd
from studio import master_upscale as mu
from studio import settings

REAL = Path(settings.REAL_LIBRARY).resolve()


def outside_real(path: Path) -> bool:
    path = Path(path).resolve()
    return REAL != path and REAL not in path.parents


def test_the_router_writes_its_decisions_and_claims_beside_the_tests():
    assert outside_real(cd.LOG) and outside_real(cd.CLAIMS)


def test_a_card_asked_of_the_live_router_trips():
    assert outside_real(cd.LOG)                       # checked first: a red run never writes the real log
    with pytest.raises(RuntimeError, match="compute router"):
        mu.card_free("rtx master", 4.0, sleep=lambda s: None)


def test_the_default_probe_is_the_trap_and_the_answer_is_the_cpu():
    said = []
    assert cd.device_for("a test job", 1.0, log=said.append) == "cpu"
    assert "a test reached the compute router" in said[0].reason


def test_an_injected_route_still_reaches_the_real_card_free():
    assert mu.card_free("av3 master", 4.0, route=lambda job, need: "cuda") is True
