"""The prompt rules learned on ep01-ep03, checked before the GPU runs."""
from studio.prompt_rules import (check_shot, group_once, kept_anchor,
                                 last_clause_exits, move_variety, push_in)


def test_a_numbered_group_with_one_description_is_caught():
    assert group_once("three workmen in collarless shirts and moleskin trousers digging")
    assert group_once("a dense crowd pressing forward along the rim")
    assert group_once("a stream of people in straw hats and light summer dresses")


def test_individually_named_figures_pass():
    assert not group_once("a bare-armed workman in braces drives a spade, a stout man in a "
                          "red waistcoat swings a pickaxe, a thin grey-haired man stoops")
    assert not group_once("heads and shoulders of onlookers above the sand edge, each turned "
                          "a different way")


def test_a_push_in_is_caught():
    assert push_in("The camera pushes in toward Ogilvy's face")
    assert not push_in("The camera holds a locked-off frame; he leans in")


def test_a_last_clause_that_leaves_the_frame_is_caught():
    assert last_clause_exits("The camera holds; he flicks the reins and the horse pulls the "
                             "cart on along the road.")
    assert last_clause_exits("inky fingers point away down the road")
    assert not last_clause_exits("The camera holds; he lifts one finger and speaks; he turns "
                                 "his head toward the lens.")


def test_a_pan_that_keeps_a_subject_is_an_orbit_request():
    assert kept_anchor("The camera pans right, travelling a finger's breadth; the eyepiece "
                       "keeps the left third")
    assert not kept_anchor("The camera pans from the green lamp across to the French windows")


def test_move_variety_counts_distinct_moves_and_repeats():
    moves = ["holds", "holds", "pans", "tracks", "tilts up"]
    out = move_variety(moves)
    assert out["distinct"] == 4 and out["back_to_back"] == 1
    assert out["most_used_share"] == 0.4


def test_check_shot_reports_every_fault_by_name():
    bad = check_shot({"index": 3, "size": "wide",
                      "frame": "three workmen in collarless shirts digging",
                      "motion": "The camera pushes in on them; they walk away down the road."})
    assert set(bad) == {"group_once", "push_in", "exit_clause"}


def test_men_inside_a_word_is_not_a_group():
    """`two immense eyes` matched `two immen`+`men` before the noun list was
    word-bounded: WotW ep04's two Martian shots flagged `group_once` for a
    phrase with no group in it."""
    assert not group_once("two immense glossy black eyes above a lipless mouth")
    assert group_once("three workmen in collarless shirts digging")


def test_the_gerund_keep_clause_is_the_same_orbit_request():
    """ep04: the Singularity spec's 'keeping X in frame' dodged the lint and
    brought ep01's orbit back as churn, blur and late reframes."""
    assert kept_anchor("The camera tracks alongside the Narrator at a running pace, "
                       "keeping him in the centre of frame with the pines at the right")
    assert kept_anchor("The camera pans right with small amplitude from a pine branch across "
                       "to the shopman, keeping his head in the centre of frame")
    assert kept_anchor("The camera pulls out from the screw, keeping the bright seam in the "
                       "upper centre of frame")


def test_a_static_shot_may_say_what_it_frames():
    assert not kept_anchor("The camera holds a static shot on the Narrator; he drags a breath")
    assert not kept_anchor("The camera pans from the lamp across to the window")


def test_a_group_noun_needs_its_own_word_boundary():
    """ep05: "the linen cracks over" flagged `group_once`, because the second
    branch of NUMBERED ended on `line` with no \b -- the same fault ep04 fixed
    on the leading side of the alternation ("two immen" -> "men")."""
    assert not group_once("the pole swings over and the linen runs out flat")
    assert not group_once("he crosses the lines of the ledger")
    assert group_once("the line of people pressing forward")
