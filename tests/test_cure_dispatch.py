"""The dispatcher routes every G-TAKELINT family to its cure, keeps every
pre-existing mapping, and sends a row tagged [row]/[card] to its OWN data
layer's cure before any plan-field word cure can touch it.  Order is
load-bearing: figurative_gaits sits above the generic NO PACE row so a
thing's gait is swapped before a blind pace append lands on it."""
from __future__ import annotations

from studio import plan_cures as pc

TAKELINT_L8 = ("G-TAKELINT shot 14: L8 NO PACE [shot 14]: a walk, climb or ride "
               "with no pace named [plan]")


def test_each_takelint_family_routes_to_its_cure():
    rows = {
        "G-TAKELINT shot 3: L2 STILLNESS: ['held'] [plan]": "stillness_words",
        TAKELINT_L8: "figurative_gaits",
        "G-TAKELINT shot 5: L21 ARRIVAL [shot 5]: the block ends on a layout, "
        "not a movement: 'edge' [plan]": "arrival_ends",
        "G-TAKELINT shot 6: L23 PACE ON A THING [shot 6]: 'the curtain' moves "
        "at a walking pace [plan]": "drop_thing_pace",
        "G-TAKELINT shot 2: L3 SLOW: this episode names no slow move; the limp "
        "carries the slowness [plan]": "strip_slow",
        "G-TAKELINT shot 2: L9 NO LIMP [shot 2]: Watson walks or climbs with no "
        "limp [plan]": "apply_limp",
        "G-TAKELINT shot 7: L16 DIALOGUE TAIL [shot 7]: no beat at or after "
        "00:05 [plan]": "holds",
        "G-TAKELINT shot 8: L18 BANNED PROP: 'glove' (the book gives bare "
        "hands) [plan]": "strip_banned_prop",
        "G-TAKELINT shot 9: L20 STYLE: the style line is 48 words; the cap is "
        "16 [plan]": "pin_series",
    }
    for row, want in rows.items():
        assert pc.cure_for(row) == want, (row, pc.cure_for(row))


def test_a_row_or_card_tag_outranks_every_word_cure():
    assert pc.cure_for("G-TAKELINT shot 3: L2 STILLNESS: ['held'] [row mrs_hall]") == "row_words"
    assert pc.cure_for("G-ROWTEXT L8 NO PACE: a walk, climb or ride with no "
                       "pace named [card revolver]") == "row_words"


def test_the_existing_no_pace_pattern_still_catches_the_takelint_row_form():
    """The spec's own check: the old r'NO PACE' pattern matches the new row,
    so the ordering above it is what keeps the swap first."""
    pattern = next(p for p, name in pc.CURES if name == "pace_words")
    assert pattern.search(TAKELINT_L8)
    assert pc.cure_for("L8 NO PACE [Shot 2]: a walk, climb or ride with no "
                       "pace named") == "pace_words"


def test_every_pre_existing_mapping_is_kept():
    rows = {
        "G-GHOST shot 3: 'the neighbour's shoulder' stages a man not in the shot": "ghost_limbs",
        "G-TWICE shot 4: Watson is placed twice": "one_position",
        "G-LIGHT: setup 'lab' names no light source with a direction": "light_directions",
        "G-SIZE shot 2: a close with no head fraction": "head_fractions",
        "beat of >= 1.0 s of silence before the button": "button_beat",
        "G-MOVES: 6 distinct moves against MIN_MOVES 8": "rebalance_heads",
        "G-SOURCE shot 3: span 'he said' is not in the chapter": "source_spans",
        "QUOTE        : [(3, 11)]": "quote_trim",
        "G-STAGE setup camp: bare creature word 'martian' in described": "strip_creatures",
        "G-STAGE shot 4: bare machine word 'tripod'": "stage_machines",
        "G-FACE-KIND shot 5: a creature id stands in faces": "drop_creature_faces",
        "G-CROWD-CLOSE shot 6: a close carries a crowd": "close_crowds",
        "G-PHANTOM setup 'roadway' (described): sentence names 'curate'": "strip_phantoms",
        "ONE PER TAKE : [(20, 21)]": "holds",
        "G-HOLE shot 3: a 7.2 s hole in speech": "holds",
        "median frame-edge tokens 2 under the floor 3": "edge_cases",
        "G-ASPECT: the plan says 9:16 where the series is 1:1": "pin_series",
    }
    for row, want in rows.items():
        assert pc.cure_for(row) == want, (row, pc.cure_for(row))


# ---- take-ladder cure dispatch (P08 item 4, cure rates dated 2026-10-19) --------------------

from studio import take_ladder as tl  # noqa: E402
from studio.judges.verdict import Fault  # noqa: E402


def warp(s: float, se: float, **ev) -> Fault:
    return Fault(kind="warp", where="T21", evidence={"value": s, **ev}, note=f"fail: S {s} Se {se} over 100% tracked")


def test_an_se_only_warp_routes_to_nothing_its_seed_cure_is_dead():
    assert tl.dead("warp_se", "seed")                              # 0 of 4: under 20 % over 4+ tries
    assert tl.cure_of([warp(-0.64, 3.55)]) == ""


def test_a_warp_over_the_s_wall_routes_to_a_seed():
    assert tl.cure_of([warp(3.0, 1.0)]) == "seed"


def test_a_warp_that_was_already_retaken_goes_to_f2_not_a_render():
    assert tl.cure_of([warp(3.0, 1.0)], taken=2) == ""


def test_a_live_class_is_not_dropped():
    assert not tl.dead("motion", "move_type") and not tl.dead("nothing", "seed")


def test_clones_on_a_clean_panel_route_to_one_seed():
    clones = [Fault(kind="clones", where="T08", evidence={"frame": 4})]
    assert tl.cure_of(clones, panel_clean=True) == "seed"
    assert tl.cure_of(clones, panel_clean=False) == ""


def test_clones_in_the_first_third_of_a_second_route_to_head_cut_first():
    early = [Fault(kind="clones", where="T08", evidence={"t": 0.1}), Fault(kind="clones", where="T08", evidence={"t": 0.25})]
    assert tl.cure_of(early, panel_clean=True) == "head_cut"
    late = early + [Fault(kind="clones", where="T08", evidence={"t": 2.0})]
    assert tl.cure_of(late, panel_clean=True) == "seed"


def test_route_passes_the_takes_attempts_to_the_warp_cure(tmp_path):
    from studio.judges.verdict import Verdict
    room = tmp_path / "takes" / "r2v"
    (room / "attempts").mkdir(parents=True)
    v = Verdict(judge="take_eye", version="1", passed=False, confidence=1.0, reads=1, faults=[warp(3.0, 1.0)])
    assert tl.route(v, room) == {"seed": {21: v.faults}}
    for n in (1, 2):
        (room / "attempts" / f"T21_fail{n}.mp4").write_bytes(b"x")
    assert tl.route(v, room) == {}


def test_an_early_clone_head_cut_with_no_head_falls_back_to_a_seed(tmp_path):
    f = {8: [Fault(kind="clones", where="T08", evidence={"t": 0.1})]}
    assert tl.uncut_clones({"head_cut": f}, written=[]) == f
    assert tl.uncut_clones({"head_cut": f}, written=[8]) == {}
