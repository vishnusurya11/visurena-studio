"""The acceptance replay's pure parts (the GPU parts run only in an owner-
approved window): cells cut row by row, a panel shows a look when its hair
family AND facial hair match, the pass share is 80 %."""
from __future__ import annotations

from studio.continuity_spec import CharacterLooks, LookBook, Markers
from tests import continuity_fixtures as fx

from scripts.refs import look_replay as replay

RAGGED = Markers(hair_colour="grey", facial_hair="beard")


def test_cells_are_cut_row_by_row():
    assert replay.panel_boxes(2048, 1024, 2, 1) == [(0, 0, 1024, 1024), (1024, 0, 2048, 1024)]


def test_a_panel_shows_the_look_only_with_its_hair_and_its_beard():
    assert replay.shows_look({"hair_colour": "white", "facial_hair": "beard"}, RAGGED)
    assert not replay.shows_look({"hair_colour": "dark", "facial_hair": "beard"}, RAGGED)
    assert not replay.shows_look({"hair_colour": "grey", "facial_hair": "moustache"}, RAGGED)


def test_the_pass_share_is_eighty_percent():
    good, bad = {"hair_colour": "grey", "facial_hair": "beard"}, {"unread": "x"}
    assert replay.tally([good] * 4 + [bad], RAGGED)["passed"]
    assert not replay.tally([good] * 3 + [bad] * 2, RAGGED)["passed"]


def test_the_staged_looks_are_the_chapters():
    from types import SimpleNamespace
    table = LookBook(characters={"narrator": CharacterLooks.model_validate(fx.CARD)})
    shots = [SimpleNamespace(faces=["narrator", "curate"])]
    assert replay.staged_looks(None, table, SimpleNamespace(number=24), shots) == {"narrator": "ragged"}


def test_a_strip_sets_the_shipped_panel_beside_the_replayed(tmp_path):
    from PIL import Image
    Image.new("RGB", (100, 100)).save(tmp_path / "a.png")
    Image.new("RGB", (50, 50)).save(tmp_path / "b.png")
    out = replay.strip(tmp_path / "a.png", tmp_path / "b.png", tmp_path / "s.png")
    assert Image.open(out).size == (100, 50)
    assert replay.bench_dir(tmp_path, 25, "x", out="o").as_posix() == "o/ep25_x"


def test_the_tally_counts_unread_panels_apart():
    good, bad = {"hair_colour": "grey", "facial_hair": "beard"}, {"unread": "x"}
    assert replay.tally([good, bad, bad], RAGGED)["unread"] == 2


# C2_verdict #7: the bar counts FACE-VISIBLE panels.  The C1 ep25 regrid scored
# 2/4 because shot 2 is "Medium from behind" and shot 4 a Wide: no beard can be seen.
def shot(size="medium", frame="Medium of the narrator at the corner", faces=("narrator",)):
    from types import SimpleNamespace
    return SimpleNamespace(size=size, frame=frame, faces=list(faces))


GREY_BEARD = {"hair_colour": "grey", "facial_hair": "beard"}


def test_a_back_view_or_a_far_size_is_not_in_the_denominator():
    assert replay.face_visible(shot())
    assert not replay.face_visible(shot(frame="Medium from behind of the narrator"))
    assert not replay.face_visible(shot(frame="The narrator walking away down the road"))
    assert not replay.face_visible(shot(frame="He stands with his back to the camera"))
    assert not replay.face_visible(shot(size="wide")) and not replay.face_visible(shot(size="establishing"))


def test_an_over_the_shoulder_panel_stays_in_the_denominator():
    assert replay.face_visible(shot(frame="Over his shoulder, the curate faces him"))


def test_a_face_visible_panel_with_no_face_read_is_a_miss():
    got = replay.tally([GREY_BEARD, {"hair_colour": "grey"}], RAGGED, [shot(), shot()])
    assert (got["shown"], got["of"], got["passed"]) == (1, 2, False)


def test_an_empty_denominator_is_unmeasurable_never_passed():
    got = replay.tally([GREY_BEARD], RAGGED, [shot(size="wide")])
    assert got["of"] == 0 and got["unmeasurable"] and not got["passed"]


def _plan_shots(number: int, ids: list[int]):
    import pytest
    from studio import episode_home
    book = episode_home.book_dir("20260827135508_the-war-of-the-worlds")
    if not (book / "episodes").exists():
        pytest.skip("no WotW library on this machine")
    by_index = {s.index: s for s in episode_home.load_plan(book, number).shots}
    return [by_index[i] for i in ids]


def test_the_c1_ep25_regrid_passes_two_of_two_and_round_0_still_fails():
    import json
    from pathlib import Path
    evidence = Path(__file__).resolve().parents[1] / "docs/audit/2026-10-10_continuity_retro/bench_evidence/c1"
    reads = json.loads((evidence / "regrid_ep25_report.json").read_text(encoding="utf-8"))["reads"]
    shots = _plan_shots(25, [0, 1, 2, 4])
    got = replay.tally([reads[k] for k in ("0", "1", "2", "4")], RAGGED, shots)
    assert (got["shown"], got["of"], got["passed"]) == (2, 2, True)
    beardless = [{"hair_colour": "grey", "facial_hair": "none"}] * 3          # round 0: shown 0 of 3
    got = replay.tally(beardless, RAGGED, _plan_shots(25, [0, 2, 4]))
    assert (got["shown"], got["of"], got["passed"]) == (0, 1, False)


def test_the_ep27_study_table_replay_passes_three_of_three():
    moustache = Markers(hair_colour="grey", facial_hair="moustache")
    got = replay.tally([{"hair_colour": "grey", "facial_hair": "moustache"}] * 3, moustache, _plan_shots(27, [3, 12, 13]))
    assert (got["shown"], got["of"], got["passed"]) == (3, 3, True)
