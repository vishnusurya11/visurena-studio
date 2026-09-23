"""Who may be in a panel is declared by the plan, never guessed from its prose.

MEASURED 2026-09-22 (audit items 1 and 2). The panel runner decided a shot
was a CROWD by searching its prose for people-words with no word boundaries,
so "compartment" matched `men`, "a hand's breadth" matched `hand`, and every
cast row copied into a plan ("a spare quick man of forty") matched `man`.
A crowd shot stands the people check down, so it was off on about 80% of
panels, and the narrator walked into panels that plan nobody.

Now a crowd is what the SETUP declares, and any other unnamed person is a
number the SHOT declares (`extras`).

And a planned face missing at a MEDIUM is a fault too. Measured on ep06-09:
of 16 medium panels with planned faces the detector found none on 3 -- ep09
12 (an empty garden planned with two people), ep07 13 (the stacked
two-picture panel that went public as ep07 S14), and ep07 9, which is right:
its plan puts the camera "past the near shoulder of the narrator". A back
view the plan asks for is not a missing face.
"""
from studio.episode_spec import Shot
from studio.panel_dq import back_view, verdict


def clean(**kw):
    base = dict(faces=[], planned=0, sharp=1.0, ink=0.0, tiled=0.0)
    base.update(kw)
    return verdict(**base)


# ---- extras ------------------------------------------------------------------

def real_shot() -> dict:
    """A shot as a real plan writes it -- the fixture comes from the contract."""
    import json
    from pathlib import Path
    plan = (Path(__file__).resolve().parents[1] / "library" /
            "20260827135508_the-war-of-the-worlds" / "episodes" / "ep08" / "plan.json")
    shot = json.loads(plan.read_text(encoding="utf-8"))["shots"][0]
    shot.pop("extras", None)
    return shot


def test_a_shot_declares_its_unnamed_people_and_defaults_to_none():
    assert Shot.model_validate(real_shot()).extras == 0
    assert Shot.model_validate({**real_shot(), "extras": 2}).extras == 2


def test_an_undeclared_face_is_a_fault():
    assert "people" in clean(faces=[0.3], planned=0, size="medium")["flags"]


def test_a_declared_extra_is_not():
    assert "people" not in clean(faces=[0.3], planned=0, extras=1, size="medium")["flags"]


def test_one_more_than_declared_is():
    assert "people" in clean(faces=[0.3, 0.3], planned=0, extras=1, size="medium")["flags"]


def test_a_crowd_the_setup_declares_has_no_count():
    assert "people" not in clean(faces=[0.3] * 6, planned=1, crowd=True, size="wide")["flags"]


# ---- missing at a medium ------------------------------------------------------

def test_a_medium_that_plans_a_face_and_has_none_is_a_fault():
    assert "missing" in clean(planned=2, size="medium")["flags"]


def test_a_back_view_the_plan_asks_for_is_not_missing():
    got = clean(planned=1, size="medium",
                prose="Medium past the near shoulder of the narrator as a workman comes up")
    assert "missing" not in got["flags"]


def test_a_wide_is_still_exempt():
    assert "missing" not in clean(planned=1, size="wide")["flags"]


def test_back_view_reads_the_phrases_a_plan_uses():
    for said in ("past the near shoulder of him", "seen from behind", "with his back to us",
                 "over the shoulder of the wife", "from behind her"):
        assert back_view(said), said
    for said in ("a hand's breadth from his shoulder", "her shoulders square", "he looks back"):
        assert not back_view(said), said
