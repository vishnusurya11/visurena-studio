"""G-WHO (owner 2026-10-28, after Jekyll ep05 shipped with doubles): two figures of one take frame
that each read as the same cast member are a wrong person, never a flag.

Face vectors cannot see it: the doubled faces of ep05 sat at 6-8 % of frame height, every one under
READABLE, and their pair cosines (0.1-0.7) do not tell one man from two.  The twin ask asks for the
same face AND the same dress, and H3 draws a second face in the first man's clothes.  What a viewer
reads is hair, facial hair and coat colour, so the reader lists those per figure and code resolves
each figure to the one staged cast member it agrees with and every other contradicts.  The reader
calls a bowler a top hat, so headwear is not read.  Fixture: real reads of ep05 frames."""
import json
from pathlib import Path

import pytest

from studio import figure_who as fw
from studio import panel_content as pc
from studio import people_faults

FIXTURE = json.loads((Path(__file__).parent / "fixtures" / "who_reads_jekyll_ep05.json").read_text(encoding="utf-8"))


def staged(take: dict) -> dict:
    return {who: fw.staged_marks(row["markers"], row["top"]) for who, row in take["cast"].items()}


def fired(take: dict) -> bool:
    return any(fw.fault(figs, staged(take)) for figs in take["frames"])


@pytest.mark.parametrize("take", FIXTURE["takes"], ids=lambda t: t["take"])
def test_the_who_read_agrees_with_the_eye(take):
    assert fired(take) == take["double_by_eye"]


def test_the_coat_is_the_first_colour_its_top_names():
    assert fw.coat_of("long black double-breasted overcoat with six white buttons, white shirt") == "dark"
    assert fw.coat_of("long deep bottle-green frock coat, dark green waistcoat, white shirt") == "green"
    assert fw.coat_of("dark clerk's frock coat") == "dark"
    assert fw.coat_of("") == ""


def test_a_cast_with_no_markers_never_resolves():
    figs = [{"hair": "white", "facial_hair": "none", "coat": "black"}] * 2
    assert fw.fault(figs, {"a": fw.staged_marks({}, ""), "b": fw.staged_marks({}, "")}) is None


def test_one_cast_member_seen_twice_is_a_people_fault():
    marks = {"utterson": fw.staged_marks({"hair_colour": "grey", "facial_hair": "none"}, "black overcoat"),
             "guest": fw.staged_marks({"hair_colour": "dark", "facial_hair": "beard"}, "brown coat")}
    figs = [{"hair": "white", "facial_hair": "none", "coat": "black"}] * 2
    line = fw.fault(figs, marks)
    assert line.startswith("who:") and "utterson" in line
    assert people_faults.wrong_line(line)


def test_an_answer_with_no_figures_is_unreadable():
    with pytest.raises(pc.Unreadable):
        fw.parse('{"people": 2}')
    assert fw.parse('{"figures": [{"hair": "grey"}]}') == [{"hair": "grey"}]


def test_the_ask_runs_only_where_two_cast_faces_can_be_read():
    assert fw.applies(planned=2, size="medium", people=2)
    assert not fw.applies(planned=1, size="medium", people=2)
    assert not fw.applies(planned=2, size="wide", people=2)
    assert not fw.applies(planned=2, size="medium", people=1)


# ---- the wiring: the staged look's coat, the take's frames, the verdict's key ----------------

def card(top_by_look: dict, base: str):
    from types import SimpleNamespace as NS
    return NS(base=base, looks={k: NS(layers=NS(top=v)) for k, v in top_by_look.items()})


def test_the_staged_top_is_the_staged_looks_top_layer(monkeypatch):
    from studio import continuity
    monkeypatch.setattr(continuity, "card_of", lambda book, who: card({"base": "black coat", "night": "green coat"}, "base"))
    assert continuity.top_for(None, "a", "night", {}) == "green coat"
    assert continuity.top_for(None, "a", "", {"look": "night"}) == "green coat"
    assert continuity.top_for(None, "a", "", {}) == "black coat"
    monkeypatch.setattr(continuity, "card_of", lambda book, who: None)
    assert continuity.top_for(None, "a", "night", {}) == ""


def tcc():
    import importlib.util
    import sys
    path = Path(__file__).resolve().parents[1] / "scripts" / "episode" / "take_content_check.py"
    spec = importlib.util.spec_from_file_location("tcc_who", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["tcc_who"] = module
    spec.loader.exec_module(module)
    return module


def test_a_take_frame_with_one_cast_member_twice_fails_its_verdict(tmp_path, monkeypatch):
    from types import SimpleNamespace as NS
    check = tcc()
    take = next(t for t in FIXTURE["takes"] if t["take"] == "T02")
    monkeypatch.setattr(check, "read_who_frame", lambda path, seed: take["frames"][seed - 31])
    shot = NS(faces=list(take["cast"]), size="medium")
    got = check.who_faults_for(shot, [pc.Seen(people=2)] * 3, tmp_path, "T02", staged(take))
    assert got and got[0].startswith("who:")
    assert not check.with_twins({"passed": True, "faults": []}, got)["passed"]


def test_a_one_cast_shot_is_never_asked(tmp_path, monkeypatch):
    from types import SimpleNamespace as NS
    check = tcc()
    monkeypatch.setattr(check, "read_who_frame", lambda path, seed: pytest.fail("asked"))
    assert check.who_faults_for(NS(faces=["a"], size="medium"), [pc.Seen(people=2)], tmp_path, "T01", {}) == []


def test_the_who_ask_is_in_the_verdict_key(monkeypatch):
    check = tcc()
    before = check.words_sha8({"planned": 2}, 4.0)
    monkeypatch.setattr(fw, "ASK", fw.ASK + " changed")
    assert check.words_sha8({"planned": 2}, 4.0) != before


def test_a_look_with_an_unknown_marker_is_never_a_sink():
    """Jekyll ep06 T05: Lanyon's `pale_fallen` look named no facial hair and no coat, so it clashed with
    nothing; the reader saw a moustache on both men, Utterson clashed, and both read as Lanyon."""
    staged = {"utterson": fw.staged_marks({"hair_colour": "grey", "facial_hair": "none"}, "black overcoat"),
              "lanyon": fw.staged_marks({"hair_colour": "grey"}, "")}
    figs = [{"hair": "white", "facial_hair": "moustache", "coat": "grey"},
            {"hair": "white", "facial_hair": "moustache", "coat": "black"}]
    assert fw.fault(figs, staged) is None


def test_a_look_with_no_top_wears_its_bases_coat(monkeypatch):
    from studio import continuity
    monkeypatch.setattr(continuity, "card_of", lambda book, who: card({"base": "dapper navy-blue frock coat", "pale": ""}, "base"))
    assert continuity.top_for(None, "lanyon", "pale", {}) == "dapper navy-blue frock coat"
