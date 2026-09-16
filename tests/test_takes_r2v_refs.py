"""The reference slots of an r2v take (spec 3.19): cast sheets, the plate, every
pinned cell in first-pin order, the END cells, then the strip.  `graph_for` stages
them in list order, so this list IS the `<Picture N>` numbering the prompt uses."""
import importlib.util
from pathlib import Path

import pytest
from PIL import Image


def _reachable_pair(start, end):
    """A cell and an END cell ONE PUSH apart: MEASURED at 0.661, inside the
    0.45-0.80 band. An exact copy measures 1.0 and is no destination -- it tells
    the take to end where it began."""
    import numpy as np
    y, x = np.mgrid[0:64, 0:64]
    a = (128 + 110 * np.sin(x / 11.0) * np.cos(y / 13.0)).astype("uint8")
    Image.fromarray(a).save(start)
    Image.fromarray(a).crop((16, 16, 48, 48)).resize((64, 64)).save(end)

from studio import episode_ref_official as ro
from studio.episode_spec import Shot, SubShot

spec = importlib.util.spec_from_file_location(
    "takes_r2v", Path(__file__).resolve().parents[1] / "scripts" / "episode" / "takes_r2v.py")
tr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tr)


def shot(index, faces, cuts=()):
    return Shot(index=index, section="setup", setup="lab", size="medium", faces=list(faces),
                frame="Medium shot of the bench.", motion="Static shot; he lifts the tube",
                cuts=[SubShot(at_s=3.0 * (k + 1), size="close", faces=list(f),
                              frame="Close on the bench.", motion="Static shot; he turns")
                      for k, f in enumerate(cuts)])


def test_a_face_a_sub_shot_shows_is_a_face_the_take_stages():
    """MEASURED (review8/identity.md): `faces_of` read shot-level faces only, so 6 of 19
    iteration-4 takes put a full readable face on screen with NO cast sheet staged and
    no <Subject N> line for it; identity then survived on the pinned cell alone, which
    is the class of T09's Watson slip in iteration 3."""
    assert tr.faces_of([shot(0, [], cuts=[["john_watson"]])]) == ["john_watson"]
    assert tr.faces_of([shot(0, ["stamford"], cuts=[["john_watson"]])]) == ["stamford", "john_watson"]


def test_the_union_keeps_first_appearance_order_and_never_repeats_a_face():
    take = [shot(0, ["stamford"], cuts=[["stamford"], ["john_watson"]]), shot(1, ["john_watson"])]
    assert tr.faces_of(take) == ["stamford", "john_watson"]


def test_every_declared_face_is_staged_up_to_the_reference_ceiling():
    """Owner 2026-09-12: anyone the scene names gets a sheet.  The ceiling is the
    node's nine reference slots, spent on faces, the plate and the pinned cells."""
    take = [shot(0, ["stamford"], cuts=[["john_watson"], ["sherlock_holmes"]])]
    assert tr.faces_of(take) == ["stamford", "john_watson", "sherlock_holmes"]
    assert len(tr.faces_of(take)) <= tr.MAX_FACES


def test_the_reference_list_is_the_picture_numbering_the_prompt_states(tmp_path, monkeypatch):
    # This is about the PICTURE NUMBERING when an END cell is staged, so it is
    # stated with the pin turned back ON. The live default withholds every END
    # picture -- `takes_r2v.NO_ENDS`, the owner's rule of 2026-09-16.
    monkeypatch.setattr(tr, "NO_ENDS", False)
    book, frames = tmp_path / "book", tmp_path / "frames"
    (book / "refs" / "characters").mkdir(parents=True)
    (frames / "plates").mkdir(parents=True)
    (frames / "cells").mkdir(parents=True)
    (book / "refs" / "characters" / "char-john_watson.png").write_bytes(b"")
    for name in ("plate_lab.png", "Q00_0.png", "Q00_1.png", "Q01_0.png"):
        ((frames / "plates" if name.startswith("plate_") else frames / "cells") / name).write_bytes(b"")
    # Q00_1E has to be a REAL picture: `end_cells` now measures whether one camera
    # move reaches it from Q00_1, so both of that pair are drawn one push apart.
    _reachable_pair(frames / "cells" / "Q00_1.png", frames / "cells" / "Q00_1E.png")
    segs = [(0, 0), (0, 1), (1, 0)]
    refs = tr.reference_list(book, frames, ["john_watson"], "lab", segs,
                             tr.end_cells(frames / "cells", segs), frames / "ref_take_00.png",
                             sizes=["medium", "close", "close"])
    assert [p.name for p in refs] == ["char-john_watson.png", "plate_lab.png", "Q00_0.png", "Q00_1.png",
                                      "Q01_0.png", "Q00_1E.png"]


def test_a_take_of_nothing_but_tight_cells_stages_no_plate(tmp_path):
    """MEASURED, episode 2: 13 of the 14 foreign frames were the take's OWN plate,
    every one from a close/insert take with no wider cell to place a room against
    (Fisher p = 0.0072).  With no wide cell the plate stops being a definition and
    becomes the only whole picture the model can fall back on."""
    book, frames = tmp_path / "book", tmp_path / "frames"
    (book / "refs" / "characters").mkdir(parents=True)
    (frames / "plates").mkdir(parents=True)
    (frames / "cells").mkdir(parents=True)
    (book / "refs" / "characters" / "char-john_watson.png").write_bytes(b"")
    for name in ("plate_lab.png", "Q00_0.png", "Q00_1.png"):
        ((frames / "plates" if name.startswith("plate_") else frames / "cells") / name).write_bytes(b"")
    segs = [(0, 0), (0, 1)]
    refs = tr.reference_list(book, frames, ["john_watson"], "lab", segs, [],
                             frames / "ref_take_00.png", sizes=["close", "insert"])
    assert [p.name for p in refs] == ["char-john_watson.png", "Q00_0.png", "Q00_1.png"]


def test_the_reference_list_never_passes_the_nine_slot_wall(tmp_path):
    book, frames = tmp_path / "book", tmp_path / "frames"
    (book / "refs" / "characters").mkdir(parents=True)
    (frames / "plates").mkdir(parents=True)
    (frames / "cells").mkdir(parents=True)
    segs = [(0, k) for k in range(9)]
    with pytest.raises(SystemExit, match=str(ro.MAX_PICTURES)):
        tr.reference_list(book, frames, ["john_watson", "stamford"], "lab", segs, [],
                          frames / "ref_take_00.png")


def test_a_pin_lands_on_a_token_start_and_the_snap_is_the_owners_forward_one():
    """OWNER: the picture cut lands ON or AFTER the voice cut (audio-first).  3.20's
    nearest-second snap is `tk.near_grid`, tested beside it and one line away."""
    assert tr.on_grid(76) == 77 and tr.on_grid(0) == 0


def test_being_named_no_longer_earns_a_whole_picture():
    """Owner 2026-09-12, on take 00: "you have Watson turning around after the dialogue
    but did not feed Watson, so the face is not matching, no moustache".  S00 lists
    only Stamford in `faces` because only his face has to READ, but the motion turns
    Watson to camera.  A reference is owed to anyone the panel text names, whatever
    `faces` says: `faces` decides who must be legible, not who is in the room."""
    from studio.episode_spec import Shot, SubShot
    shot = Shot(index=0, section="hook", setup="criterion", size="medium_close", faces=["stamford"],
                frame="Medium close on Stamford at the counter.",
                motion="Static shot; Watson turns his whole body round to face Stamford.",
                cuts=[SubShot(at_s=3.0, size="insert", faces=[],
                              frame="Insert on the bare sunburnt hand of John Watson on the knob.",
                              motion="Static shot; the fingers close")])
    # FIX B 2026-09-13: being NAMED no longer earns a whole-frame picture. Watson is
    # named in the motion and shown by no segment, so he is described in the subject
    # definitions and costs no reference slot. Measured: 6 such sheets in episode 3.
    assert tr.faces_of([shot], ["john_watson", "sherlock_holmes", "stamford"]) == ["stamford"]
    # a name nobody mentions stays out
    assert "sherlock_holmes" not in tr.faces_of([shot], ["sherlock_holmes", "john_watson", "stamford"])
