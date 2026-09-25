"""A repeat is a near-duplicate pair of representative frames that no shared
setup explains: the same room drawn twice inside one setup is the setup; the
same picture in two setups is the fault."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from studio.judges import master_eye as me

FIXTURE = json.loads((Path(__file__).parent / "fixtures" / "flow" / "frame_match.json").read_text("utf-8"))


def test_only_the_pair_across_setups_counts():
    ok, evidence = me.repeats(FIXTURE["pairs"])
    assert not ok and evidence["count"] == 1
    assert evidence["pairs"] == [{"a": 2, "b": 8, "cosine": 0.96, "shared_setup": False}]
    assert evidence["wall"] == me.REPEAT


def test_a_master_with_no_such_pair_is_a_y():
    ok, evidence = me.repeats([p for p in FIXTURE["pairs"] if p["shared_setup"] or p["cosine"] < 0.9])
    assert ok and evidence["count"] == 0


def test_near_pairs_are_found_from_the_signatures_and_named_by_setup():
    rng = np.random.default_rng(1)
    a = rng.integers(0, 255, (48, 84, 3)).astype(np.uint8)
    b = rng.integers(0, 255, (48, 84, 3)).astype(np.uint8)
    sig_a, sig_b = me.signatures([a, b])
    reps = {1: sig_a, 2: sig_a, 3: sig_b}
    shared = me.near_pairs(reps, {1: "room", 2: "room", 3: "road"})
    assert [(p["a"], p["b"], p["shared_setup"]) for p in shared] == [(1, 2, True)]
    assert me.repeats(shared)[0]
    apart = me.near_pairs(reps, {1: "room", 2: "road", 3: "road"})
    assert [(p["a"], p["b"], p["shared_setup"]) for p in apart] == [(1, 2, False)]
    assert not me.repeats(apart)[0]


def test_the_board_field_reads_the_recorded_similarities():
    on = {int(k): v for k, v in FIXTURE["last_vs_cell"]["on"].items()}
    off = {int(k): v for k, v in FIXTURE["last_vs_cell"]["off"].items()}
    assert me.board(on)[0]
    ok, evidence = me.board(off)
    assert not ok and evidence["off"] == {1: 0.12, 2: 0.075, 4: 0.09} and evidence["share"] == 0.75
