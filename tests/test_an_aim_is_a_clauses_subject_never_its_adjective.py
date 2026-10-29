"""Jekyll ep05 shot 15 froze twice in the repair: its camera line read "The camera tracks beside the
small;" -- `move_rebalance.cell_aims` took `head_noun` of a whole at_rest clause ("the red baize door
stands small at the TOP CENTRE" -> "small"), and every later cure aimed the camera at an adjective.
An aim is kept only where the clause holds it as a noun, after a determiner."""
from studio import move_rebalance as mr

SHOT_15 = {"at_rest": "THE FOCUS OF THE PICTURE IS the doctor at the RIGHT third, his hands rising to his face "
                      "beside the lamp. The lawyer sits at the LEFT third; the red baize door stands small at "
                      "the TOP CENTRE.",
           "frame": "Medium two-shot of the doctor and the lawyer at the table by the lamp.", "motion": "The camera holds"}


def test_a_predicate_adjective_is_not_an_aim():
    assert not mr.determined("small", "the red baize door stands small at the TOP CENTRE")


def test_a_noun_after_its_determiner_is():
    assert mr.determined("door", "the red baize door stands small at the TOP CENTRE")
    assert mr.determined("lamp", "his hands rising to his face beside the brass lamp")


def test_shot_15_never_aims_at_small():
    assert "small" not in mr.cell_aims(SHOT_15)
