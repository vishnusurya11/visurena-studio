"""`sheet_dq.py` runs the pre-spend gate over every setup of an episode.

It builds each sheet's prompt exactly as `seq_boards.py` will build it, gates
the TEXT, and writes `frames/sheet_dq.json`.  It draws nothing: a run of this
script costs $0 and touches no GPU, which is the whole point of putting it
before the draw.
"""
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

from studio.episode_spec import Setup, Shot

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("ep_sheet_dq", ROOT / "scripts" / "episode" / "sheet_dq.py")
dq = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dq)

# AMENDED 2026-09-16: the description names a GARMENT.  It used to be "a brown
# bowler hat" alone and the setup counted as clean -- which is the episode 9
# fault verbatim (a WARDROBE line with no clothes on it), now a HARD finding
# (`sheet_gate.garments_named`).
PHYSICAL = {"john_watson": "A man in his late twenties, as brown as a nut, a brown tweed overcoat, a brown bowler hat."}
CORRIDOR = Setup(described="A whitewashed hospital corridor, 1881.", cast=["john_watson"],
                 landmark="the pale barred window", route="from the near end to the far door",
                 crowd="two porters halted at the left-hand wall with a covered trolley between them")


FRAMES = ("Medium shot from behind at the near end: two men walking away over the flagstones.",
          "Close on the round clean-shaven face in strict profile, whitewashed brick streaming past.",
          "Full shot up the flight of worn stone treads, the iron rail bright along one side.",
          "Insert on a dun-coloured panel and its cast-iron latch, cold light from a high opening.")


def shot(index, **kw):
    base = {"index": index, "section": "setup", "setup": "corridor", "size": "medium", "path": 0.1,
            "frame": FRAMES[index % len(FRAMES)], "motion": "he walks on",
            "camera": f"{'low' if index % 2 else 'at walking height'} in the corridor, lens {index}",
            "crowd": "two porters halted at the wall, unloading a covered trolley"}
    return Shot(**(base | kw))


def episode(shots):
    return SimpleNamespace(number=1, setups={"corridor": CORRIDOR}, shots=shots)


def test_a_clean_setup_passes_with_no_finding():
    report = dq.setup_report(episode([shot(0), shot(1, path=0.4)]), "corridor", PHYSICAL)
    assert report["passed"] is True and report["findings"] == []


def test_a_camera_move_in_one_panel_fails_that_setup_and_names_the_panel():
    bad = shot(1, path=0.4, camera="tracking beside him down the corridor")
    report = dq.setup_report(episode([shot(0), bad]), "corridor", PHYSICAL)
    assert report["passed"] is False
    hits = [f for f in report["findings"] if f["check"] == "CAMERA"]
    assert [(f["panel"], f["text"].lower()) for f in hits] == [("Q01_0", "tracking")]


def test_every_sheet_of_the_setup_is_reported_with_its_grid_and_its_panels():
    report = dq.setup_report(episode([shot(k, path=k / 20) for k in range(4)]), "corridor", PHYSICAL)
    sheet = report["sheets"][0]
    assert sheet["grid"] == "3x2" and len(sheet["panels"]) == 6  # 4 panels + 2 END panels in the spares
    assert sheet["verdict"]["passed"] in (True, False)


def test_the_report_covers_every_setup_and_rolls_up_to_one_verdict():
    report = dq.report(episode([shot(0), shot(1, path=0.4, camera="a pan along the wall, tracking with him")]), PHYSICAL)
    assert [s["setup"] for s in report["setups"]] == ["corridor"]
    assert report["passed"] is False and report["hard"] >= 1


def test_the_report_is_json_and_carries_no_absolute_path(tmp_path):
    report = dq.report(episode([shot(0), shot(1, path=0.4)]), PHYSICAL)
    text = json.dumps(report)
    assert "D:\\" not in text and "/library/" not in text
    (tmp_path / "sheet_dq.json").write_text(text, encoding="utf-8")


def test_the_verdict_line_says_the_setup_the_sheets_and_the_counts():
    report = dq.report(episode([shot(0), shot(1, path=0.4, camera="tracking beside him")]), PHYSICAL)
    line = dq.rows(report)[0]
    assert line.startswith("corridor") and "FAIL" in line and "CAMERA" in line
