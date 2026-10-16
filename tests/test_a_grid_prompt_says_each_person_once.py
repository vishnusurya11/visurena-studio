"""Jekyll ep01 grid audit (docs/audit/2026-10-15_jekyll_ep01_ref_audit/02_prompts.md,
grid classes G1, G3-G6, G8).  Owner 2026-10-15: a plan epithet ("the lawyer",
"the little man", "the girl") ALWAYS binds to its staged slot, and a person is
described once per prompt.  $0: pure text."""
from __future__ import annotations

from studio import storyboard_grid as sg


# ---- G1: only grid geometry becomes "picture" ------------------------------------

def test_a_single_picture_keeps_the_doors_panels():
    said = sg._one_picture("its panels streaked black; a match on the panels of the door; "
                           "the blistered door panels fill the background; the blistered brown panels")
    assert said.count("panels") == 4 and "picture" not in said


def test_a_single_picture_renames_the_grid_cell():
    said = sg._one_picture("The panel contains the horse. Framing: the panel cuts at the shoulders; "
                           "every panel is set in it; a storyboard")
    assert "panel" not in said.lower() and "storyboard" not in said
    assert said.startswith("The picture contains")


# ---- G3: the staged person is a man, a woman, a girl, a boy -----------------------

def test_a_staged_girl_is_the_girl_in_her_slot():
    girl = {"name": "CHILD", "display": "the child", "ref": 1, "noun": "girl", "aliases": ["the girl"]}
    assert sg.called([girl])["CHILD"] == "the girl in <image1>"
    assert sg._binding({**girl, "clothes": ["grey bonnet"]}).startswith("The girl in <image1> wears: grey bonnet.")


def test_a_counted_group_of_men_says_his_own():
    said = sg.varied_group("two men walk on")
    assert "his own face" in said and "his or her" not in said
    assert "her own face" in sg.varied_group("three women wait")


# ---- G4: epithets bind to the slot; a slot carries no parenthetical ---------------

LAWYER = {"name": "MR. UTTERSON", "display": "Mr. Utterson", "ref": 1, "noun": "man", "aliases": ["the lawyer"]}
ENFIELD = {"name": "MR. RICHARD ENFIELD", "display": "Mr. Enfield", "ref": 2, "noun": "man",
           "aliases": ["mr. enfield"]}


def test_an_epithet_becomes_its_slot_and_loses_its_parenthetical():
    body = ("as the lawyer (long, gaunt face, black bowler hat) and Mr. Enfield (light-brown top hat) stop; "
            "over the lawyer's near shoulder")
    said = sg._slotted(body, [LAWYER, ENFIELD])
    assert "lawyer" not in said and "Enfield" not in said and "(" not in said
    assert "the man in <image1> and the man in <image2> stop" in said
    assert "the man in <image1>'s near shoulder" in said


def test_an_unstaged_epithet_keeps_its_words_without_the_parenthetical():
    hyde = {"name": "EDWARD HYDE", "display": "Mr. Hyde", "ref": None, "noun": "man",
            "aliases": ["the little man"], "line": "a man with coarse black hair"}
    said = sg._slotted("the little man (soft black felt hat, small, slight frame) walks", [hyde])
    assert said == "the little man walks"


def test_an_unstaged_person_is_said_by_his_layers_line_once():
    hyde = {"name": "EDWARD HYDE", "ref": None, "noun": "man", "line": "a man with coarse black hair"}
    shots = [{"who": ["EDWARD HYDE"], "body": "a"}, {"who": ["EDWARD HYDE"], "body": "b"}]
    said = sg._unnamed(shots, [hyde])
    assert said[0]["who"] == ["a man with coarse black hair"]
    assert said[1]["who"] == ["the same man again"]


# ---- G5: "wears" is clothes ------------------------------------------------------

def test_clothes_come_from_headwear_and_top_without_physique():
    hyde = sg.clothes_of({"headwear": "soft black felt wideawake hat, wide floppy brim", "hair": "black hair",
                          "top": "respectable, well-fitting clothing on a small, slight, narrow-shouldered "
                                 "frame; lean, corded, knuckly hands of dusky pallor"})
    assert hyde == ["soft black felt wideawake hat, wide floppy brim", "respectable, well-fitting clothing"]
    enfield = sg.clothes_of({"headwear": "", "top": "fashionable dark frock coat; compact, upright, "
                                                    "well-dressed man about town, broad-shouldered, heavy jaw"})
    assert enfield == ["fashionable dark frock coat"]


def test_worn_items_drop_physique():
    items = sg.worn_items("Wearing: fashionable dark frock coat; compact, upright, broad-shouldered, heavy jaw")
    assert items == ["fashionable dark frock coat"]


# ---- G6: the framing follows the cell ----------------------------------------------

def test_an_insert_of_hands_is_filled_by_the_hands():
    said = sg.framing("insert", True, "Insert of the bony hands of the man in <image1> clasped behind his back")
    assert "the hands" in said and "figure" not in said


def test_an_insert_of_a_lock_is_filled_by_the_lock():
    said = sg.framing("insert", True, "Insert of the lock of the blistered door as he thrusts a key into it")
    assert "the lock" in said and "figure" not in said


def test_an_over_the_shoulder_full_shot_is_not_one_whole_figure():
    said = sg.framing("full", True, "Full shot over the shoulder of the man in <image1> at the near kerb")
    assert "the whole figure" not in said and "shoulder" in said


def test_an_ordinary_full_shot_keeps_its_cut():
    assert sg.framing("full", True, "Full shot of the corner") == sg.cut_clause("full", True)


def test_a_hands_insert_binds_only_the_hands():
    p = {"name": "U", "ref": 1, "noun": "man", "clothes": ["black bowler hat", "dark suit"]}
    said = sg._binding(p, hands=True)
    assert "hands" in said and "exactly once in each picture" not in said and "bowler" not in said


def test_an_insert_who_line_names_the_hands():
    p = {"name": "U", "ref": 1, "noun": "man"}
    said = sg._unnamed([{"who": ["U"], "body": "x", "size": "INSERT"}], [p])
    assert said[0]["who"] == ["the hands of the man in <image1>"]


# ---- G8: plates and papers are blank ------------------------------------------------

def test_brass_plates_are_plain_and_a_blank_sentence_is_said():
    text = sg.grid_prompt_v2([{"size": "WIDE", "body": "a polished brass plate glints", "cut": "c", "who": []}],
                             1, 1, ([1], "shop fronts with polished brass plates"), [], 1)
    assert "plain polished brass plates" in text and "plain polished brass plate glints" in text
    assert sg.UNWRITTEN in text and sg.BLANK in text
    assert sg.BLANK == "Every plate, sign and paper in the picture is plain and blank, unlettered."


def test_no_blank_sentence_without_bait():
    text = sg.grid_prompt_v2([{"size": "WIDE", "body": "a heath", "cut": "c", "who": []}], 1, 1, ([1], "a heath"), [], 1)
    assert sg.BLANK not in text


# ---- found reading the rebuilt Jekyll ep01 prompts (2026-10-15) --------------------

def test_plain_plates_never_doubles_and_reads_a_hyphenated_polish():
    assert sg.plain_plates("well-polished brass plates") == "plain well-polished brass plates"
    assert sg.plain_plates("plain well-polished brass plates") == "plain well-polished brass plates"
    assert sg.plain_plates("plain plain polished brass plates") == "plain polished brass plates"


def test_a_common_noun_name_is_not_bound():
    girl = {"name": "CHILD", "display": "the child", "ref": 2, "noun": "girl", "aliases": ["the girl"]}
    said = sg._slotted("the girl, a small child, half his height", [girl])
    assert said == "The girl in <image2>, a small child, half his height"   # a body opens a sentence


def test_an_unstaged_name_is_said_in_plain_words():
    enfield = {"name": "MR. RICHARD ENFIELD", "display": "Mr. Enfield", "ref": None, "noun": "man",
               "plain": "the man in the light-brown top hat", "aliases": ["mr. enfield"]}
    said = sg._slotted("while Mr. Enfield (light-brown top hat) starts forward", [enfield])
    assert said == "while the man in the light-brown top hat starts forward"


def test_a_slot_that_opens_a_sentence_is_capitalised():
    said = sg._slotted("at the door. the lawyer stands", [LAWYER])
    assert said == "at the door. The man in <image1> stands"


def test_hands_wear_their_coat_and_gloves_only():
    p = {"name": "E", "ref": 2, "noun": "man", "clothes": [
        "light-brown top hat", "mid-grey long frock coat with black lapels, cream waistcoat, black gloves, black cane"]}
    said = sg._binding(p, hands=True)
    assert said == ("Only the hands of the man in <image2> are in the picture, in the sleeves of his "
                    "mid-grey long frock coat with black lapels and his black gloves, as drawn on <image2>.")
    hyde = {"name": "H", "ref": 1, "noun": "man", "clothes": ["felt hat", "knee-length black coat, white shirt"]}
    assert "his knee-length black coat," in sg._binding(hyde, hands=True)
