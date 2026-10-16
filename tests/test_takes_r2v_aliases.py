"""takes_r2v hands the builder the plan's epithets and the book's drawn look (Jekyll ep01 iter5)."""
import sys
from pathlib import Path
from types import SimpleNamespace as NS

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "episode"))
import takes_r2v  # noqa: E402
from studio import episode_ref_official as ro  # noqa: E402


def shot(frame, motion=""):
    return NS(frame=frame, motion=motion, at_rest="", end="", camera="", changed="", cuts=[])


ROWS = [{"kind": "character", "entity_id": "gabriel_john_utterson",
         "physical": "Lank grey hair; black bowler hat with a pale grey band. A lean, long man.",
         "wardrobe": {"outdoor": "long black double-breasted overcoat"}},
        {"kind": "character", "entity_id": "edward_hyde",
         "physical": "Coarse black hair; soft black felt wideawake hat. Lean, corded, knuckly pale hands.",
         "wardrobe": {}}]


def test_plan_texts_reads_every_shot_field():
    ep = NS(shots=[shot("a wide of the lawyer (black bowler hat)", "the little man (corded) walks")])
    assert "the little man (corded) walks" in takes_r2v.plan_texts(ep)


def test_adopt_aliases_binds_each_epithet_to_its_row():
    ep = NS(shots=[shot("the lawyer (black bowler hat) turns", "the little man (soft black felt wideawake hat) walks")])
    takes_r2v.adopt_aliases(ep, ROWS)
    assert ro.ALIASES == {"gabriel_john_utterson": ["the lawyer"], "edward_hyde": ["the little man"]}
    ro.ALIASES.clear()


def test_mode_said_names_the_panel_when_one_is_staged():
    said = takes_r2v.mode_said(True, panel=True)
    assert "storyboard panel" in said and "no storyboard cell" not in said


def test_lint_faults_names_each_take_and_the_plan(monkeypatch):
    from studio import prompt_lint
    monkeypatch.setattr(prompt_lint, "facts_for", lambda book, rec, plan: {"faces": []})
    monkeypatch.setattr(prompt_lint, "plan_faults", lambda plan, rows: ["P11 dangling aim: shot 10 to the folded;"])
    monkeypatch.setattr(prompt_lint, "characters", lambda book: [])
    got = takes_r2v.lint_faults(Path("."), {"shots": []}, [{"index": 3, "prompt": "At the first frame tHE FOCUS"}])
    assert got[0].startswith("T03 P1") and got[-1].startswith("plan P11")
