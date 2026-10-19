"""The face refine gate, round 2 of the face-blur fix (2026-10-19), on round 1's own rows.

- Identity: facenet is a photo model and reads cel faces weakly (T01 Utterson 0.04 on his own
  take).  CCIP (anime-trained) is the term that separates a person from another: on round 1 the
  refined crops read 0.011-0.064 to their own sheet and 0.152-0.324 to the other person's.  So
  identity falls when CCIP rises more than 0.03 or crosses the same-character line 0.1785, or
  when facenet and clip_vision BOTH fall; with the anime terms unread, facenet alone, as before.
- Drift: mean |refined - take| inside the face box may not pass 35 (round 1's own faces 11.6-31.6;
  another row's refined face against a take's face, median 48.9).
- Seam: the paste's change outside the head <= 10 (round 1: 0.41-0.58 x the old band seam, median
  0.55, so 18 -> 10 leaves every hard-paste verdict as it was).
- The eye score is logged, never a wall.
Fixture: tests/fixtures/face_blur_round1_rows.json (the bench's refine.json re-measured)."""
from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

from studio import face_refine as fr

ROWS = json.loads((Path(__file__).parent / "fixtures" / "face_blur_round1_rows.json").read_text(encoding="utf-8"))["rows"]


def measures(row: dict, soft: bool | None = None) -> fr.Measures:
    soft = row["soft"] if soft is None else soft
    return fr.Measures(id_src=row["id_src"], id_ref=row["id_ref"], seam=row["seam_soft" if soft else "seam_hard"],
                       flick_src=row["flick_src"], flick_ref=row["flick_soft" if soft else "flick_hard"],
                       faces_src=row["faces_src"], faces_ref=row["faces_ref"], change=row["change"], drift=row["drift"],
                       eye_src=row["eye_src"], eye_ref=row["eye_ref"], ccip_src=row["ccip_src"], ccip_ref=row["ccip_ref"],
                       clip_src=row["clip_src"], clip_ref=row["clip_ref"])


def good() -> fr.Measures:
    return fr.Measures(id_src=0.5, id_ref=0.6, seam=5.0, flick_src=10.0, flick_ref=9.0, faces_src=1, faces_ref=1,
                       change=12.0, drift=18.0, eye_src=40.0, eye_ref=70.0, ccip_src=0.08, ccip_ref=0.04,
                       clip_src=0.8, clip_ref=0.85)


def test_every_round_one_face_is_kept_with_the_soft_paste_for_the_small_ones():
    said = {(r["take"], r["who"]): fr.decide(measures(r)) for r in ROWS}
    assert all(kept for kept, _ in said.values()), {k: why for k, (kept, why) in said.items() if not kept}


def test_the_hard_paste_still_refuses_exactly_round_ones_three_seams():
    refused = {(r["take"], r["who"]) for r in ROWS if not fr.decide(measures(r, soft=False))[0]}
    assert refused == {(r["take"], r["who"]) for r in ROWS if r["old_why"].startswith("seam")}
    assert {t for t, _ in refused} == {"T01", "T07"}


def test_a_facenet_drop_alone_never_refuses_when_ccip_holds():
    kept, why = fr.decide(replace(good(), id_ref=0.3))
    assert kept, why


def test_a_ccip_rise_refuses():
    kept, why = fr.decide(replace(good(), ccip_ref=0.12))
    assert not kept and "ccip" in why


def test_a_face_that_becomes_another_character_refuses():
    kept, why = fr.decide(replace(good(), ccip_src=0.16, ccip_ref=0.185))
    assert not kept and "ccip" in why


def test_facenet_and_clip_falling_together_refuse():
    kept, why = fr.decide(replace(good(), id_ref=0.3, clip_ref=0.7))
    assert not kept and "identity" in why


def test_unread_anime_terms_leave_facenet_to_decide_alone():
    m = replace(good(), id_ref=0.3, ccip_src=None, ccip_ref=None, clip_src=None, clip_ref=None)
    kept, why = fr.decide(m)
    assert not kept and "identity" in why


def test_a_face_that_drifts_off_its_take_refuses():
    kept, why = fr.decide(replace(good(), drift=40.0))
    assert not kept and "drift" in why
    assert fr.decide(replace(good(), drift=None))[0]


def test_the_eye_score_is_logged_never_a_wall():
    assert fr.decide(replace(good(), eye_src=90.0, eye_ref=0.0))[0]


def test_the_walls_are_the_ones_round_one_set():
    assert (fr.SEAM_MAX, fr.DRIFT_MAX, fr.CCIP_RISE, fr.CLIP_DROP) == (10.0, 35.0, 0.03, 0.05)
