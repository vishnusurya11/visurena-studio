"""Phase-0 bench B1 (2026-10-10): the restyled panel replaces the storyboard panel's slot and
nothing else -- the sheets, the voice and the prompt stay the shipped take's."""
from scripts.bench import restyle


def graph() -> dict:
    return {"18": {"class_type": "LoadImage", "inputs": {"image": "sheet_front_28241af7.png"}},
            "20": {"class_type": "LoadImage", "inputs": {"image": "shot_12_1885304d.png"}},
            "8": {"class_type": "MiniMaxH3ReferenceToVideo", "inputs": {"prompt": "x"}}}


def test_only_the_panel_slot_changes():
    out = restyle.with_panel(graph(), "restyled_ab12.png")
    assert out["20"]["inputs"]["image"] == "restyled_ab12.png"
    assert out["18"] == graph()["18"]


def test_the_place_clause_is_read_from_the_take_prompt():
    p = "One 5.88-second take of 1 shot in a Victorian study at night seen from beside its French windows. [Shot 1] runs"
    assert restyle.scene_of(p) == "a Victorian study at night seen from beside its French windows"
