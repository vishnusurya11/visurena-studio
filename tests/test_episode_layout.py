"""One episode folder, in named rooms, so fourteen of them stay legible.

THE OWNER, 2026-09-13: "name the files carefully and in sub folders at episode
level ... so it is cleaner when scaled up, easy to edit and update, re-roll."

WHAT IT LOOKED LIKE.  Episode 3 kept every artefact of every stage in three flat
folders.  `frames/` alone held the location plates, the drawn sheets, their
prompts, their dq reports, all 37 cut cells, the END cells, the superseded
`.before.png` drafts and the single-panel redraw working files -- 100+ files
under one name, with the stage each belonged to encoded only in its prefix.
`shots_r2v/` held the mp4s, the graphs, the prompts, the per-take verdicts and
the failed attempts together.  The engine lived in FOLDER SUFFIXES
(`shots_r2v`, `shots_r2v_withends`, `work_r2v`) and the masters, the reports and
the QC sat loose at the top.

At one episode that is untidy.  At fourteen it is unworkable, and the specific
thing it makes hard is the thing this pipeline does most: RE-ROLL one stage and
leave the others alone.

THE LAYOUT.  One folder per STAGE, in pipeline order, and the engine is a folder
rather than a suffix:

    ep04/
      plan.json  story.md  youtube.json      the contract and the prose
      audio/     lines/ + the music bed
      boards/    plates/  sheets/  cells/  panels/
      takes/     <engine>/ + <engine>/attempts/ + work/
      cut/       master.mp4 and every master_iterN.mp4
      reports/   qc.json and the html

Every path still resolves through `episode_home` and nowhere else, which is what
makes this a contained change rather than a sweep of string literals.
"""
from pathlib import Path

from studio import episode_home as eh

BOOK = Path("/library/a-book")


def test_the_episode_folder_is_unchanged():
    assert eh.home(BOOK, 4) == BOOK / "episodes" / "ep04"


def test_the_contract_stays_at_the_top_where_it_is_read_first():
    """`plan.json` and `story.md` are what a human opens; they do not move."""
    assert eh.plan_path(BOOK, 4) == BOOK / "episodes" / "ep04" / "plan.json"


# ---- audio ------------------------------------------------------------------

def test_the_lines_live_under_audio():
    assert eh.lines_dir(BOOK, 4) == BOOK / "episodes" / "ep04" / "audio" / "lines"


def test_the_bed_lives_beside_the_lines_not_inside_them():
    assert eh.audio_dir(BOOK, 4) == BOOK / "episodes" / "ep04" / "audio"


# ---- boards -----------------------------------------------------------------

def test_a_plate_is_not_a_sheet_is_not_a_cell():
    """The three kinds `frames/` used to mix, told apart by their folder."""
    base = BOOK / "episodes" / "ep04" / "boards"
    assert eh.plates_dir(BOOK, 4) == base / "plates"
    assert eh.sheets_dir(BOOK, 4) == base / "sheets"
    assert eh.cells_dir(BOOK, 4) == base / "cells"


def test_the_single_panel_redraws_have_their_own_room():
    """`panel_*.png` and the `.before.png` drafts are working files, and mixing
    them with the cells is how a superseded draft became a take's foreign frame."""
    assert eh.panels_dir(BOOK, 4) == BOOK / "episodes" / "ep04" / "boards" / "panels"


# ---- takes ------------------------------------------------------------------

def test_the_engine_is_a_folder_not_a_suffix():
    assert eh.takes_dir(BOOK, 4, "r2v") == BOOK / "episodes" / "ep04" / "takes" / "r2v"
    assert eh.takes_dir(BOOK, 4, "i2v") == BOOK / "episodes" / "ep04" / "takes" / "i2v"


def test_a_failed_attempt_is_kept_apart_from_the_take_that_won():
    """`T14_fail2.mp4` beside `T14.mp4` is how best-of-N reads as clutter and how
    a superseded take is mistaken for a current one."""
    assert eh.attempts_dir(BOOK, 4, "r2v") == BOOK / "episodes" / "ep04" / "takes" / "r2v" / "attempts"


def test_the_scratch_of_a_render_is_not_an_artefact_of_it():
    assert eh.work_dir(BOOK, 4, "r2v") == BOOK / "episodes" / "ep04" / "takes" / "work"


# ---- cut and reports --------------------------------------------------------

def test_every_master_lands_in_one_place():
    cut = BOOK / "episodes" / "ep04" / "cut"
    assert eh.cut_dir(BOOK, 4) == cut
    assert eh.master_path(BOOK, 4, "r2v") == cut / "master_r2v.mp4"
    assert eh.master_path(BOOK, 4, "i2v") == cut / "master.mp4"


def test_the_reports_are_not_mixed_with_the_film():
    assert eh.reports_dir(BOOK, 4) == BOOK / "episodes" / "ep04" / "reports"
    assert eh.qc_path(BOOK, 4, "r2v") == BOOK / "episodes" / "ep04" / "reports" / "qc_r2v.json"
    assert eh.qc_path(BOOK, 4, "i2v") == BOOK / "episodes" / "ep04" / "reports" / "qc.json"


# ---- the whole shape --------------------------------------------------------

def test_every_stage_folder_is_named_and_none_overlap():
    """A file has exactly one home, so a re-roll of one stage cannot disturb
    another. This is the property the owner asked for."""
    rooms = [eh.audio_dir(BOOK, 4), eh.boards_dir(BOOK, 4), eh.takes_root(BOOK, 4),
             eh.cut_dir(BOOK, 4), eh.reports_dir(BOOK, 4)]
    assert len({r.name for r in rooms}) == len(rooms)
    assert all(r.parent == eh.home(BOOK, 4) for r in rooms)
