"""Every shot and sub-shot of a setup sits at a position on the setup's route,
and the positions never go backwards: the storyboard is drawn as one
sequence, so nobody reaches the door twice."""
import pytest

from studio import episode_seq_board as sq
from studio.episode_spec import Episode, Setup, Shot, SubShot


def test_route_positions_must_not_go_backwards_within_a_setup():
    ok = [Shot(index=0, section="hook", setup="c", size="medium", frame="A.", motion="Static", path=0.1),
          Shot(index=1, section="setup", setup="c", size="medium", frame="B.", motion="Static", path=0.4,
               cuts=[SubShot(at_s=3.0, size="close", frame="C.", motion="Static", path=0.5)])]
    assert sq.route_ok(ok) is True
    bad = [Shot(index=0, section="hook", setup="c", size="medium", frame="A.", motion="Static", path=0.6),
           Shot(index=1, section="setup", setup="c", size="medium", frame="B.", motion="Static", path=0.4)]
    assert sq.route_ok(bad) is False


def test_segments_of_a_setup_list_shots_and_sub_shots_in_order_with_their_position():
    shots = [Shot(index=0, section="hook", setup="c", size="medium", frame="A.", motion="Static", path=0.1),
             Shot(index=1, section="setup", setup="c", size="insert", frame="B.", motion="Static", path=0.3,
                  cuts=[SubShot(at_s=3.0, size="close", faces=["john_watson"], frame="C.", motion="Static", path=0.35)]),
             Shot(index=2, section="setup", setup="lab", size="medium", frame="D.", motion="Static", path=0.0)]
    segs = sq.segments(shots, "c")
    assert [(s["shot"], s["sub"]) for s in segs] == [(0, 0), (1, 0), (1, 1)]
    assert segs[2]["frame"] == "C." and segs[2]["path"] == 0.35 and segs[2]["faces"] == ["john_watson"]


def test_the_geography_prompt_names_the_walk_and_the_door_size_per_panel():
    setup = Setup(described="A corridor.", cast=["john_watson"], landmark="the barred window",
                  route="from the corridor's near end to the dissecting-room doorway at its far end")
    segs = [{"shot": 0, "sub": 0, "size": "full", "frame": "Two men walk away from behind.", "motion": "Static", "path": 0.1, "faces": []},
            {"shot": 1, "sub": 0, "size": "medium", "frame": "Side view of the two men.", "motion": "Static", "path": 0.3, "faces": []}]
    text = sq.prompt(segs, setup, {"john_watson": "Thin."}, previous=False, first=True, geography=True)
    assert text.startswith("SHEET\nA film storyboard sheet")
    assert "farther along it than the one before" in text and "from the corridor's near end" in text
    assert ("Panel 1 - FULL SHOT. In frame: Two men walk away from behind. The barred window is the height "
            "of a thumbnail.") in text
    assert ("Panel 2 - MEDIUM. In frame: Side view of the two men. The barred window is the height of a "
            "finger.") in text


def test_sheets_chunk_nine_cells_and_name_the_cell_files():
    segs = [{"shot": i, "sub": 0, "frame": "x", "motion": "y", "path": i / 12, "faces": []} for i in range(12)]
    chunks = sq.chunks(segs)
    assert [len(c) for c in chunks] == [9, 3]
    assert sq.cell_name(3, 1) == "Q03_1.png" and sq.cell_name(12, 0) == "Q12_0.png"
