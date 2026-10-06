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
