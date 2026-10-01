"""Five-expert debate 2026-09-30 (docs/audit/2026-09-30_rounds_debate.md): 9 of
11 audited take refusals were false alarms costing ~4 GPU-h.  Four fixes:
the mustache check reads each face's own row; a declared crowd is not a clone
farm; staged print is not lettering; dusk is daylight to the look floor."""
import re

from studio import panel_content as pc, take_look


def seen(**kw):
    return pc.Seen(**{"people": 0, "lookalikes": 0, "text": False, "hour": "day",
                      "landform": "flat", "subjects": [], **kw})


def test_a_constables_required_moustache_is_not_georges_fault():
    """T19: George's row says clean-shaven; the police row demands 'full drooping
    moustaches'.  Concatenated, the check fired every round on regulation hair."""
    rows = ["A lean clean-shaven man of twenty-two.",
            "Weather-reddened English faces with full drooping moustaches on most."]
    got = pc.contradictions(seen(subjects=["man", "moustache", "helmet"]), rows)
    assert got == []
    alone = pc.contradictions(seen(subjects=["man", "moustache"]), ["A lean clean-shaven man."])
    assert alone == ["moustache on a clean-shaven character"]
    joined = pc.contradictions(seen(subjects=["moustache"]), " ".join(rows))
    assert joined == []                                     # a single string is one row per face? no -- backward path stays lenient


def test_a_declared_crowd_is_not_a_clone_farm():
    """T03/T12: the plan's crowd prose orders a classroom of students; era dress
    reads as 'copies'.  With a crowd declared, only 3+ lookalikes is a fault."""
    assert not pc.people_fault(seen(people=15, lookalikes=2), planned=1, crowd=True)
    assert pc.people_fault(seen(people=15, lookalikes=3), planned=1, crowd=True)
    assert pc.people_fault(seen(people=3, lookalikes=1), planned=2, crowd=False)
    assert pc.people_fault(seen(people=4, lookalikes=0), planned=2, crowd=False)
    assert not pc.people_fault(seen(people=2, lookalikes=0), planned=2, crowd=False)


def test_staged_print_expects_text_at_any_size_but_wide():
    """T05 (medium, 'facing the dark Woking board'), T13 (insert on a map-shop
    window), T18 ('newspaper and examination notes under the lamp'): the plan
    stages the print; the lettering row may not bill the renderer for it."""
    assert pc.lettering_expected("facing the dark Woking board", "medium")
    assert pc.lettering_expected("Surrey maps fastened to the glass, damp pink sheets", "insert")
    assert pc.lettering_expected("newspaper and examination notes under the paraffin lamp", "medium")
    assert not pc.lettering_expected("a papered wall and a poster far off", "wide")   # ep07's lesson stands
    assert not pc.lettering_expected("the brother stands in the doorway", "medium")


def test_dusk_is_daylight_to_the_look_floor():
    """T10: a rosy dusk crane over bright water read p5 22-26 on every seed; the
    no-floor wall was calibrated on Sherlock interiors and DAY_WORDS lacked dusk."""
    assert take_look.is_daylight("a dusk sky over the river, rosy to the west", True)
    assert take_look.is_daylight("dawn light over the street", True)
    assert not take_look.is_daylight("a lamp is the only light in the parlour", False)
    assert not take_look.is_daylight("moonlight, the lantern the only light", True)


def test_drifted_reads_one_row_per_face():
    """ep15 (2026-10-01): the beard fix made the checkers pass a LIST of rows
    and drifted() crashed on .lower(); a hair drifts only when NO row allows it."""
    from studio.panel_content import Seen
    from studio.take_content import drifted
    seen = Seen(people=2, lookalikes=0, hour="day", landform="", text=False,
                subjects=["a grey hair man", "a woman"])
    assert drifted(seen, ["thick chestnut-auburn hair", "grey hair, lined face"]) == []
    assert drifted(seen, ["thick chestnut-auburn hair"]) != []
    assert drifted(seen, "grey hair") == []
    assert drifted(seen, []) == []
