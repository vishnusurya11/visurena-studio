"""The grid prompt puts the picture's subject first, and a single picture
never hears the words storyboard, grid or panel.

Audit Tier 3, item 19, measured 2026-09-22 on ep09's grid prompts: 626-1472
words, and the subject block started 31-62% of the way in, behind layout, 70
words of style, 150 of place and a 110-word identity block cut off at 600
characters ("Straw boater w --"). A one-picture prompt said "storyboard",
"grid" or "panel" 13 times; the geometry docstring had already measured that
the model obeys those words over the arithmetic.

v2 orders it: one layout line, the panels subject-first, one binding line per
person, the place, the style. It stays beside v1 until a same-seed render of
ep09 grids decides between them.
"""
from studio.storyboard_grid import grid_prompt, grid_prompt_v2, worn_items

PLACE = ([3], "the walled lawn on the crest of Maybury Hill with the valley below it on fire")
CAST = [{"ref": 1, "name": "NARRATOR", "entity": "n", "wear": "x" * 900, "against": "a"},
        {"ref": 2, "name": "WIFE", "entity": "w", "wear": "y" * 900, "against": "b"}]


def panel(body, who=(), extras=0, size="MEDIUM"):
    return {"size": size, "body": body, "cut": "the panel cuts at the waist", "who": list(who),
            "extras": extras}


def test_the_first_panel_comes_before_the_cast_the_place_and_the_style():
    text = grid_prompt_v2([panel("THE HUSSAR SHOUTS", ["NARRATOR"])], 1, 1, PLACE, CAST[:1], 3)
    at = text.index("THE HUSSAR SHOUTS")
    assert at < text.index("NARRATOR is the person") and at < text.index("Maybury Hill")
    assert at < text.lower().index("art style")


def test_a_single_picture_never_says_storyboard_grid_or_panel():
    text = grid_prompt_v2([panel("a close-up of a face")], 1, 1, PLACE, [], 3).lower()
    for word in ("storyboard", "grid", "panel"):
        assert word not in text, word


def test_several_panels_are_laid_out_in_one_line_and_numbered():
    text = grid_prompt_v2([panel("A"), panel("B"), panel("C"), panel("D")], 2, 2, PLACE, [], 3)
    assert text.splitlines()[0].count("2") >= 2
    assert "PANEL 1" in text and "PANEL 4" in text


def test_no_description_is_cut_off_mid_word():
    text = grid_prompt_v2([panel("two at tea", ["NARRATOR", "WIFE"])], 1, 1, PLACE, CAST, 3)
    assert "x" * 900 not in text and "--" not in text


def test_a_panel_with_declared_extras_says_so_and_is_not_called_empty():
    text = grid_prompt_v2([panel("a soldier with a flag", extras=1)], 1, 1, PLACE, [], 3)
    assert "place alone" not in text and "1 unnamed" in text


def test_a_panel_with_nobody_is_the_place_alone():
    assert "place alone" in grid_prompt_v2([panel("a haze of smoke")], 1, 1, PLACE, [], 3)


def test_v2_is_shorter_than_v1_for_the_same_grid():
    shots = [panel(f"body {i} " * 20, ["NARRATOR"]) for i in range(4)]
    v1 = grid_prompt(shots, 2, 2, PLACE, CAST[:1], style="DRAWN IN THE STYLE OF <image3>")
    v2 = grid_prompt_v2(shots, 2, 2, PLACE, CAST[:1], 3)
    assert len(v2.split()) < len(v1.split())


WIFE = ("Woman of 29, slim. Oval face, wide hazel eyes. Wearing: Cream cotton blouse with high "
        "collar and pin-tucked front, sage-green wool skirt to the ankle. Low brown boots. Paisley "
        "cashmere shawl in rust and cream folded over one arm. Small sage-green felt toque trimmed "
        "with a cream ostrich tip. Grey kid gloves. A cameo brooch.")


def test_the_binding_line_carries_the_worn_items_whole_and_at_most_five():
    """ep09 A/B, lawn 2x2: bound by name alone, the wife lost her shawl in both
    panels she was in; v1's cut-off identity block had kept it."""
    cast = [{"ref": 2, "name": "WIFE", "entity": "w", "wear": WIFE, "against": "b"}]
    text = grid_prompt_v2([panel("she stands", ["WIFE"])], 1, 1, PLACE, cast, 3)
    line = next(x for x in text.split("\n\n") if x.startswith("WIFE is"))
    assert "Paisley cashmere shawl in rust and cream folded over one arm" in line
    assert "Cream cotton blouse with high collar and pin-tucked front" in line
    assert "sage-green wool skirt to the ankle" in line      # after a comma; ep09 v2b dropped it
    assert "hazel" not in line and "cameo" not in line       # the face is the sheet's; five items


def test_a_colon_introduces_parts_of_one_item_not_new_items():
    wear = ("Wearing: Mid-grey tweed lounge suit: single-breasted jacket, matching waistcoat. "
            "White shirt, dark green tie. Straw boater.")
    assert worn_items(wear) == ["Mid-grey tweed lounge suit", "White shirt", "dark green tie",
                                "Straw boater"]


NARR = ("Man of 34. Wearing: Mid-grey tweed lounge suit. White shirt. Straw boater with a black "
        "band.")


def test_a_bareheaded_person_is_not_bound_to_wear_a_hat():
    """ep09 shot 11: the plan put the boater in his hand, the binding line put
    it on his head, and the panel drew both."""
    cast = [{"ref": 1, "name": "NARRATOR", "entity": "n", "wear": NARR, "against": "a"}]
    text = grid_prompt_v2([panel("bareheaded in the heather, his boater in one hand", ["NARRATOR"])],
                          1, 1, PLACE, cast, 3)
    line = next(x for x in text.split("\n\n") if x.startswith("NARRATOR is"))
    assert "boater" not in line and "Mid-grey tweed lounge suit" in line


def test_a_person_with_a_hat_on_keeps_it():
    cast = [{"ref": 1, "name": "NARRATOR", "entity": "n", "wear": NARR, "against": "a"}]
    text = grid_prompt_v2([panel("in the heather", ["NARRATOR"])], 1, 1, PLACE, cast, 3)
    assert "Straw boater with a black band" in text


def test_a_staged_prop_is_bound_as_an_object_not_a_person():
    """ep10's tripod: without its sheet in the grid, every panel draws the
    machine from words and no two agree (ep10 prep audit, 2026-09-23)."""
    text = grid_prompt_v2([panel("a tripod striding over the pines")], 1, 1, PLACE, [], 3,
                          props=[{"ref": 1, "name": "the Martian fighting-machine"}])
    assert "the Martian fighting-machine is the object in <image1>" in text
    assert "is the person in <image1>" not in text


HOUSE = ("the front of a pale house at night: rows of lit windows, a gravel drive, two gate piers; "
         "the light is lamplight from the open door, so the gravel reads warm")


def test_a_grid_of_tight_shots_names_the_place_briefly():
    """ep10 shot 1, a medium close on the wife: a 100-word description of the
    whole house front drew the house every time, the wife 0.02-0.04 of the frame
    across five seeds. The staged picture carries the place; a tight grid gets
    its name and its light only."""
    text = grid_prompt_v2([panel("her face", ["WIFE"], size="MEDIUM CLOSE")], 1, 1, ([2], HOUSE), [], 3)
    assert "gate piers" not in text and "the front of a pale house at night" in text
    assert "the light is lamplight from the open door" in text


def test_a_grid_with_a_wide_keeps_the_whole_place():
    text = grid_prompt_v2([panel("the house", size="WIDE")], 1, 1, ([2], HOUSE), [], 3)
    assert "gate piers" in text
