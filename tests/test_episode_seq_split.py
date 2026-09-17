"""One camera axis per sheet: geography panels sorted by distance on their
own strip, close-ups and inserts on sheets that carry no geography."""
from studio import episode_seq_board as sq
from studio.affirm import negations
from studio.episode_spec import Setup


def seg(shot, sub, size, path, frame="the barred window far off", faces=()):  # the landmark is in frame
    return {"shot": shot, "sub": sub, "size": size, "path": path, "frame": frame, "motion": "Static", "faces": list(faces)}


SEGS = [seg(0, 0, "medium_close", 0.05, faces=["stamford"]), seg(1, 0, "close", 0.15, faces=["stamford"]),
        seg(1, 1, "insert", 0.18), seg(3, 0, "medium", 0.40, "Over Watson's shoulder from behind, the barred window far"),
        seg(4, 0, "full", 0.55, "Full shot from behind, the two men walking away to the barred window"), seg(4, 2, "medium", 0.66, "Side view, the barred window ahead"),
        seg(7, 2, "medium", 1.0, "From behind: Stamford through the side-door under the barred window")]


def test_a_walk_panel_is_a_wide_framing_with_a_place_on_the_route():
    assert [(s["shot"], s["sub"]) for s in SEGS if sq.on_route(s)] == [(3, 0), (4, 0), (4, 2), (7, 2)]
    assert [(s["shot"], s["sub"]) for s in SEGS if not sq.on_route(s)] == [(0, 0), (1, 0), (1, 1)]


def test_the_walk_prompt_names_a_growing_landmark():
    setup = Setup(described="A corridor.", cast=[], landmark="the barred window",
                  route="from the corridor's near end to the doorway at its far end")
    geo = [s for s in SEGS if sq.on_route(s)]
    text = sq.prompt(geo, setup, {}, previous=False, first=True, geography=True)
    assert "so the barred window is larger in each of them than in the one before" in text
    assert "is the height of a hand" in text and "fills the frame" in text
    assert "each of them farther along it than the one before" in text


def test_a_sheet_with_no_walk_panel_carries_no_geography():
    setup = Setup(described="A corridor.", cast=[], landmark="the barred window", route="from A to B")
    close = [s for s in SEGS if not sq.on_route(s)]
    text = sq.prompt(close, setup, {}, previous=True, first=False, geography=[])
    assert "look along that path" not in text and "is larger in each of them" not in text
    assert "The panels are in story order" in text


def test_the_door_ladder_maps_route_position_to_a_size_word():
    assert sq.door_size(0.05) == "is the height of a thumbnail"
    assert sq.door_size(0.45) == "is the height of a hand"
    assert sq.door_size(0.95) == "fills the frame"


def test_panels_are_in_story_order_and_an_end_panel_follows_its_own_start(monkeypatch):
    """Owner 2026-09-11: the sheet reads in story order.  Sorting the wides first
    made panel 1 of the criterion sheet shot 2 and panel 2 shot 0."""
    # END panels are the reproducible CONTROL now, not the default: the owner's
    # rule of 2026-09-16 fills spare cells with ALTERNATES instead
    # (`episode_seq_board.DRAW_ENDS`). These three state how the packer PLACES an
    # END panel when one is asked for, so they ask for one.
    monkeypatch.setattr(sq, "DRAW_ENDS", True)
    sheets = sq.sheets(SEGS)
    group, route, _grid = sheets[0]
    assert [(s["shot"], s["sub"], bool(s.get("end"))) for s in group] == [
        (0, 0, False), (1, 0, False), (1, 1, False), (3, 0, False), (3, 0, True),
        (4, 0, False), (4, 0, True), (4, 2, False), (7, 2, False)]
    assert route == [4, 5, 6, 7, 8, 9]  # the panel numbers on the walk, in story order
    ends = [k for k, s in enumerate(group, start=1) if s.get("end")]
    for k in ends:
        assert group[k - 2]["shot"] == group[k - 1]["shot"]  # an END panel sits after its own start


def test_the_far_landmark_line_only_fires_on_a_route_panel():
    """'the mirror behind them' is not the far landmark: the ladder sentence used to
    fire on the substring 'behind' anywhere in a panel's text."""
    setup = Setup(described="A bar.", cast=[], landmark="the far door")
    close = seg(2, 0, "close", None, "Close on Stamford, the gilt mirror behind them")
    assert "height of" not in sq.panel_text(1, close, [], setup)
    walk = seg(3, 0, "medium", 0.4, "Over Watson's shoulder from behind, the door far")
    assert "height of" in sq.panel_text(1, walk, [1], setup)


def test_a_setup_that_fits_one_sheet_draws_geography_then_close_ups_with_no_repeats(monkeypatch):
    """Owner 2026-09-11: 'most 3x3 storyboards have all 3 rows the same' — a
    two-cell strip was padded with seven alternates.  Seven cells fit one sheet."""
    # END panels are the reproducible CONTROL now, not the default: the owner's
    # rule of 2026-09-16 fills spare cells with ALTERNATES instead
    # (`episode_seq_board.DRAW_ENDS`). These three state how the packer PLACES an
    # END panel when one is asked for, so they ask for one.
    monkeypatch.setattr(sq, "DRAW_ENDS", True)
    sheets = sq.sheets(SEGS)
    assert len(sheets) == 1
    group, route, grid = sheets[0]
    assert grid == (3, 3, (2048, 3072)) and len(group) == 9  # seven panels + two END panels, no repeats
    assert [(s["shot"], s["sub"]) for s in group if s.get("end")] == [(3, 0), (4, 0)]
    setup = Setup(described="A corridor.", cast=[], landmark="the barred window", route="from A to B")
    text = sq.prompt(group, setup, {}, previous=False, first=True, geography=route)
    assert sq.DIFFERENT in text  # the law is stated affirmatively: a negated noun is still that noun
    assert "The panels are in story order: panel 1 happens first" in text
    assert "so the barred window is larger in each of them than in the one before" in text
    assert "Panel 5 - PANEL 4 ONE ACTION LATER" in text
    assert "Panel 7 - PANEL 6 ONE ACTION LATER" in text
    # the END panel CARRIES the start panel's nouns instead of pointing at them
    assert "drawn afresh" not in text and "identical" not in text and "alternate" not in text
    assert negations(text) == []


def test_the_grid_is_the_smallest_that_holds_the_cells():
    assert sq.grid(2) == (3, 1, (1536, 1024)) and sq.grid(3) == (3, 1, (1536, 1024))
    assert sq.grid(4) == (3, 2, (2048, 2048)) and sq.grid(6) == (3, 2, (2048, 2048))
    assert sq.grid(7) == (3, 3, (2048, 3072)) and sq.grid(9) == (3, 3, (2048, 3072))


def test_end_frames_fill_the_spare_cells_walk_cells_first_and_are_named_apart():
    group = [s for s in SEGS[:5] if s["size"] in sq.GEO_SIZES] + [s for s in SEGS[:5] if s["size"] not in sq.GEO_SIZES]
    ends = sq.end_panels(group, 2)
    assert [(e["shot"], e["sub"]) for e in ends] == [(3, 0), (4, 0)]  # the walk panels first
    # THE END PANEL CARRIES THE START PANEL'S OWN NOUNS, rather than pointing at
    # them with "the same place ... drawn afresh". And a motion of "Static" yields
    # NO change clause at all -- static is the word for nothing moving, and it was
    # being handed to the drawer as the thing that changed.
    assert ends[0]["end"]
    assert "the barred window far" in ends[0]["frame"] and "drawn afresh" not in ends[0]["frame"]
    assert "identical" not in ends[0]["frame"] and "Static" not in ends[0]["frame"]
    assert ends[0]["changed"] == ""
    assert sq.cell_name(4, 0, end=True) == "Q04_0E.png" and sq.cell_name(4, 0) == "Q04_0.png"


def test_a_setup_over_nine_cells_still_splits_by_axis():
    many = SEGS + [seg(9 + i, 0, "close", 0.9) for i in range(4)]
    sheets = sq.sheets(many)
    # AMENDED 2026-09-13: evenly, not greedily -- a remainder sheet is a grid
    # the drawer fills and the packer discards. See `test_sheets_are_balanced.py`.
    assert [len(g) for g, _, _ in sheets] == [6, 6]
    assert [(s["shot"], s["sub"]) for s in sheets[0][0]][:3] == [(0, 0), (1, 0), (1, 1)]


def test_an_end_panel_names_the_panel_number_it_closes_on_this_sheet(monkeypatch):
    """The END panel used to be numbered by its place in the SEGMENT list, so once
    one END cell was inserted every later END named the panel before its own start."""
    # END panels are the reproducible CONTROL now, not the default: the owner's
    # rule of 2026-09-16 fills spare cells with ALTERNATES instead
    # (`episode_seq_board.DRAW_ENDS`). These three state how the packer PLACES an
    # END panel when one is asked for, so they ask for one.
    monkeypatch.setattr(sq, "DRAW_ENDS", True)
    panels = sq.with_ends(SEGS[:5], spare=2)
    ends = [(k, s["of"]) for k, s in enumerate(panels, start=1) if s.get("end")]
    assert ends == [(5, 4), (7, 6)]
    for k, of in ends:
        assert panels[of - 1] is panels[k - 2]  # the panel it closes is the one straight before it
