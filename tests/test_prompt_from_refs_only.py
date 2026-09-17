"""A take prompt built from the PLATE and the CAST CARDS, with no storyboard cell.

The paid drawer that makes the storyboard sheets ran out of credits on
2026-09-17 with episode 14 written, cast, recorded and plated. This is the
experiment the owner asked for: send the references alone and see what the
render does. It is NOT the normal path -- a cell is frame zero, and four DQ
rows (coherence off-board, last-vs-cell, cut-landing, foreign) measure against
it -- so the prompt must be honest about what it stages: no picture may be
called a first frame, nothing may cite a picture the graph never staged, and
every staged picture still needs its definition (L11 counts them).
"""
import pytest

from studio import episode_ref_official as ro
from studio.episode_spec import Line, Setup, Shot

SHOTS = [Shot(index=11, section="spike", setup="lab", size="close", faces=[],
              path=0.3,
              frame="Close on the test-tube in Sherlock Holmes's fingers at the bench, the tall window "
                    "grey behind it, the retort at his elbow.",
              camera="at the bench level with his hands, an arm's length from the tube, a 90mm lens. The "
                     "window light comes from the LEFT onto the glass and leaves the bench black",
              at_rest="The test-tube stands at the CENTRE of the frame the height of the middle third.",
              motion="The camera tilts down across the whole shot, travelling a finger's breadth; the tube "
                     "keeps the frame's centre; the liquid turns crimson; his thumb rolls the tube a "
                     "finger's breadth."),
         Shot(index=12, section="reaction", setup="lab", size="medium_close", faces=["sherlock_holmes"],
              path=0.5,
              frame="Medium close of Sherlock Holmes at the bench, the lean pale face lit from the window "
                    "at the left, the retort at his elbow.",
              camera="across the bench level with his eyes, two long strides from him, a 50mm lens. The "
                     "window light comes from the LEFT onto his face and leaves the wall behind him black",
              at_rest="Sherlock Holmes's head and shoulders fill the CENTRE of the frame, his head a third "
                      "of the frame's height.",
              motion="The camera pans right across the whole shot, travelling a finger's breadth; the black "
                     "wall keeps the frame behind him; his brows lift on the words; his hand sets the tube "
                     "down on the bench.")]
PLACED = [{"index": 11, "t_start": 92.96, "seconds": 4.25}, {"index": 12, "t_start": 97.21, "seconds": 3.71}]
LINES = [Line(index=17, kind="narration", speaker="john_watson", text="He looked at my hands.", shot=11),
         Line(index=18, kind="dialogue", speaker="sherlock_holmes", text="You have been in Afghanistan.",
              shot=12)]
AT = {17: (93.21, 3.75), 18: (97.46, 3.19)}
PHYS = {"sherlock_holmes": "A man in his late twenties, excessively lean, a pale indoor complexion."}
FRAMES = 199
LAB = "The chemical laboratory of Saint Bartholomew's Hospital, 1881, a tall window over the bench."


def built(**kw):
    kw = {"faces": ["sherlock_holmes"], "physical": PHYS, "described": LAB, "narrator": "john_watson",
          "refs": 2, "has_plate": True, "cells_staged": False, "check_lint": False, **kw}
    return ro.build(SHOTS, PLACED, LINES, AT, FRAMES, **kw)


def test_numbering_stops_at_the_plate_when_no_cell_is_staged():
    plate, cells, last, after = ro.picture_numbers(2, 3, [], has_plate=True, has_cells=False)
    assert plate == 3 and last == {}
    assert cells == {0: None, 1: None, 2: None}
    assert after == 3, "the slot after the last picture is the plate's own"


def test_numbering_is_unchanged_when_cells_are_staged():
    plate, cells, last, after = ro.picture_numbers(2, 3, [], has_plate=True)
    assert plate == 3 and cells == {0: 4, 1: 5, 2: 6} and after == 7


def test_no_picture_is_called_a_first_frame():
    text = built()
    assert "first frame of [Shot" not in text
    assert "begins from <Picture" not in text
    assert "first frame): fully_preserved" not in text


def test_every_staged_picture_is_still_defined_and_no_other_is_cited():
    text = built()
    cited = {int(n) for n in __import__("re").findall(r"<Picture (\d+)>", text)}
    assert cited == {1, 2}, "one cast card and the plate, and nothing else"


def test_the_shot_says_where_it_opens_in_words():
    body = built()
    body = body[body.index("detailed_description:"):]
    assert "The shot opens on a close shot of" in body
    assert "At 00:04 the shot cuts to a medium close shot of <Subject 1>" in body


def test_the_summary_gives_each_shot_its_seconds_without_a_picture():
    text = built()
    assert "[Shot 1] runs from 00:00 to 00:04" in text
    assert "[Shot 2] runs from 00:04 to 00:08" in text


def test_the_picture_and_task_type_lints_pass_on_a_refs_only_prompt():
    """The whole point: L11 counts defined pictures against staged references and
    refuses a citation the graph never staged; L13 names the task types in play.
    (The two-segment fixture is too short for L14's 150 words a block, which is
    why the repo's other builder tests pass check_lint=False as well.)"""
    with pytest.raises(ValueError) as caught:
        built(check_lint=True)
    said = str(caught.value)
    assert "L11" not in said and "L13" not in said, said
    assert "L14 LENGTH" in said, said


def test_a_cell_prompt_still_says_it_begins_from_its_picture():
    text = ro.build(SHOTS, PLACED, LINES, AT, FRAMES, faces=["sherlock_holmes"], physical=PHYS,
                    described=LAB, narrator="john_watson", check_lint=False)
    assert "is the first frame of [Shot 1]" in text and "begins from <Picture" in text
