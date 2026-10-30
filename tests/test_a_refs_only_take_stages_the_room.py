"""A take with no panel stages its setup's EMPTIED room, not the book's place picture (Jekyll ep06, 2026-10-29).

Take 23 went refs-only and staged refs/locations/jekyll_house/front_door_square__..., a warm, gold-lit wide
street; its four siblings were drawn on the storyboard's cool blue room.  The picture jumped in the middle
of one conversation.  One room per setup: where the room is cut and holds no people, it is the place."""
from pathlib import Path

from scripts.episode import takes_r2v as tr
from studio import grid_room as gr


def room(home: Path, people: int | None) -> Path:
    path = gr.room_path(home, "doorstep")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"room")
    if people is not None:
        gr.note_people(path, people)
    return path


def test_a_panel_less_take_stages_the_emptied_room(tmp_path):
    emptied = room(tmp_path, 0)
    assert tr.place_of(tmp_path, "doorstep", tmp_path / "loc.png", panel=False) == emptied


def test_a_room_with_people_left_never_reaches_a_take(tmp_path):
    room(tmp_path, 1)
    assert tr.place_of(tmp_path, "doorstep", tmp_path / "loc.png", panel=False) == tmp_path / "loc.png"


def test_a_room_cut_before_the_rule_is_not_staged(tmp_path):
    room(tmp_path, None)
    assert tr.place_of(tmp_path, "doorstep", tmp_path / "loc.png", panel=False) == tmp_path / "loc.png"


def test_a_take_with_its_panel_keeps_the_place_picture(tmp_path):
    room(tmp_path, 0)
    assert tr.place_of(tmp_path, "doorstep", tmp_path / "loc.png", panel=True) == tmp_path / "loc.png"


def test_no_room_keeps_the_place_picture(tmp_path):
    assert tr.place_of(tmp_path, "doorstep", tmp_path / "loc.png", panel=False) == tmp_path / "loc.png"


def test_the_staged_room_is_named_so_the_graph_finds_it(tmp_path):
    """Jekyll ep06 run 30: the card named the room by its bare file name and graph_for looked for it among the
    sequence cells (boards/cells/doorstep_poole.png): 'cannot stage missing image'.  A record keeps the room's
    book-relative path, and picture_path brings it back to the file."""
    from studio import episode_seq_board as sq
    book = tmp_path / "book"
    path = gr.room_path(book / "episodes" / "ep06", "doorstep")
    path.parent.mkdir(parents=True)
    path.write_bytes(b"room")
    name = tr.ref_name(book, path)
    assert name == "episodes/ep06/storyboard/anchors/doorstep.png"
    assert sq.picture_path(book / "episodes" / "ep06" / "boards", book, name) == path
