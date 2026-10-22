"""A block whose plan camera names no light says the setup's source in a whole sentence, once (wave-2 review of A17).

`block_light` wrapped the style-line fragment in "The light is ...": on ep01's own setups that wrote "The light is
lamp, shadows.", "The light is sun from the left, shadow." and "The light is candle, black shadows." -- broken, and
the black said again beside the style line's.  On T07 the at-rest fill, freed of the scope tail (A18), added
"..., shining with lamplight." beside the block's "corner lamp light comes from the upper RIGHT": the light said
twice in the block, which the census's `light_twice` (style line only) could not see.  Now the block's sentence is
the source and its side ("The lamp from the left lights the scene."), no black; a fill clause that says a light
effect is dropped when the block already says its light; and the census counts a block that says it twice.
This file also pins the wave-2 helpers that had no test: follow_marks, stray_commas, clock_of, panel_faults."""
from __future__ import annotations

import shot_framework_fixtures as sf
from scripts.episode import craft_lint as cl
from studio import episode_ref_official as ro, grid_lint, house_style as hs
from studio.episode_spec import Setup

LAMP = Setup(described="A by-street at night; a gas lamp burns at the kerb on the LEFT, black shadows", outdoors=True)


def seg(setup=LAMP, **kw) -> dict:
    return {"setup": setup, "time": "", "camera": "", "at_rest": "", **kw}


def test_the_block_light_is_a_whole_sentence_with_no_black():
    with sf.adopted():
        said = ro.block_light(seg())
    assert said.startswith("The ") and said.endswith(" the scene.")
    assert "The light is" not in said and not hs.BLACKS.search(said) and "," not in said


def test_a_shot_at_another_hour_gets_no_setup_light():
    assert ro.block_light(seg(time="day")) == ""


FLOOR = ("the focus of the picture is his black boots striding on the wet cobbles at the RIGHT third, the hem "
         "of the knee-length black coat above them.")


def test_a_lit_block_fills_with_no_second_light():
    rest = f"{FLOOR} The iron grating sits at the CENTRE, shining with lamplight. The cross street opens at the LEFT"
    said = " ".join(ro.detail(seg(camera="on the cobbles; the corner lamp light comes from the upper RIGHT",
                                  at_rest=rest), 80))
    assert "shining with lamplight" not in said and "sits at the CENTRE. The cross street" in said


def test_the_authors_floor_keeps_its_light():
    rest = "the grating sits at the CENTRE, shining with lamplight"
    said = " ".join(ro.detail(seg(camera="on the cobbles; the corner lamp light comes from the upper RIGHT",
                                  at_rest=rest), 80))
    assert "shining with lamplight" in said


def test_an_unlit_block_fills_with_its_light():
    rest = f"{FLOOR} The iron grating sits at the CENTRE, shining with lamplight."
    said = " ".join(ro.detail(seg(setup=None, camera="on the cobbles", at_rest=rest), 80))
    assert "shining with lamplight" in said


def test_t07_says_its_light_once():
    said = sf.detailed(sf.take_prompt(7))
    assert "shining with lamplight" not in said and "BOTTOM half. The mouth" in said
    assert cl.light_twice(said) == 0


def test_follow_marks_never_stamps_the_last_second():
    assert ro.follow_marks(0, 5, 2, line_end=5) == [4]
    assert ro.follow_marks(3, 4, 1, line_end=9) == [3]
    assert ro.follow_marks(4, 4, 1, line_end=9) == []


def test_stray_commas_skip_the_spoken_line():
    assert ro.stray_commas("He walks,, east .,") == [",,", ".,"]
    assert ro.stray_commas('He says <d>[English] "Well,, sir."</d> and goes.') == []


def test_clock_of_reads_night_before_dusk():
    assert hs.clock_of("at dusk, the moon up") == "night"
    assert hs.clock_of("at dusk") == "dusk" and hs.clock_of("a grey street") == ""


def test_panel_faults_reads_one_panel_at_a_time():
    twin = "<image1> and <image2> stand. The two men are two different individuals: each one has his own face."
    focus = "THE FOCUS OF THE PICTURE IS the black fist at the CENTRE. Framing: head and shoulders fill the centre."
    assert [f.split()[0] for f in grid_lint.panel_faults(f"{twin}\n\n{focus}")] == ["TWIN", "FOCUS"]
    assert grid_lint.panel_faults("<image1> stands alone.") == []
