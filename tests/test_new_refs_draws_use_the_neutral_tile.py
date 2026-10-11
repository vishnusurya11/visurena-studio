"""C3_verdict post-bench P1 (owner ruling 2026-10-11 on the C2 sheet: adopt the
neutral tile for NEW draws; D7, D8): a new refs draw -- base sheet, location
wide, prop sheet, a reseeded pack row -- runs image_krea2_cinematic_2x_neutraltile_visurena,
whose 2x tile pass is conditioned on style words only (USDU handed every tile
the subject prompt and a trouser tile painted a face).  The row's recorded
workflow name stays as history; the book title plate does NOT switch (D7)."""
from __future__ import annotations

import json

from studio import comfy, refs_pack, sheet_ladder

OLD = "image_krea2_cinematic_2x"
NEW = "image_krea2_cinematic_2x_neutraltile_visurena"


def test_new_draws_name_the_neutral_tile_workflow_and_it_resolves():
    assert refs_pack.T2I == NEW
    template, inject = comfy.load_workflow(refs_pack.T2I)        # a checkout without the file fails loudly
    assert {"prompt", "seed", "width", "height"} <= set(inject)


def test_the_graph_differs_from_the_benched_presave_only_in_its_saves_and_the_arm():
    """Arm (b) of the C3 bench: the tile pass at denoise 0.15 (0 ghosts, the
    least streaking, the best head facenet); one save, node 14 gone."""
    new, _ = comfy.load_workflow(NEW)
    bench, _ = comfy.load_workflow("image_krea2_cinematic_2x_presave_neutraltile_visurena")
    differ = sorted(k for k in set(new) | set(bench) if new.get(k) != bench.get(k))
    assert differ == ["12", "13", "14"] and "14" not in new
    assert new["12"]["inputs"]["denoise"] == 0.15 and bench["12"]["inputs"]["denoise"] == 0.2
    assert {k: v for k, v in new["12"]["inputs"].items() if k != "denoise"} == \
        {k: v for k, v in bench["12"]["inputs"].items() if k != "denoise"}


def test_a_reseeded_old_row_draws_on_the_new_workflow_and_keeps_its_name():
    row = {"workflow": OLD, "prompt": "a pit", "seed": 1}
    job = sheet_ladder.job_from_row("refs/locations/pit/wide.png", row)
    assert job.workflow == NEW and row["workflow"] == OLD


def test_a_row_naming_another_workflow_keeps_it():
    job = sheet_ladder.job_from_row("refs/locations/pit/wide.png", {"workflow": "image_ideogram4_t2i", "prompt": "x"})
    assert job.workflow == "image_ideogram4_t2i"


def test_the_book_title_plate_does_not_switch():
    from studio import book_title
    import inspect
    assert f'"workflow": "{OLD}"' in inspect.getsource(book_title)
